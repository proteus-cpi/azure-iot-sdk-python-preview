# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""This module contains a client that is responsible for providing shared access tokens that will eventually establish
 the authenticity of devices to Device Provisioning Service.
"""

from azure.iot.device.common.sastoken import SasToken


class SymmetricKeySecurityClient(object):
    """
    A client that is responsible for providing shared access tokens that will eventually establish
    the authenticity of devices to Device Provisioning Service.
    :ivar registration_id: : The registration ID is used to uniquely identify a device in the Device Provisioning Service.
    :ivar id_scope: : The ID scope is used to uniquely identify the specific provisioning service the device will
        register through.
    """

    def __init__(self, registration_id, symmetric_key, id_scope):
        """
        Initialize the symmetric key security client.
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
        self._registration_id = registration_id
        self._symmetric_key = symmetric_key
        self._id_scope = id_scope
        self._sas_token = None

    @property
    def registration_id(self):
        """
        :return: The registration ID is used to uniquely identify a device in the Device Provisioning Service.
        The registration ID is alphanumeric, lowercase string and may contain hyphens.
        """
        return self._registration_id

    @property
    def id_scope(self):
        """
        :return: Host running the Device Provisioning Service.
        """
        return self._id_scope

    def _create_shared_access_signature(self):
        """
        Construct SAS tokens that have a hashed signature formed using the symmetric key of this security client.
        This signature is recreated by the Device Provisioning Service to verify whether a security token presented
        during attestation is authentic or not.
        :return: A string representation of the shared access signature which is of the form
        SharedAccessSignature sig={signature}&se={expiry}&skn={policyName}&sr={URL-encoded-resourceURI}
        """
        uri = self._id_scope + "/registrations/" + self._registration_id
        key = self._symmetric_key
        time_to_live = 3600
        keyname = "registration"
        return SasToken(uri, key, keyname, time_to_live)

    def get_current_sas_token(self):
        if self._sas_token is None:
            self._sas_token = self._create_shared_access_signature()
        else:
            self._sas_token.refresh()
        return str(self._sas_token)
