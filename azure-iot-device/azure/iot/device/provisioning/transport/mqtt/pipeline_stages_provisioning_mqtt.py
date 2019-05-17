# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

import logging
import json
import six.moves.urllib as urllib
from azure.iot.device.common.transport import pipeline_ops_base
from azure.iot.device.common.transport.mqtt import pipeline_ops_mqtt
from azure.iot.device.common.transport.mqtt import pipeline_events_mqtt
from azure.iot.device.common.transport.pipeline_stages_base import PipelineStage
from azure.iot.device.provisioning.models import RegistrationResult
from azure.iot.device.provisioning.transport import constant
from azure.iot.device.provisioning.transport import (
    pipeline_events_provisioning,
    pipeline_ops_provisioning,
)
from . import mqtt_topic

logger = logging.getLogger(__name__)


class ProvisioningMQTTConverter(PipelineStage):
    """
    PipelineStage which converts other Iot and IotHub operations into Mqtt operations.  This stage also
    converts mqtt pipeline events into Iot and IotHub pipeline events.
    """

    def __init__(self):
        super(ProvisioningMQTTConverter, self).__init__()
        self.action_to_topic = {}

    def _run_op(self, op):

        if isinstance(op, pipeline_ops_provisioning.SetSymmetricKeySecurityClientArgs):
            # get security client args from above, save some, use some to build topic names,
            # always pass it down because MQTT Provider stage will also want to receive these args.
            # self._set_topic_names(device_id=op.device_id, module_id=op.module_id)

            client_id = op.registration_id
            client_version = urllib.parse.quote_plus(constant.USER_AGENT)
            username = "{id_scope}/registrations/{registration_id}/api-version={api_version}&ClientVersion={client_version}".format(
                id_scope=op.id_scope,
                registration_id=op.registration_id,
                api_version=constant.API_VERSION,
                client_version=client_version,
            )

            hostname = op.provisioning_host

            # if op.module_id:
            #     client_id = "{}/{}".format(op.device_id, op.module_id)
            # else:
            #     client_id = op.device_id
            #
            # username = "{hostname}/{client_id}/?api-version=2018-06-30".format(
            #     hostname=op.hostname, client_id=client_id
            # )

            # if op.gateway_hostname:
            #     hostname = op.gateway_hostname
            # else:
            #     hostname = op.hostname

            self.continue_with_different_op(
                original_op=op,
                new_op=pipeline_ops_mqtt.SetConnectionArgs(
                    client_id=client_id, hostname=hostname, username=username
                ),
            )

        elif isinstance(op, pipeline_ops_provisioning.EnableRegisterResponses):
            # Enabling for register gets translated into an Mqtt subscribe operation
            topic = mqtt_topic.get_topic_for_subscribe()
            self.continue_with_different_op(
                original_op=op, new_op=pipeline_ops_mqtt.Subscribe(topic=topic)
            )

        elif isinstance(op, pipeline_ops_provisioning.SendRegistrationRequest):
            # Convert Sending the request into Mqtt Publish operations
            topic = mqtt_topic.get_topic_for_register(op.rid)
            self.continue_with_different_op(
                original_op=op, new_op=pipeline_ops_mqtt.Publish(topic=topic, payload=op.request)
            )

        elif isinstance(op, pipeline_ops_provisioning.SendQueryRequest):
            # Convert Sending the request into Mqtt Publish operations
            topic = mqtt_topic.get_topic_for_query(op.rid, op.operation_id)
            self.continue_with_different_op(
                original_op=op, new_op=pipeline_ops_mqtt.Publish(topic=topic, payload=op.request)
            )

        # elif isinstance(op, pipeline_ops_iothub.SendMethodResponse):
        #     # Sending a Method Response gets translated into an MQTT Publish operation
        #     topic = mqtt_topic.get_method_topic_for_publish(
        #         op.method_response.request_id, str(op.method_response.status)
        #     )
        #     payload = json.dumps(op.method_response.payload)
        #     self.continue_with_different_op(
        #         original_op=op, new_op=pipeline_ops_mqtt.Publish(topic=topic, payload=payload)
        #     )

        elif isinstance(op, pipeline_ops_provisioning.DisableRegisterResponses):
            # Disabling a feature gets turned into an Mqtt unsubscribe operation
            topic = mqtt_topic.get_topic_for_subscribe()
            self.continue_with_different_op(
                original_op=op, new_op=pipeline_ops_mqtt.Unsubscribe(topic=topic)
            )

        else:
            # All other operations get passed down
            self.continue_op(op)

    # def _set_topic_names(self, device_id, module_id):
    #     """
    #     Build topic names based on the device_id and module_id passed.
    #     """
    #     self.telemetry_topic = mqtt_topic.get_telemetry_topic_for_publish(device_id, module_id)
    #     self.action_to_topic = {
    #         constant.REGISTER: (mqtt_topic.get_c2d_topic_for_subscribe(device_id, module_id)),
    #         constant.QUERY: (mqtt_topic.get_input_topic_for_subscribe(device_id, module_id)),
    #     }

    def _handle_pipeline_event(self, event):
        """
        Pipeline Event handler function to convert incoming Mqtt messages into the appropriate IotHub
        events, based on the topic of the message
        """
        if isinstance(event, pipeline_events_mqtt.IncomingMessage):
            topic = event.topic

            if mqtt_topic.is_dps_response_topic(topic):
                logger.info(
                    "Received payload:{payload} on topic:{topic}".format(
                        payload=event.payload, topic=topic
                    )
                )
                key_values = mqtt_topic.extract_properties_from_topic(topic)
                status_code = mqtt_topic.extract_status_code_from_topic(topic)
                rid = key_values["rid"][0]
                if event.payload is not None:
                    response = event.payload.decode("utf-8")
                # TODO : If status code is common to all incoming messages,
                # TODO : we can extract status code instead of sending portion of topic
                # TODO : Does entire topic needs to be sent and processing done later
                self.handle_pipeline_event(
                    pipeline_events_provisioning.RegistrationResponseEvent(
                        rid, status_code, key_values, response
                    )
                )
            else:
                logger.warning("Warning: dropping message with topic {}".format(topic))

        else:
            # all other messages get passed up
            PipelineStage._handle_pipeline_event(self, event)
