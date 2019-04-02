# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides factory methods for creating clients which would
communicate with Device Provisioning Service.
"""
from ..security.sk_security_client import SymmetricKeySecurityClient
from ..transport.mqtt_transport import MQTTTransport
from .sk_registration_client import SymmetricKeyRegistrationClient


def create_from_security_client(provisioning_host, security_client, transport_choice):
    """
    Creates different types of registration clients which can enable devices to communicate with Device Provisioning
    Service based on parameters passed.
    :param provisioning_host: Host running the Device Provisioning Service. Can be found in the Azure portal in the
    Overview tab as the string Global device endpoint
    :param security_client: Instance of Security client object which can be either of Symmetric Key, TPM or X.509
    :param transport_choice: A string representing the transport the user wants
    :return: A specific registration client based on parameters and validations.
    """
    if not provisioning_host:
        raise ValueError("Provisioning Host must be provided.")
    transport_choice = transport_choice.lower()
    if transport_choice == "mqtt":
        if isinstance(security_client, SymmetricKeySecurityClient):
            mqtt_transport = MQTTTransport(provisioning_host, security_client)
            return SymmetricKeyRegistrationClient(mqtt_transport)
            # TODO : other instances of security provider can also be checked before creating mqtt
        else:
            raise ValueError(
                "A symmetric key security provider must be provided for instantiating MQTT"
            )
    else:
        raise NotImplementedError("This transport has not yet been implemented")
        # TODO : Message must be enhanced later for other security providers. MQTT can also support X509.
