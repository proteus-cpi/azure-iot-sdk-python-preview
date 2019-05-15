# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
from azure.iot.device.common.transport.pipeline_events_base import PipelineEvent


class RegistrationResponse(PipelineEvent):
    """
    A PipelineEvent object which represents an incoming RegistrationResponse event. This object is probably
    created by some converter stage based on a transport-specific event
    """

    def __init__(self, topic, response):
        """
        Initializer for RegistrationResponse objects.
        :param topic: The topic on which the response received.
        :param response: The response received from a registration process
        """
        super(RegistrationResponse, self).__init__()
        self.topic = topic
        self.response = response


class QueryResponse(PipelineEvent):
    """
    A PipelineEvent object which represents an incoming QueryResponse event. This object is probably
    created by some converter stage based on a transport-specific event
    """

    def __init__(self, topic, response):
        """
        Initializer for QueryResponse objects.
        :param topic: The topic on which the response was received.
        :param response: The response received from a query process
        """
        super(RegistrationResponse, self).__init__()
        self.topic = topic
        self.response = response


class QueryRequest(PipelineEvent):
    """
    A PipelineEvent object which represents an incoming polling request event. This object is probably
    created by some converter stage based on a transport-specific event
    """

    def __init__(self, request_id, topic, request):
        """
        Initializer for RegistrationRequest objects.
        :param request_id: The id of the request
        :param topic: The topic to which the request needs to be
        :param request: The content of the request.
        """
        super(QueryRequest, self).__init__()
        self.request_id = request_id
        self.topic = topic
        self.request = request


class RegistrationRequest(PipelineEvent):
    """
    A PipelineEvent object which represents an incoming RegistrationRequest event.
    This object is probably created by some converter stage based on a transport-specific event.
    """

    def __init__(self, request_id, topic, request):
        """
        Initializer for RegistrationRequest objects.
        :param request_id: The id of the request
        :param topic: The topic to which the request needs to be
        :param request: The content of the request.
        TODO : Since the content is blank do we need this ?
        """
        super(RegistrationRequest, self).__init__()
        self.request_id = request_id
        self.topic = topic
        self.request = request
