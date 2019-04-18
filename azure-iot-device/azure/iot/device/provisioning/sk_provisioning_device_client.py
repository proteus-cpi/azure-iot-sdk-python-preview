# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module contains one of the implementations of the Provisioning Device Client which uses Symmetric Key authentication.
"""
import logging
from threading import Event
import traceback
from .provisioning_device_client import ProvisioningDeviceClient
from .internal.polling_machine import PollingMachine

logger = logging.getLogger(__name__)


class SymmetricKeyProvisioningDeviceClient(ProvisioningDeviceClient):
    """
    Client which can be used to run the registration of a device with provisioning service
    using Symmetric Key authentication.
    """

    def __init__(self, mqtt_state_based_provider):
        """
        Initializer for the Symmetric Key Registration Client
        :param mqtt_state_based_provider: The state-based protocol provider. As of now this only supports MQTT.
        """
        super(SymmetricKeyProvisioningDeviceClient, self).__init__(mqtt_state_based_provider)
        self._polling_machine = PollingMachine(mqtt_state_based_provider)
        # To be defined by sample
        self.on_registration_complete = None
        self._polling_machine.on_disconnected = self._on_connection_state_change
        self._polling_machine.on_registration_complete = self._on_device_registration_complete

    def register(self):
        """
        Register the device with the provisioning service.
        """
        logger.info("Registering with Hub...")
        register_complete = Event()

        def callback_register(result=None, error=None):
            # This could be a failed/successful registration result from the HUB
            # or a error from polling machine. Response should be given appropriately
            if result is not None:
                if result.status == "assigned":
                    logger.info("Successfully registered with Hub")
                else:  # There be other statuses
                    logger.error("Failed registering with Hub")
            if error is not None:  # This can only happen when the polling machine runs into error
                logger.info(error)

            register_complete.set()

        self._polling_machine.register(callback=callback_register)

        register_complete.wait()

    def cancel(self):
        """
        Cancels the current registration process.
        """
        logger.info("Cancelling the current registration process")
        cancel_complete = Event()

        def callback_cancel():
            cancel_complete.set()
            logger.info("Successfully cancelled the current registration process")

        self._polling_machine.cancel(callback=callback_cancel)
        cancel_complete.wait()

    def _on_device_registration_complete(self, registration_result):
        """Handler to be called by the transport when registration changes status."""
        logger.info("_on_device_registration_update")

        if self.on_registration_complete:
            try:
                self.on_registration_complete(registration_result)
            except:  # noqa: E722 do not use bare 'except'
                logger.error("Unexpected error calling on_registration_complete")
                logger.error(traceback.format_exc())

    def _on_connection_state_change(self, new_state):
        """Handler to be called by the transport upon a connection state change."""
        logger.info("Connection State - {}".format(new_state))
