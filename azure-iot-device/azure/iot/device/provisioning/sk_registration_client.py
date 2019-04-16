# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module contains one of the implementations of the Registration Client which uses Symmetric Key authentication.
"""
import logging
from threading import Event
from .registration_client import RegistrationClient
from .models.registration_result import RegistrationResult
from .internal.polling_machine import PollingMachine

logger = logging.getLogger(__name__)


class SymmetricKeyRegistrationClient(RegistrationClient):
    """
    Client which can be used to run the registration of a device using Symmetric Key authentication.
    """

    def __init__(self, mqtt_state_based_provider):
        """
        Initializer for the Symmetric Key Registration Client
        """
        super(SymmetricKeyRegistrationClient, self).__init__(mqtt_state_based_provider)
        self._polling_machine = PollingMachine(mqtt_state_based_provider)
        # To be defined by sample
        self.on_registration_update = None
        self._polling_machine.on_connected = self._on_state_change
        self._polling_machine.on_disconnected = self._on_state_change
        self._polling_machine.on_registration_status_update = self._on_device_registration_update

    def register(self):
        """
        Register the device with the provisioning service.
        """
        logger.info("Registering with Hub...")
        register_complete = Event()

        def callback_register(result):
            register_complete.set()
            # TODO This could be a failed result or a successful one.
            # TODO Response should be given appropriately
            if isinstance(result, RegistrationResult):
                if result.status == "assigned":
                    logger.info("Successfully registered with Hub")
                else:  # TODO Only error or failed should come here
                    logger.error("Failed registering with Hub")
            else:
                logger.info(result)

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

    def _on_device_registration_update(self, registration_result):
        """Handler to be called by the transport when registration changes status."""
        logger.info("on_device_registration_complete")
        if self.on_registration_update:
            self.on_registration_update(registration_result)

    def _on_state_change(self, new_state):
        """Handler to be called by the transport upon a connection state change."""
        logger.info("Connection State - {}".format(new_state))
