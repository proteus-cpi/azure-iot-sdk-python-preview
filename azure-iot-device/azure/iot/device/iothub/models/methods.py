# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""This module contains classes related to direct method invocations.
"""


class MethodRequest(object):
    """Represents a request to invoke a direct method.

    :ivar str request_id: The request id.
    :ivar str name: The name of the method to be invoked.
    :ivar payload: The payload being sent with the request.
    """

    def __init__(self, request_id, name, payload):
        """Initializer for a MethodRequest.

        :param str request_id: The request id.
        :param str name: The name of the method to be invoked
        :param payload: The payload being sent with the request.
        """
        self._request_id = request_id
        self._name = name
        self._payload = payload

    @property
    def request_id(self):
        return self._request_id

    @property
    def name(self):
        return self._name

    @property
    def payload(self):
        return self._payload


class MethodResponse(object):
    """Represents a response to a direct method.

    :ivar str request_id: The request id of the MethodRequest being responded to.
    :ivar int status: The status of the execution of the MethodRequest.
    :ivar payload: The payload to be sent with the response.
    """

    def __init__(self, request_id, status, payload):
        """Initializer for MethodResponse.

        :param str request_id: The request id of the MethodRequest being responded to.
        :param int status: The status of the execution of the MethodRequest.
        :param payload: The payload to be sent with the response.
        """
        self.request_id = request_id
        self.status = status
        self.payload = payload

    @classmethod
    def create_from_method_request(cls, method_request, status, payload):
        """Factory method for creating a MethodResponse from a MethodRequest.

        :param method_request: The MethodRequest object to respond to.
        :type method_request: MethodRequest.
        :param int status: The status of the execution of the MethodRequest.
        :param payload: The payload to be sent with the response.
        """
        return cls(request_id=method_request.request_id, status=status, payload=payload)

    @property
    def payload(self):
        return self._payload

    @payload.setter
    def payload(self, value):
        self._payload = value.encode()
