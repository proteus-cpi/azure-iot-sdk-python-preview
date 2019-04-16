# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
import pytest
from azure.iot.device.provisioning.security.sk_security_client import SymmetricKeySecurityClient
from azure.iot.device.provisioning.transport.state_based_mqtt_provider import StateBasedMQTTProvider
from azure.iot.device.provisioning.sk_registration_client import SymmetricKeyRegistrationClient
from azure.iot.device.provisioning.registration_client_factory import create_from_security_client

fake_symmetric_key = "Zm9vYmFy"
fake_registration_id = "MyPensieve"
fake_id_scope = "Enchanted0000Ceiling7898"

xfail_notimplemented = pytest.mark.xfail(raises=NotImplementedError, reason="Unimplemented")


@pytest.fixture
def provisioning_host():
    return "fakehost.com"


@pytest.fixture
def security_client():
    return SymmetricKeySecurityClient("fake_registration_id", "fake_symmetric_key", "fake_id_scope")


def test_raises_when_client_created_from_no_host(security_client):
    with pytest.raises(ValueError, match="Provisioning Host must be provided."):
        create_from_security_client("", security_client, "mqtt")


@pytest.mark.parametrize(
    "protocol,expected_transport",
    [
        pytest.param("mqtt", StateBasedMQTTProvider, id="mqtt"),
        pytest.param("amqp", None, id="amqp", marks=xfail_notimplemented),
        pytest.param("http", None, id="http", marks=xfail_notimplemented),
    ],
)
def test_create_from_security_provider_instantiates_client(
    provisioning_host, security_client, protocol, expected_transport
):
    client = create_from_security_client(provisioning_host, security_client, protocol)
    assert isinstance(client, SymmetricKeyRegistrationClient)
    assert client.on_registration_update is None


def test_raises_when_client_created_from_security_provider_with_not_symmetric_security():
    with pytest.raises(
        ValueError,
        match="A symmetric key security provider must be provided for instantiating MQTT",
    ):
        not_symmetric_security_client = NonSymmetricSecurityClientTest()
        create_from_security_client(provisioning_host, not_symmetric_security_client, "mqtt")


class NonSymmetricSecurityClientTest(object):
    def __init__(self):
        self.registration_id = fake_registration_id
        self.id_scope = fake_id_scope
