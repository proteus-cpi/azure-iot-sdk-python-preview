# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

import logging
from azure.iot.device.common.transport import pipeline_stages_base
from azure.iot.device.common.transport import pipeline_ops_base
from azure.iot.device.common.transport.mqtt import pipeline_stages_mqtt
from azure.iot.device.provisioning.transport.abstract_transport import AbstractTransport
from azure.iot.device.provisioning.transport import pipeline_stages_provisioning
from azure.iot.device.provisioning.transport import pipeline_events_provisioning
from azure.iot.device.provisioning.transport import pipeline_ops_provisioning
from . import pipeline_stages_provisioning_mqtt

logger = logging.getLogger(__name__)


class MQTTTransport(AbstractTransport):
    def __init__(self, security_client):
        """
        Constructor for instantiating a transport
        :param auth_provider: The authentication provider
        """
        AbstractTransport.__init__(self, security_client)
        self._pipeline = (
            pipeline_stages_base.PipelineRoot()
            .append_stage(pipeline_stages_provisioning.UseSymmetricKeySecurityClient())
            .append_stage(pipeline_stages_base.EnsureConnection())
            .append_stage(pipeline_stages_provisioning_mqtt.ProvisioningMQTTConverter())
            .append_stage(pipeline_stages_mqtt.Provider())
        )

        def _handle_pipeline_event(event):
            if isinstance(event, pipeline_events_provisioning.RegistrationResponseEvent):
                if self.on_transport_message_received:
                    self.on_transport_message_received(
                        event.rid, event.status_code, event.key_values, event.response
                    )
                else:
                    logger.warning("C2D event received with no handler.  dropping.")

            # elif isinstance(event, pipeline_events_iothub.InputMessageEvent):
            #     if self.on_transport_input_message_received:
            #         self.on_transport_input_message_received(event.input_name, event.message)
            #     else:
            #         logger.warning("input mesage event received with no handler.  dropping.")
            #
            # elif isinstance(event, pipeline_events_iothub.MethodRequest):
            #     if self.on_transport_method_request_received(event.method_request):
            #         self.on_transport_method_request_received(event.method_request)
            #     else:
            #         logger.warning("Method request event received with no handler. Dropping.")

            else:
                logger.warning("Dropping unknown pipeline event {}".format(event.name))

        def _handle_connected():
            if self.on_transport_connected:
                self.on_transport_connected("connected")

        def _handle_disconnected():
            if self.on_transport_disconnected:
                self.on_transport_disconnected("disconnected")

        self._pipeline.on_pipeline_event = _handle_pipeline_event
        self._pipeline.on_connected = _handle_connected
        self._pipeline.on_disconnected = _handle_disconnected

        def remove_this_code(call):
            if call.error:
                raise call.error

        self._pipeline.run_op(
            pipeline_ops_provisioning.SetSymmetricKeySecurityClient(
                security_client=security_client, callback=remove_this_code
            )
        )

    def connect(self, callback=None):
        """
        Connect to the service.

        :param callback: callback which is called when the connection to the service is complete.
        """
        logger.info("connect called")

        def pipeline_callback(call):
            if call.error:
                # TODO we need error semantics on the client
                exit(1)
            if callback:
                callback()

        self._pipeline.run_op(pipeline_ops_base.Connect(callback=pipeline_callback))

    def disconnect(self, callback=None):
        """
        Disconnect from the service.

        :param callback: callback which is called when the connection to the service has been disconnected
        """
        logger.info("disconnect called")

        def pipeline_callback(call):
            if call.error:
                # TODO we need error semantics on the client
                exit(1)
            if callback:
                callback()

        self._pipeline.run_op(pipeline_ops_base.Disconnect(callback=pipeline_callback))

    def send_request(self, rid, request, operation_id=None, callback=None):
        """
        Send a telemetry message to the service.

        :param callback: callback which is called when the message publish has been acknowledged by the service.
        """

        def pipeline_callback(call):
            if call.error:
                # TODO we need error semantics on the client
                exit(1)
            if callback:
                callback()

        op = None
        if operation_id is not None:
            op = pipeline_ops_provisioning.SendQueryRequest(
                rid=rid, operation_id=operation_id, request=request, callback=pipeline_callback
            )
        else:
            op = pipeline_ops_provisioning.SendRegistrationRequest(
                rid=rid, request=request, callback=pipeline_callback
            )

        self._pipeline.run_op(op)

    # def send_output_event(self, message, callback=None):
    #     """
    #     Send an output message to the service.
    #
    #     :param callback: callback which is called when the message publish has been acknowledged by the service.
    #     """
    #
    #     def pipeline_callback(call):
    #         if call.error:
    #             # TODO we need error semantics on the client
    #             exit(1)
    #         if callback:
    #             callback()
    #
    #     self._pipeline.run_op(
    #         pipeline_ops_iothub.SendOutputEvent(message=message, callback=pipeline_callback)
    #     )
    #
    # def send_method_response(self, method_response, callback=None):
    #     logger.info("Transport send_method_response called")
    #
    #     def pipeline_callback(call):
    #         if call.error:
    #             # TODO we need error semantics on the client
    #             exit(1)
    #         if callback:
    #             callback()
    #
    #     self._pipeline.run_op(
    #         pipeline_ops_iothub.SendMethodResponse(
    #             method_response=method_response, callback=pipeline_callback
    #         )
    #     )

    def enable_feature(self, feature_name, callback=None):
        """
        Enable the given feature by subscribing to the appropriate topics.

        :param feature_name: one of the feature name constants from constant.py
        :param callback: callback which is called when the feature is enabled
        """
        logger.info("enable_feature {} called".format(feature_name))
        self.feature_enabled[feature_name] = True

        def pipeline_callback(call):
            if call.error:
                # TODO we need error semantics on the client
                exit(1)
            if callback:
                callback()

        self._pipeline.run_op(
            pipeline_ops_base.EnableFeature(feature_name=feature_name, callback=pipeline_callback)
        )

    def disable_feature(self, feature_name, callback=None):
        """
        Disable the given feature by subscribing to the appropriate topics.
        :param callback: callback which is called when the feature is disabled

        :param feature_name: one of the feature name constants from constant.py
        """
        logger.info("disable_feature {} called".format(feature_name))
        self.feature_enabled[feature_name] = False

        def pipeline_callback(call):
            if call.error:
                # TODO we need error semantics on the client
                exit(1)
            if callback:
                callback()

        self._pipeline.run_op(
            pipeline_ops_base.DisableFeature(feature_name=feature_name, callback=pipeline_callback)
        )
