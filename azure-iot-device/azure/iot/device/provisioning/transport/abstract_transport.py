# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

import abc
import six


# TODO : Methods like subscribe/unsubscribe were called enable/disable following previous pattern


@six.add_metaclass(abc.ABCMeta)
class AbstractTransport:
    """
    All specific transport will follow implementations of this abstract class.
    """

    def __init__(self, security_client):
        self._auth_provider = security_client

        # Event Handlers - Will be set by Client after instantiation of Transport
        self.on_transport_connected = None
        self.on_transport_disconnected = None
        self.on_transport_message_received = None

    @abc.abstractmethod
    def connect(self, callback):
        """
        Connect to the specific messaging system used by the specific transport protocol
        """
        pass

    @abc.abstractmethod
    def disconnect(self, callback):
        """
        Disconnect from the specific messaging system used by the specific transport protocol
        """
        pass

    @abc.abstractmethod
    def enable_responses(self, callback=None):
        """
        Enable to ability to receive responses.
        """
        pass

    @abc.abstractmethod
    def disable_responses(self, callback=None):
        """
        Disable the ability to receiving responses.
        """
        pass

    @abc.abstractmethod
    def send_request(self, request, callback):
        """
        Send a request.
        """
        pass
