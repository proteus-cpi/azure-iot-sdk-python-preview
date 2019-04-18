# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

import pytest
import datetime
from mock import MagicMock
from azure.iot.device.provisioning.internal.polling_machine import PollingMachine
from azure.iot.device.provisioning.models.registration_result import (
    RegistrationResult,
    RegistrationState,
)
from azure.iot.device.provisioning.security.sk_security_client import SymmetricKeySecurityClient
from azure.iot.device.provisioning.transport.state_based_mqtt_provider import StateBasedMQTTProvider
from azure.iot.device.provisioning.sk_registration_client import SymmetricKeyRegistrationClient
from azure.iot.device.provisioning.registration_client_factory import create_from_security_client


fake_request_id = "Request1234"
fake_operation_id = "Operation4567"
fake_status = "Flying"
fake_device_id = "MyNimbus2000"
fake_assigned_hub = "Dumbledore'sArmy"
fake_sub_status = "FlyingOnHippogriff"
fake_created_dttm = datetime.datetime(2020, 5, 17)
fake_last_update_dttm = datetime.datetime(2020, 10, 17)
fake_etag = "HighQualityFlyingBroom"
fake_symmetric_key = "Zm9vYmFy"
fake_registration_id = "MyPensieve"
fake_id_scope = "Enchanted0000Ceiling7898"


@pytest.fixture
def state_based_mqtt(mocker):
    return mocker.MagicMock(spec=StateBasedMQTTProvider)


@pytest.fixture
def polling_machine(mocker, state_based_mqtt):

    # mock_polling_machine.on_connected = MagicMock()
    # mock_polling_machine.on_disconnected = MagicMock()
    mocker.patch("azure.iot.device.provisioning.internal.polling_machine.RequestResponseMachine")
    # mock_init_request_response_provider = mocker.patch("azure.iot.device.provisioning.internal.polling_machine.RequestResponseMachine")
    # mock_request_response_provider = mock_init_request_response_provider.return_value
    mock_polling_machine = PollingMachine(state_based_mqtt)
    return mock_polling_machine


class TestRegister:
    def test_register_calls_connect_on_request_response_provider_with_subscribe_action(
        self, polling_machine, mocker
    ):
        mock_init_subscribe_action = mocker.patch(
            "azure.iot.device.provisioning.internal.polling_machine.SubscribeAction"
        )
        mock_subscribe_action = mock_init_subscribe_action.return_value

        polling_machine.on_connect_completed = MagicMock()

        mock_request_response_provider = polling_machine._request_response_provider
        polling_machine.register()

        mock_request_response_provider.connect.assert_called_once_with(
            polling_machine.on_connect_completed, post_connect_actions=[mock_subscribe_action]
        )

    def test_on_subscribe_completed_calls_send_register_request_on_request_response_provider(
        self, polling_machine, mocker
    ):
        mock_init_publish_action = mocker.patch(
            "azure.iot.device.provisioning.internal.polling_machine.PublishAction"
        )
        mock_publish_action = mock_init_publish_action.return_value

        mock_init_query_timer = mocker.patch(
            "azure.iot.device.provisioning.internal.polling_machine.Timer"
        )
        mock_query_timer = mock_init_query_timer.return_value
        mocker.patch.object(mock_query_timer, "start")

        polling_machine.state = "initializing"
        mock_request_response_provider = polling_machine._request_response_provider
        polling_machine.on_subscribe_completed()

        mock_request_response_provider.send_request.assert_called_once_with(mock_publish_action)


class TestResponse:
    @pytest.fixture
    def fake_registration_state(self):
        return RegistrationState(
            fake_device_id,
            fake_assigned_hub,
            fake_sub_status,
            fake_created_dttm,
            fake_last_update_dttm,
            fake_etag,
        )

    @pytest.fixture
    def registration_result_assigned(self, fake_registration_state):
        return RegistrationResult(
            fake_request_id, fake_operation_id, "assigned", fake_registration_state
        )

    @pytest.fixture
    def registration_result_assigning(self, fake_registration_state):
        return RegistrationResult(
            fake_request_id, fake_operation_id, "assigning", fake_registration_state
        )

    @pytest.fixture
    def registration_result_error(self, fake_registration_state):
        return RegistrationResult(
            fake_request_id, fake_operation_id, "error", fake_registration_state
        )

    def test_on_receiving_response_with_status_assigned_calls_callback_of_register_complete(
        self, polling_machine, registration_result_assigned, mocker
    ):
        polling_machine._query_timer = MagicMock()
        mocker.patch.object(polling_machine._query_timer, "cancel")

        polling_machine.state = "polling"
        polling_machine.on_registration_status_update = MagicMock()
        polling_machine._register_callback = MagicMock()
        # Must be passed into a mock object as the register callback is set to None
        mock_callback = polling_machine._register_callback
        polling_machine._handle_response_received(registration_result_assigned)

        mock_callback.assert_called_once_with(registration_result_assigned)

    def test_on_receiving_response_with_status_assigning_waits_for_interval_and_calls_send_request_on_request_response_provider(
        self, polling_machine, registration_result_assigning, mocker
    ):
        polling_machine._query_timer = MagicMock()
        mocker.patch.object(polling_machine._query_timer, "cancel")

        mock_init_any_timer = mocker.patch(
            "azure.iot.device.provisioning.internal.polling_machine.Timer"
        )
        mock_timer = mock_init_any_timer.return_value
        mocker.patch.object(mock_timer, "start")
        polling_timer_run = mocker.patch.object(mock_timer, "run")

        mock_init_publish_action = mocker.patch(
            "azure.iot.device.provisioning.internal.polling_machine.PublishAction"
        )
        mock_publish_action = mock_init_publish_action.return_value
        mock_request_response_provider = polling_machine._request_response_provider

        polling_machine.state = "registering"
        polling_machine.on_registration_status_update = MagicMock()
        polling_machine._handle_response_received(registration_result_assigning)

        polling_timer_run.assert_called_once_with()
        mock_request_response_provider.send_request.assert_called_once_with(mock_publish_action)

    def test_on_receiving_response_with_status_error_calls_callback_of_register_error(
        self, polling_machine, registration_result_error, mocker
    ):
        polling_machine._query_timer = MagicMock()
        mocker.patch.object(polling_machine._query_timer, "cancel")

        polling_machine.state = "polling"
        polling_machine.on_registration_status_update = MagicMock()
        polling_machine._register_callback = MagicMock()
        # Must be passed into a mock object as the register callback is set to None
        mock_callback = polling_machine._register_callback
        polling_machine._handle_response_received(registration_result_error)

        mock_callback.assert_called_once_with(registration_result_error)
