# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
import logging
import uuid
from threading import Timer
from transitions import Machine
from ..transport import constant

from .action import SubscribeAction, PublishAction, UnsubscribeAction
from .request_response_provider import RequestResponseMachine


logger = logging.getLogger(__name__)


class PollingMachine(object):
    """
    Class that is responsible for sending the initial registration request and polling the
    registration process for constant updates.
    """

    def __init__(self, state_based_provider):
        """
        :param state_based_provider: The state machine based provider.
        """
        self._polling_timer = None
        self._query_timer = None

        self._register_callback = None
        self._cancel_callback = None

        self.on_connected = None
        self.on_disconnected = None
        self.on_registration_status_update = None

        self._operations = {}

        self._request_response_provider = RequestResponseMachine(state_based_provider)

        self._request_response_provider.on_response_received = self._handle_response_received

        states = [
            "disconnected",
            "initializing",
            "registering",
            "waiting_to_poll",
            "polling",
            "completed",
            "error",
            "cancelling",
        ]

        transitions = [
            {
                "trigger": "_trig_register",
                "source": "disconnected",
                "before": "_initialize_register",
                "dest": "initializing",
            },
            {
                "trigger": "_trig_register",
                "source": "error",
                "before": "_initialize_register",
                "dest": "initializing",
            },
            {"trigger": "_trig_register", "source": "registering", "dest": None},
            {
                "trigger": "_trig_send_register_request",
                "source": "initializing",
                "before": "_send_register_request",
                "dest": "registering",
            },
            {
                "trigger": "_trig_wait",
                "source": "registering",
                "dest": "waiting_to_poll",
                "after": "_wait_for_interval",
            },
            {
                "trigger": "_trig_poll",
                "source": "waiting_to_poll",
                "dest": "polling",
                "after": "_query_operation_status",
            },
            {
                "trigger": "_trig_complete",
                "source": "registering",
                "dest": "completed",
                "after": "_call_complete",
            },
            {
                "trigger": "_trig_complete",
                "source": "waiting_to_poll",
                "dest": "completed",
                "after": "_call_complete",
            },
            {
                "trigger": "_trig_complete",
                "source": "polling",
                "dest": "completed",
                "after": "_call_complete",
            },
            {
                "trigger": "_trig_error",
                "source": "registering",
                "dest": "error",
                "after": "_call_error",
            },
            {
                "trigger": "_trig_error",
                "source": "waiting_to_poll",
                "dest": "error",
                "after": "_call_error",
            },
            {
                "trigger": "_trig_error",
                "source": "polling",
                "dest": "error",
                "after": "_call_error",
            },
            {"trigger": "_trig_cancel", "source": "disconnected", "dest": None},
            {
                "trigger": "_trig_cancel",
                "source": "registering",
                "dest": "cancelling",
                "after": "clear_and_disconnect",
            },
            {
                "trigger": "_trig_cancel",
                "source": "waiting_to_poll",
                "dest": "cancelling",
                "after": "clear_and_disconnect",
            },
            {
                "trigger": "_trig_cancel",
                "source": "polling",
                "dest": "cancelling",
                "after": "clear_and_disconnect",
            },
        ]

        def _on_transition_complete(event_data):
            if not event_data.transition:
                dest = "[no transition]"
            else:
                dest = event_data.transition.dest
            logger.info(
                "Transition complete.  Trigger=%s, Dest=%s, result=%s, error=%s",
                event_data.event.name,
                dest,
                str(event_data.result),
                str(event_data.error),
            )

        self._state_machine = Machine(
            model=self,
            states=states,
            transitions=transitions,
            initial="disconnected",
            send_event=True,  # Use event_data structures to pass transition arguments
            finalize_event=_on_transition_complete,
            queued=True,
        )

    def register(self, callback=None):
        """
        Register the device with the provisioning service.
        """
        logger.info("register called from polling machine")
        self._register_callback = callback
        self._trig_register()

    def cancel(self, callback=None):
        logger.info("cancel called from polling machine")
        self._cancel_callback = callback
        self._trig_cancel()

    def _initialize_register(self, event_data):
        logger.info("Preparing for registration process.")
        # Choice: Sending action here as the polling/dps state machine must figure out
        # in what order action must be sent. The request response is only responsible for
        # requesting and responding. However the actions can be taken down to the
        # the request response machine as well.
        subscribe_action = SubscribeAction(
            constant.SUBSCRIBE_TOPIC_PROVISIONING, qos=1, callback=self.on_subscribe_completed
        )
        # The request response takes a tuple of actions
        # It will call state based provider connect which
        # It will add subscribe to pending action queue
        # it will execute connect and then execute subscribe
        # TODO : Should I have a waiting callback or a connack on which something happens ?
        self._request_response_provider.connect(
            self.on_connect_completed, post_connect_actions=[subscribe_action]
        )

    def _send_register_request(self, event_data):
        logger.info("Sending registration request from polling machine")
        self._set_query_timer()

        rid = str(uuid.uuid4())

        publish_action = PublishAction(
            constant.PUBLISH_TOPIC_REGISTRATION + rid, " ", callback=self.on_publish_completed
        )
        self._operations[rid] = publish_action
        self._request_response_provider.send_request(publish_action)

    def _query_operation_status(self, event_data):
        logger.info("Querying operation status from polling machine")
        self._set_query_timer()

        rid = str(uuid.uuid4())
        registration_result = event_data.args[0].args[0]

        operation_id = registration_result.operation_id
        publish_action = PublishAction(
            constant.PUBLISH_TOPIC_QUERYING_I
            + rid
            + constant.PUBLISH_TOPIC_QUERYING_II
            + operation_id,
            " ",
            callback=self.on_publish_completed,
        )
        self._operations[rid] = publish_action
        self._request_response_provider.send_request(publish_action)

    def _handle_response_received(self, registration_result):
        self._query_timer.cancel()
        self._query_timer = None
        if self.on_registration_status_update:
            self.on_registration_status_update(registration_result)

        if registration_result.status == "assigning":
            rid = registration_result.request_id
            if rid in self._operations:
                publish_action = self._operations[rid]
                # If this request was generated by us for a query operation,
                # then we are getting a response for a query operation and
                # and we must clear the polling timer before beginning anything
                if "operationId" in publish_action.publish_topic:
                    self._polling_timer.cancel()
                    self._polling_timer = None
            self._trig_wait(registration_result)
        elif registration_result.status == "assigned":
            self._trig_complete(registration_result)
        else:
            self._trig_error(registration_result)

    def clear_and_disconnect(self, event_data):
        self._query_timer = None
        self._polling_timer = None
        unsubscribe_action = UnsubscribeAction(
            constant.SUBSCRIBE_TOPIC_PROVISIONING, callback=self.on_unsubscribe_completed
        )
        self._request_response_provider.disconnect(
            callback=self.on_disconnect_completed, pre_disconnect_actions=[unsubscribe_action]
        )
        # TODO : Do I need to wait for disconnect and then call the cancel callback?
        callback = self._cancel_callback

        if callback:
            self._cancel_callback = None
            callback()

    def _call_error(self, event_data):
        logger.info("Failed register from polling machine")
        error = event_data.args[0]
        callback = self._register_callback

        if callback:
            self._register_callback = None
            callback(error)

    def _call_complete(self, event_data):
        logger.info("Complete register from polling machine")
        registration_result = event_data.args[0]
        callback = self._register_callback

        if callback:
            self._register_callback = None
            callback(registration_result)

    def _set_query_timer(self):
        def time_up_query():
            logger.error("Time is up for query timer")
            # TODO TimeoutError causing problems
            self._trig_error(ValueError("Time is up for query timer"))

        self._query_timer = Timer(constant.DEFAULT_TIMEOUT_INTERVAL / 1000, time_up_query)
        self._query_timer.start()

    def _wait_for_interval(self, event_data):
        def time_up_polling():
            logger.info(
                "Done waiting for polling interval of %s ms", str(constant.DEFAULT_POLLING_INTERVAL)
            )

        self._polling_timer = Timer(constant.DEFAULT_POLLING_INTERVAL / 1000, time_up_polling)
        logger.info("Waiting for " + str(constant.DEFAULT_POLLING_INTERVAL) + " ms")
        self._polling_timer.run()  # This is waiting for that polling interval
        self._trig_poll(event_data)

    def on_connect_completed(self):
        logger.info("on_connect_completed for DPS")
        if self.on_connected:
            self.on_connected("connected")

    def on_disconnect_completed(self):
        logger.info("on_disconnect_completed for DPS")
        if self.on_disconnected:
            self.on_disconnected("disconnected")

    def on_subscribe_completed(self):
        logger.info("on_subscribe_completed for DPS")
        self._trig_send_register_request()

    def on_unsubscribe_completed(self):
        logger.info("on_unsubscribe_completed")

    def on_publish_completed(self):
        logger.info("on_publish_completed for DPS")
