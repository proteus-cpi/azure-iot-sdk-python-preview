# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

import pytest
from azure.iot.device.provisioning.security.sk_security_client import SymmetricKeySecurityClient
import six.moves.urllib as urllib


fake_symmetric_key = "Zm9vYmFy"
key_name = "registration"
fake_provisioning_host = "beauxbatons.academy-net"
fake_registration_id = "MyPensieve"
module_id = "Divination"
fake_id_scope = "Enchanted0000Ceiling7898"
signature = "IsolemnlySwearThatIamuUptoNogood"
expiry = "1539043658"


@pytest.mark.it("properties have getters")
def test_properties_are_gettable_after_create_security_client():
    security_client = SymmetricKeySecurityClient(
        fake_registration_id, fake_symmetric_key, fake_id_scope
    )
    assert security_client.id_scope == fake_id_scope
    assert security_client.registration_id == fake_registration_id


@pytest.mark.it("properties do not have setter")
def test_properties_are_not_settable():
    security_client = SymmetricKeySecurityClient(
        fake_registration_id, fake_symmetric_key, fake_id_scope
    )
    with pytest.raises(AttributeError, match="can't set attribute"):
        security_client.registration_id = "MyNimbus2000"
        security_client.id_scope = "WhompingWillow"


@pytest.mark.it("create sas token")
def test_create_sas():
    security_client = SymmetricKeySecurityClient(
        fake_registration_id, fake_symmetric_key, fake_id_scope
    )
    sas_value = security_client.get_current_sas_token()
    assert key_name in sas_value
    assert fake_registration_id in sas_value
    assert fake_id_scope in sas_value


def test_extract_properties_from_topic():
    """
    Extract key=value pairs from custom properties and set the properties on the received message.
    :param topic: The topic string
    """
    topic = "$dps/registrations/res/202/?$rid=d3d9bc12-7ee3-44a6-a0d6-4a0be4da0c60&retry-after=3&key=value"
    topic_parts = topic.split("$")
    key_value_dict = urllib.parse.parse_qs(topic_parts[2])
    print(key_value_dict)
    print(type(key_value_dict))


# TODO: leverage this helper in all property extraction functions
def test_extract_properties():
    """Return a dictionary of properties from a string in the format
    ${key1}={value1}&${key2}={value2}&...{keyn}={valuen}
    """
    topic = "$dps/registrations/res/202/?$rid=d3d9bc12-7ee3-44a6-a0d6-4a0be4da0c60&$retry-after=3&$key=value"
    topic_parts = topic.split("$")
    properties_str = topic_parts[2]

    d = {}
    kv_pairs = properties_str.split("&")

    for entry in kv_pairs:
        pair = entry.split("=")
        key = urllib.parse.unquote_plus(pair[0]).lstrip("$")
        value = urllib.parse.unquote_plus(pair[1])
        d[key] = value

    print(d)
    print(type(d))
