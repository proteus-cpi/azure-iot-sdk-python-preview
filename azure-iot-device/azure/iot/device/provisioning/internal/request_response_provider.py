# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

import logging
import json
from ..models.registration_result import RegistrationResult, RegistrationState

logger = logging.getLogger(__name__)


class RequestResponseMachine(object):
    def __init__(self, state_based_provider):

        self._state_based_provider = state_based_provider
        self._state_based_provider.on_state_based_provider_message_received = self._receive_response

        self.on_response_received = None

    def send_request(self, publish_action):
        """

        :param publish_action: The publish
        :return:
        """
        self.publish([publish_action])

    def connect(self, callback=None, post_connect_actions=None):
        # TODO : MQTT Transport connect should take post connect actions.
        self._state_based_provider.connect(callback=callback, actions=post_connect_actions)

    def disconnect(self, callback=None, pre_disconnect_actions=None):
        # TODO : MQTT Transport connect should take pre disconnect actions.
        self._state_based_provider.disconnect(callback=callback, actions=pre_disconnect_actions)

    def publish(self, publish_actions=None):
        self._state_based_provider.publish(publish_actions)

    def subscribe(self, subscribe_actions=None):
        self._state_based_provider.subscribe(subscribe_actions)

    def _receive_response(self, topic, payload):
        """
        Handler that processes the response from the service.
        :param topic: The topic in bytes name on which the message arrived on.
        :param payload: Payload in bytes of the message received.
        """
        # $dps/registrations/res/200/?$rid=28c32371-608c-4390-8da7-c712353c1c3b
        # {"operationId":"4.550cb20c3349a409.390d2957-7b58-4701-b4f9-7fe848348f4a","status":"assigning"}
        logger.info("")
        topic_str = topic.decode("utf-8")
        if topic_str.startswith("$dps/registrations/res/"):
            topic_parts = topic_str.split("$")
            rid_parts = topic_parts[2].split("=")
            rid = rid_parts[1]

        payload_str = payload.decode("utf-8")
        decoded_result = json.loads(payload_str)
        decoded_state = (
            None
            if "registrationState" not in decoded_result
            else decoded_result["registrationState"]
        )
        registration_state = None
        if decoded_state is not None:
            registration_state = RegistrationState(
                decoded_state["deviceId"],
                decoded_state["assignedHub"],
                decoded_state["substatus"],
                decoded_state["createdDateTimeUtc"],
                decoded_state["lastUpdatedDateTimeUtc"],
                decoded_state["etag"],
            )

        registration_result = RegistrationResult(
            rid, decoded_result["operationId"], decoded_result["status"], registration_state
        )
        self.on_response_received(registration_result)
