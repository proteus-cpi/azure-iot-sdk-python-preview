# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

import os
import logging
from six.moves import input
from azure.iot.device import SymmetricKeySecurityClient
from azure.iot.device import create_from_security_client


logging.basicConfig(level=logging.INFO)

provisioning_host = os.getenv("PROVISIONING_HOST")
id_scope = os.getenv("PROVISIONING_IDSCOPE")
registration_id = os.getenv("PROVISIONING_REGISTRATION_ID")
symmetric_key = os.getenv("PROVISIONING_SYMMETRIC_KEY")


symmetric_key_security_client = SymmetricKeySecurityClient(registration_id, symmetric_key, id_scope)
registration_client = create_from_security_client(
    provisioning_host, symmetric_key_security_client, "mqtt"
)


def registration_status_callback(registration_result):
    print("Operation Id =", registration_result.operation_id)
    print("Status =", registration_result.status)
    print(registration_result.status)
    if registration_result.status == "assigned":
        print("Device has been registered")
    elif registration_result.status == "assigning":
        print("Device is registering")
    else:
        print("Failed registration attempt")

    if registration_result.registration_state is not None:
        print("Registration state details are:-")
        print("Device Id =", registration_result.registration_state.device_id)
        print("Assigned Hub =", registration_result.registration_state.assigned_hub)


registration_client.on_registration_update = registration_status_callback

registration_client.register()

while True:
    selection = input("Press Q to quit\n")
    if selection == "Q" or selection == "q":
        print("Quitting...")
        break


# Output looks like
# Operation Id = 4.550cb20c3349a409.c79cdcdc-ca44-46db-ad9c-9cd04d472ae0
# Status = assigning
# assigning
# Device is registering
# Operation Id = 4.550cb20c3349a409.c79cdcdc-ca44-46db-ad9c-9cd04d472ae0
# Status = assigned
# assigned
# Device has been registered
# Registration state details are:-
# Device Id = hedwig
# Assigned Hub = IOTHubQuickStart.azure-devices.net
# """
