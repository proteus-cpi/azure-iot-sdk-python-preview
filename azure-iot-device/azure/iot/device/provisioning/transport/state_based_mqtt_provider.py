# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

import logging
import six.moves.queue as queue
import six.moves.urllib as urllib
from transitions import Machine
from . import constant
from azure.iot.device.iothub.transport.mqtt.mqtt_provider import MQTTProvider
from ..internal.action import SubscribeAction, PublishAction, UnsubscribeAction

logger = logging.getLogger(__name__)


class StateBasedMQTTProvider(object):
    def __init__(self, provisioning_host, security_client):
        self.security_client = security_client
        self.provisioning_host = provisioning_host

        self._pending_action_queue = queue.Queue()
        self._in_progress_actions = {}
        self._responses_with_unknown_mid = {}

        self.on_state_based_provider_connected = None
        self.on_state_based_provider_disconnected = None
        self.on_state_based_provider_message_received = None

        self._connect_callback = None
        self._disconnect_callback = None

        self._create_mqtt_provider()

        states = ["disconnected", "connecting", "connected", "disconnecting"]

        transitions = [
            {
                "trigger": "_trig_connect",
                "source": "disconnected",
                "before": "_add_actions_to_queue",
                "dest": "connecting",
                "after": "_call_provider_connect",
            },
            {"trigger": "_trig_connect", "source": ["connecting", "connected"], "dest": None},
            {
                "trigger": "_trig_provider_connect_complete",
                "source": "connecting",
                "dest": "connected",
                "after": "_execute_actions_in_queue",
            },
            {
                "trigger": "_trig_disconnect",
                "source": ["disconnected", "disconnecting"],
                "dest": None,
            },
            {
                "trigger": "_trig_disconnect",
                "source": "connected",
                "dest": "disconnecting",
                "after": "_call_provider_disconnect",
            },
            {
                "trigger": "_trig_provider_disconnect_complete",
                "source": "disconnecting",
                "dest": "disconnected",
            },
            {
                "trigger": "_trig_add_action_to_pending_queue",
                "source": "connected",
                "before": "_add_actions_to_queue",
                "dest": None,
                "after": "_execute_actions_in_queue",
            },
            {
                "trigger": "_trig_add_action_to_pending_queue",
                "source": "connecting",
                "before": "_add_actions_to_queue",
                "dest": None,
            },
            {
                "trigger": "_trig_add_action_to_pending_queue",
                "source": "disconnected",
                "before": "_add_actions_to_queue",
                "dest": "connecting",
                "after": "_call_provider_connect",
            },
            {
                "trigger": "_trig_on_shared_access_string_updated",
                "source": "connected",
                "dest": "connecting",
                "after": "_call_provider_reconnect",
            },
            {
                "trigger": "_trig_on_shared_access_string_updated",
                "source": ["disconnected", "disconnecting"],
                "dest": None,
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

    def connect(self, callback=None, actions=None):
        """
        Connect to the service.

        :param callback: callback which is called when the connection to the service is complete.
        :param actions: Certain actions that need to executed once connected depending on the scenario.
        Example : Like in DPS you have to subscribe first before connecting.
        """
        logger.info("connect called")
        self._connect_callback = callback
        self._trig_connect(actions)

    def disconnect(self, callback=None, actions=None):
        """
        Disconnect from the service.

        :param callback: callback which is called when the connection to the service has been disconnected
        :param actions: Certain actions that need to executed before disconnecting depending on the scenario.
        """
        logger.info("disconnect called")
        self._disconnect_callback = callback
        for action in actions:
            self._execute_action(action)
        self._trig_disconnect()

    def publish(self, action):
        self._trig_add_action_to_pending_queue(action)

    def subscribe(self, action):
        self._trig_add_action_to_pending_queue(action)

    def unsubscribe(self, topic, callback=None):
        action = UnsubscribeAction(topic, callback)
        self._trig_add_action_to_pending_queue(action)

    def _create_mqtt_provider(self):
        client_id = self.security_client.registration_id

        username = (
            self.security_client.id_scope
            + "/registrations/"
            + self.security_client.registration_id
            + "/api-version="
            + constant.API_VERSION
            + "&ClientVersion="
            + urllib.parse.quote_plus(constant.USER_AGENT)
        )

        hostname = self.provisioning_host

        self._mqtt_provider = MQTTProvider(client_id, hostname, username, ca_cert=None)

        self._mqtt_provider.on_mqtt_connected = self._on_provider_connect_complete
        self._mqtt_provider.on_mqtt_disconnected = self._on_provider_disconnect_complete
        self._mqtt_provider.on_mqtt_published = self._on_provider_publish_complete
        self._mqtt_provider.on_mqtt_subscribed = self._on_provider_subscribe_complete
        self._mqtt_provider.on_mqtt_unsubscribed = self._on_provider_unsubscribe_complete
        self._mqtt_provider.on_mqtt_message_received = self._on_provider_message_received

    def _on_provider_connect_complete(self):
        """
        Callback that is called by the provider when the connection has been established
        """
        logger.info("_on_state_based_provider_connect_complete")
        self._trig_provider_connect_complete()

        if self.on_state_based_provider_connected:
            self.on_state_based_provider_connected("connected")
        callback = self._connect_callback
        if callback:
            self._connect_callback = None
            callback()

    def _on_provider_disconnect_complete(self):
        """
        Callback that is called by the provider when the connection has been disconnected
        """
        logger.info("_on_state_based_provider_disconnect_complete")
        self._trig_provider_disconnect_complete()

        if self.on_state_based_provider_disconnected:
            self.on_state_based_provider_disconnected("disconnected")
        callback = self._disconnect_callback
        if callback:
            self._disconnect_callback = None
            callback()

    def _on_provider_publish_complete(self, mid):
        """
        Callback that is called by the provider when it receives a PUBACK from the service

        :param mid: message id that was returned by the provider when `publish` was called.  This is used to tie the
            PUBLISH to the PUBACK.
        """
        logger.info("_on_state_based_provider_publish_complete")
        if mid in self._in_progress_actions:
            callback = self._in_progress_actions[mid]
            del self._in_progress_actions[mid]
            callback()
        else:
            logger.warning("PUBACK received with unknown MID: %s", str(mid))
            self._responses_with_unknown_mid[
                mid
            ] = mid  # storing MID for now.  will probably store result code later.

    def _on_provider_subscribe_complete(self, mid):
        """
        Callback that is called by the provider when it receives a SUBACK from the service

        :param mid: message id that was returned by the provider when `subscribe` was called.  This is used to tie the
            SUBSCRIBE to the SUBACK.
        """
        logger.info("_on_state_based_provider_subscribe_complete")
        if mid in self._in_progress_actions:
            callback = self._in_progress_actions[mid]
            del self._in_progress_actions[mid]
            callback()
        else:
            logger.warning("SUBACK received with unknown MID: %s", str(mid))
            self._responses_with_unknown_mid[
                mid
            ] = mid  # storing MID for now.  will probably store result code later.

    def _on_provider_message_received(self, topic, payload):
        """
        Callback that is called by the provider when a message is received.  This message can be any MQTT message,
        including, but not limited to, a C2D message, an input message, a TWIN patch, a twin response (/res), and
        a method invocation.  This function needs to decide what kind of message it is based on the topic name and
        take the correct action.

        :param topic: MQTT topic name that the message arrived on
        :param payload: Payload of the message
        """
        logger.info("_on_state_based_provider_message_received")
        logger.info("Message received on topic %s", topic)
        self.on_state_based_provider_message_received(topic, payload)

    def _on_provider_unsubscribe_complete(self, mid):
        """
        Callback that is called by the provider when it receives an UNSUBACK from the service

        :param mid: message id that was returned by the provider when `unsubscribe` was called.  This is used to tie the
            UNSUBSCRIBE to the UNSUBACK.
        """
        logger.info("_on_state_based_provider_unsubscribe_complete")
        if mid in self._in_progress_actions:
            callback = self._in_progress_actions[mid]
            del self._in_progress_actions[mid]
            callback()
        else:
            logger.warning("UNSUBACK received with unknown MID: %s", str(mid))
            self._responses_with_unknown_mid[
                mid
            ] = mid  # storing MID for now.  will probably store result code later.

    def _call_provider_connect(self, event_data):
        logger.info("Calling provider connect")
        password = self._get_current_sas_token()
        self._mqtt_provider.connect(password)

        if hasattr(self.security_client, "token_update_callback"):
            self.security_client.token_update_callback = self._on_shared_access_string_updated

    def _call_provider_reconnect(self, event_data):
        """
        Call into the provider to reconnect the transport.

        This is called by the state machine as part of a state transition

        :param EventData event_data:  Object created by the Transitions library with information about the state transition
        """
        logger.info("Calling provider reconnect")
        password = self.security_client.get_current_sas_token()
        self._mqtt_provider.reconnect(password)

    def _call_provider_disconnect(self, event_data):
        """
        Call into the provider to disconnect the transport.

        This is called by the state machine as part of a state transition

        :param EventData event_data:  Object created by the Transitions library with information about the state transition
        """
        logger.info("Calling provider disconnect")
        self._mqtt_provider.disconnect()
        # self.security_client.disconnect()

    def _add_actions_to_queue(self, event_data):
        """
        Queue an action for running later.  All actions that need to run while connected end up in
        this queue, even if they're going to be run immediately.

        This is called by the state machine as part of a state transition

        :param EventData event_data:  Object created by the Transitions library with information about the state transition
        """
        for action in event_data.args[0]:
            self._pending_action_queue.put_nowait(action)

    def _execute_actions_in_queue(self, event_data):
        """
        Execute any actions that are waiting in the action queue.
        This is called by the state machine as part of a state transition.
        This function actually calls down into the provider to perform the necessary operations.

        :param EventData event_data:  Object created by the Transitions library with information about the state transition
        """
        logger.info("checking _pending_action_queue")
        while True:
            try:
                action = self._pending_action_queue.get_nowait()
            except queue.Empty:
                logger.info("done checking queue")
                return

            self._execute_action(action)

    def _execute_action(self, action):
        """
        Execute an action from the action queue.  This is called when the transport is connected and the
        state machine is able to execute individual actions.

        :param TransportAction action: object containing the details of the action to be executed
        """

        if isinstance(action, PublishAction):
            mid = self._mqtt_provider.publish(action.publish_topic, action.message)
            if mid in self._responses_with_unknown_mid:
                del self._responses_with_unknown_mid[mid]
                action.callback()
            else:
                self._in_progress_actions[mid] = action.callback

        elif isinstance(action, SubscribeAction):
            logger.info(
                "running SubscribeAction topic=%s qos=%s", action.subscribe_topic, action.qos
            )
            mid = self._mqtt_provider.subscribe(action.subscribe_topic, action.qos)
            logger.info("subscribe mid = %s", mid)
            if mid in self._responses_with_unknown_mid:
                del self._responses_with_unknown_mid[mid]
                action.callback()
            else:
                self._in_progress_actions[mid] = action.callback

        else:
            logger.error("Removed unknown action type from queue.")

    def _get_current_sas_token(self):
        """
        Set the current Shared Access Signature Token string.
        """
        return self.security_client.create_shared_access_signature()
