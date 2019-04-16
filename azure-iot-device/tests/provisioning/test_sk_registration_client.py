# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

import pytest
from azure.iot.device.provisioning.internal.polling_machine import PollingMachine
from azure.iot.device.provisioning.sk_registration_client import SymmetricKeyRegistrationClient


@pytest.fixture
def client(transport):
    return SymmetricKeyRegistrationClient(transport)


@pytest.fixture
def success_result(mocker):
    return mocker.MagicMock()


class FakePollingMachine(PollingMachine):
    def register(self, callback):
        callback(success_result)

    def cancel(self, callback):
        callback()

    def disconnect(self, callback):
        callback()


@pytest.fixture
def polling_machine(mocker):
    return mocker.MagicMock(wraps=FakePollingMachine(mocker.MagicMock()))


def test_instantation(transport):
    client = SymmetricKeyRegistrationClient(transport)
    assert hasattr(client, "on_registration_update")
    assert hasattr(client, "_polling_machine")


def test_client_register_calls_polling_machine_register(mocker, transport, polling_machine):
    mock_polling_machine_init = mocker.patch(
        "azure.iot.device.provisioning.sk_registration_client.PollingMachine"
    )
    mock_polling_machine_init.return_value = polling_machine

    client = SymmetricKeyRegistrationClient(transport)
    client.register()
    assert polling_machine.register.call_count == 1
