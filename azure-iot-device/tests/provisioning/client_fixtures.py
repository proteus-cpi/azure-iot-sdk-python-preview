# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

import pytest
from azure.iot.device.provisioning.security.sk_security_client import SymmetricKeySecurityClient
from azure.iot.device.provisioning.transport.state_based_mqtt_provider import StateBasedMQTTProvider


@pytest.fixture
def provisioning_host():
    return "fakehost.com"


@pytest.fixture
def security_client():
    return SymmetricKeySecurityClient("fake_registration_id", "fake_symmetric_key", "fake_id_scope")


class FakeMQTTStateBasedProvider(StateBasedMQTTProvider):
    def connect(self, callback):
        callback()

    def disconnect(self, callback):
        callback()

    def enable_feature(self, feature_name, callback=None, qos=1):
        callback()

    def disable_feature(self, feature_name, callback=None):
        callback()

    def send_event(self, event, callback):
        callback()

    def send_output_event(self, event, callback):
        callback()

    def send_method_response(self, method, payload, status, callback=None):
        callback()


@pytest.fixture
def transport(mocker):
    return mocker.MagicMock(
        wraps=FakeMQTTStateBasedProvider(mocker.MagicMock(), mocker.MagicMock())
    )
