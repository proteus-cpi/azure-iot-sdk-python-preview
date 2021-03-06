# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
from azure.iot.device.common.transport.pipeline_ops_base import PipelineOperation


class SetAuthProvider(PipelineOperation):
    """
    A PipelineOperation object which tells the pipeline to use a particular authorization provider.
    Some pipeline stage is expected to extract arguments out of the auth provider and pass them
    on so an even lower stage can use those arguments to connect.

    This operation is in the group of IotHub operations because autorization providers are currently
    very IotHub-specific
    """

    def __init__(self, auth_provider, callback=None):
        """
        Initializer for SetAuthProvider objects.

        :param object auth_provider: The authorization provider object to use to retrieve connection parameters
          which can be used to connect to the service.
        :param Function callback: The function that gets called when this operation is complete or has failed.
         The callback function must accept A PipelineOperation object which indicates the specific operation which
         has completed or failed.
        """
        super(SetAuthProvider, self).__init__(callback=callback)
        self.auth_provider = auth_provider


class SetAuthProviderArgs(PipelineOperation):
    """
    A PipelineOperation object which contains connection arguments which were retrieved from an authorization provider,
    likely by a pipeline stage which handles the SetAuthProvider operation.

    This operation is in the group of IoTHub operations because the arguments which it accepts are very specific to
    IotHub connections and would not apply to other types of client connections (such as a DPS client).
    """

    def __init__(
        self,
        device_id,
        hostname,
        module_id=None,
        gateway_hostname=None,
        ca_cert=None,
        callback=None,
    ):
        """
        Initializer for SetAuthProviderArgs objects.

        :param str device_id: The device id for the device that we are connecting.
        :param str hostname: The hostname of the iothub service we are connecting to.
        :param str module_id: (optional) If we are connecting as a module, this contains the module id
          for the module we are connecting.
        :param str gateway_hostname: (optional) If we are going through a gateway host, this is the
          hostname for the gateway
        :param str ca_cert: (Optional) The CA certificate to use if theMQTT server that we're going to
          connect to uses server-side TLS
        :param Function callback: The function that gets called when this operation is complete or has failed.
         The callback function must accept A PipelineOperation object which indicates the specific operation which
         has completed or failed.
        """
        super(SetAuthProviderArgs, self).__init__(callback=callback)
        self.device_id = device_id
        self.module_id = module_id
        self.hostname = hostname
        self.gateway_hostname = gateway_hostname
        self.ca_cert = ca_cert


class SendTelemetry(PipelineOperation):
    """
    A PipelineOperation object which contains arguments used to send a telemetry message to an IotHub or EdegHub server.

    This operation is in the group of IoTHub operations because it is very specific to the IotHub client
    """

    def __init__(self, message, callback=None):
        """
        Initializer for SendTelemetry objects.

        :param Message message: The message that we're sending to the service
        :param Function callback: The function that gets called when this operation is complete or has failed.
         The callback function must accept A PipelineOperation object which indicates the specific operation which
         has completed or failed.
        """
        super(SendTelemetry, self).__init__(callback=callback)
        self.message = message
        self.needs_connection = True


class SendOutputEvent(PipelineOperation):
    """
    A PipelineOperation object which contains arguments used to send an output message to an EdgeHub server.

    This operation is in the group of IoTHub operations because it is very specific to the IotHub client
    """

    def __init__(self, message, callback=None):
        """
        Initializer for SendOutputEvent objects.

        :param Message message: The output message that we're sending to the service. The name of the output is
          expected to be stored in the output_name attribute of this object
        :param Function callback: The function that gets called when this operation is complete or has failed.
         The callback function must accept A PipelineOperation object which indicates the specific operation which
         has completed or failed.
        """
        super(SendOutputEvent, self).__init__(callback=callback)
        self.message = message
        self.needs_connection = True


class SendMethodResponse(PipelineOperation):
    """
    A PipleineOperation object which contains arguments used to send a method response to an IoTHub or EdgeHub server.

    This operation is in the group of IoTHub operations because it is very specific to the IoTHub client.
    """

    def __init__(self, method_response, callback=None):
        """
        Initializer for SendMethodResponse objects.

        :param method_response: The method response to be sent to IoTHub/EdgeHub
        :type method_response: MethodResponse
        :param callback: The function that gets called when this operation is complete or has failed.
         The callback function must accept a PipelineOperation object which indicates the specific operation has which
         has completed or failed.
        :type callback: Function/callable
        """
        super(SendMethodResponse, self).__init__(callback=callback)
        self.method_response = method_response
        self.needs_connection = True
