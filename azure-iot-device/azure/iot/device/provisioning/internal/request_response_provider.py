# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

import logging
import six.moves.urllib as urllib

logger = logging.getLogger(__name__)

POS_STATUS_CODE_IN_TOPIC = 3
POS_URL_PORTION = 1
POS_QUERY_PARAM_PORTION = 2


class RequestResponseProvider(object):
    """
    Class that processes requests sent from device and responses received at device.
    """

    def __init__(self, state_based_provider):

        self._mqtt_transport = state_based_provider

        self._mqtt_transport.on_transport_message_received = self._receive_response

        self._pending_requests = {}

    def send_request(self, rid, request, operation_id=None, callback_on_response=None):
        """
        Sends a request
        :param rid: Id of the request
        :param request: The payload of the request.
        :param operation_id: A id of the operation in case it is an ongoing process.
        :param callback_on_response: callback which is called when response comes back for this request.
        """
        self._pending_requests[rid] = callback_on_response
        self._mqtt_transport.send_request(
            rid=rid, request=request, operation_id=operation_id, callback=self._on_publish_completed
        )

    def connect(self, callback=None):
        if callback is None:
            callback = self._on_connection_state_change
        self._mqtt_transport.connect(callback=callback)

    def disconnect(self, callback=None):
        if callback is None:
            callback = self._on_connection_state_change
        self._mqtt_transport.disconnect(callback=callback)

    def publish(self, topic, request, callback=None):
        if callback is None:
            callback = self._on_publish_completed
        self._mqtt_transport.publish(topic=topic, message=request, callback=callback)

    def enable_responses(self, callback=None):
        if callback is None:
            callback = self._on_subscribe_completed
        self._mqtt_transport.enable_responses(callback=callback)

    def disable_responses(self, callback=None):
        if callback is None:
            callback = self._on_unsubscribe_completed
        self._mqtt_transport.disable_responses(callback=callback)

    def _receive_response(self, rid, status_code, key_value_dict, response):
        """
        Handler that processes the response from the service.
        :param rid: The id of the request which is being responded to.
        :param status_code: The status code inside the response
        :param key_value_dict: A dictionary of keys mapped to a list of values extracted from the topic of the response.
        :param response: String payload of the message received.
        :return:
        """
        # """ Sample topic and payload
        # $dps/registrations/res/200/?$rid=28c32371-608c-4390-8da7-c712353c1c3b
        # {"operationId":"4.550cb20c3349a409.390d2957-7b58-4701-b4f9-7fe848348f4a","status":"assigning"}
        # """
        logger.info("Received response {}:".format(response))

        if rid in self._pending_requests:
            callback = self._pending_requests[rid]
            # Only send the status code and the portion of the topic containing query parameters
            callback(rid, status_code, key_value_dict, response)
            del self._pending_requests[rid]

    def _on_connection_state_change(self, new_state):
        """Handler to be called by the pipeline upon a connection state change."""
        logger.info("Connection State - {}".format(new_state))

    def _on_publish_completed(self):
        logger.info("publish completed for request response provider")

    def _on_subscribe_completed(self):
        logger.info("subscribe completed for request response provider")

    def _on_unsubscribe_completed(self):
        logger.info("on_unsubscribe_completed for request response provider")
