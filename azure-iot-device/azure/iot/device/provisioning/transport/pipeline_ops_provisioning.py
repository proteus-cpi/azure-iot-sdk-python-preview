# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
from azure.iot.device.common.transport.pipeline_ops_base import PipelineOperation

# TODO : Should this be named just SecurityProvider or SecurityClient?


class SetSymmetricKeySecurityClient(PipelineOperation):
    """
    A PipelineOperation object which tells the pipeline to use a symmetric key security client.
    Some pipeline stage is expected to extract arguments out of the security client and pass them
    on so an even lower stage can use those arguments to connect.

    This operation is in the group of provisioning operations because security clients are currently
    very provisioning-specific
    """

    def __init__(self, security_client, callback=None):
        """
        Initializer for SetSecurityClient.

        :param object security_client: The security client object to use to retrieve connection parameters
          which can be used to connect to the service.
        :param Function callback: The function that gets called when this operation is complete or has failed.
         The callback function must accept A PipelineOperation object which indicates the specific operation which
         has completed or failed.
        """
        super(SetSymmetricKeySecurityClient, self).__init__(callback=callback)
        self.security_client = security_client


# TODO : Should this be named SetSecurityProviderArgs or SetSecurityClientArgs?


class SetSymmetricKeySecurityClientArgs(PipelineOperation):
    """
    A PipelineOperation object which contains connection arguments which were retrieved from a
    symmetric key security client likely by a pipeline stage which handles the
    SetSymmetricKeySecurityClient operation.

    This operation is in the group of IoTHub operations because the arguments which it accepts are
    very specific to DPS connections and would not apply to other types of client connections
    (such as a IotHub client).
    """

    def __init__(self, provisioning_host, registration_id, id_scope, callback=None):
        """
        Initializer for SetSymmetricKeySecurityClientArgs.
        :param registration_id: The registration ID is used to uniquely identify a device in the Device Provisioning Service.
        The registration ID is alphanumeric, lowercase string and may contain hyphens.
        :param symmetric_key: The key which will be used to create the shared access signature token to authenticate
        the device with the Device Provisioning Service. By default, the Device Provisioning Service creates
        new symmetric keys with a default length of 32 bytes when new enrollments are saved with the Auto-generate keys
        option enabled. Users can provide their own symmetric keys for enrollments by disabling this option within
        16 bytes and 64 bytes and in valid Base64 format.
        :param id_scope: The ID scope is used to uniquely identify the specific provisioning service the device will
        register through. The ID scope is assigned to a Device Provisioning Service when it is created by the user and
        is generated by the service and is immutable, guaranteeing uniqueness.
        """
        super(SetSymmetricKeySecurityClientArgs, self).__init__(callback=callback)
        self.provisioning_host = provisioning_host
        self.registration_id = registration_id
        self.id_scope = id_scope
        # self.symmetric_key = symmetric_key


class SendRegistrationRequest(PipelineOperation):
    """
    A PipelineOperation object which contains arguments used to send a registration request
    to an Device Provisioning Hub.

    This operation is in the group of DPS operations because it is very specific to the DPS client.
    """

    def __init__(self, rid, request, callback=None):
        """
        Initializer for SendRegistrationRequest objects.

        :param rid : The id of the request being sent
        :param request: The request that we are sending to the service
        :param Function callback: The function that gets called when this operation is complete or has failed.
         The callback function must accept A PipelineOperation object which indicates the specific operation which
         has completed or failed.
        """
        super(SendRegistrationRequest, self).__init__(callback=callback)
        self.rid = rid
        self.request = request
        self.needs_connection = True


class SendQueryRequest(PipelineOperation):
    """
    A PipelineOperation object which contains arguments used to send a registration request
    to an Device Provisioning Hub.

    This operation is in the group of DPS operations because it is very specific to the DPS client.
    """

    def __init__(self, rid, operation_id, request, callback=None):
        """
        Initializer for SendRegistrationRequest objects.

        :param rid
        :param request: The request that we are sending to the service
        :param Function callback: The function that gets called when this operation is complete or has failed.
         The callback function must accept A PipelineOperation object which indicates the specific operation which
         has completed or failed.
        """
        super(SendQueryRequest, self).__init__(callback=callback)
        self.rid = rid
        self.operation_id = operation_id
        self.request = request
        self.needs_connection = True


class EnableRegisterResponses(PipelineOperation):
    """
    A PipelineOperation object which contains arguments used enable responses from the registration
    process in general. This involves enabling responses to a registration request as well as a query request.

    This operation is in the group of DPS operations because it is very specific to the DPS client
    """

    def __init__(self, callback=None):
        """
        Initializer for EnableRegisterResponses objects.

        :param Function callback: The function that gets called when this operation is complete or has failed.
         The callback function must accept A PipelineOperation object which indicates the specific operation which
         has completed or failed.
        """
        super(EnableRegisterResponses, self).__init__(callback=callback)
        self.needs_connection = True


class DisableRegisterResponses(PipelineOperation):
    """
    A PipelineOperation object which contains arguments used disable responses from the registration
    process in general. This involves disabling responses to a registration request as well as a query request.

    This operation is in the group of DPS operations because it is very specific to the DPS client
    """

    def __init__(self, callback=None):
        """
        Initializer for DisableRegisterResponses objects.

        :param Function callback: The function that gets called when this operation is complete or has failed.
         The callback function must accept A PipelineOperation object which indicates the specific operation which
         has completed or failed.
        """
        super(DisableRegisterResponses, self).__init__(callback=callback)
        self.needs_connection = True


#
# class SendMethodResponse(PipelineOperation):
#     """
#     A PipleineOperation object which contains arguments used to send a method response to an IoTHub or EdgeHub server.
#
#     This operation is in the group of IoTHub operations because it is very specific to the IoTHub client.
#     """
#
#     def __init__(self, method_response, callback=None):
#         """
#         Initializer for SendMethodResponse objects.
#
#         :param method_response: The method response to be sent to IoTHub/EdgeHub
#         :type method_response: MethodResponse
#         :param callback: The function that gets called when this operation is complete or has failed.
#          The callback function must accept a PipelineOperation object which indicates the specific operation has which
#          has completed or failed.
#         :type callback: Function/callable
#         """
#         super(SendMethodResponse, self).__init__(callback=callback)
#         self.method_response = method_response
#         self.needs_connection = True
