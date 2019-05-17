# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
from azure.iot.device.common.transport.pipeline_events_base import PipelineEvent


class RegistrationResponseEvent(PipelineEvent):
    """
    A PipelineEvent object which represents an incoming RegistrationResponse event. This object is probably
    created by some converter stage based on a transport-specific event
    """

    def __init__(self, request_id, status_code, key_values, response):
        """
        Initializer for RegistrationResponse objects.
        :param request_id : The id of the request to which the response arrived.
        :param status_code: The status code received in the topic.
        :param key_values: A dictionary containing key mapped to a list of values that were extarcted from the topic.
        :param response: The response received from a registration process
        """
        super(RegistrationResponseEvent, self).__init__()
        self.rid = request_id
        self.status_code = status_code
        self.key_values = key_values
        self.response = response


# class QueryResponseEvent(PipelineEvent):
#     """
#     TODO : Not sure if this event is separately needed.
#     A PipelineEvent object which represents an incoming QueryResponse event. This object is probably
#     created by some converter stage based on a transport-specific event
#     """
#
#     def __init__(self, topic, response):
#         """
#         Initializer for QueryResponse objects.
#         :param topic: The topic on which the response was received.
#         :param response: The response received from a query process
#         """
#         super(QueryResponseEvent, self).__init__()
#         self.topic = topic
#         self.response = response


# class QueryRequest(PipelineEvent):
#     """
#     A PipelineEvent object which represents an incoming polling request event. This object is probably
#     created by some converter stage based on a transport-specific event
#     """
#
#     def __init__(self, request_id, topic, request):
#         """
#         Initializer for RegistrationRequest objects.
#         :param request_id: The id of the request
#         :param topic: The topic to which the request needs to be
#         :param request: The content of the request.
#         TODO : Since the content is blank do we need the request parameter ?
#         """
#         super(QueryRequest, self).__init__()
#         self.request_id = request_id
#         self.topic = topic
#         self.request = request
#
#
# class RegistrationRequest(PipelineEvent):
#     """
#     A PipelineEvent object which represents an incoming RegistrationRequest event.
#     This object is probably created by some converter stage based on a transport-specific event.
#     """
#
#     def __init__(self, request_id, topic, request):
#         """
#         Initializer for RegistrationRequest objects.
#         :param request_id: The id of the request
#         :param topic: The topic to which the request needs to be
#         :param request: The content of the request.
#         TODO : Since the content is blank do we need the request parameter ?
#         """
#         super(RegistrationRequest, self).__init__()
#         self.request_id = request_id
#         self.topic = topic
#         self.request = request
