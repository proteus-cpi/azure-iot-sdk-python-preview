# --------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------


class RegistrationResult(object):
    """
    The result of any registration attempt
    """

    def __init__(self, rid=None, operation_id=None, status=None, registration_state=None):
        """
        :param rid: The request id to which the response is being obtained
        :param operation_id: The id of the operation as returned by the initial registration request.
        :param status: The status of the registration process.
        Values can be "unassigned", "assigning", "assigned", "failed", "disabled"
        :param registration_state : Details like device id, assigned hub , date times etc returned
        from the provisioning service.
        """
        self.request_id = rid
        self.operation_id = operation_id
        self.status = status
        self.registration_state = registration_state


class RegistrationState(object):
    """
    The registration state regarding the device.
    """

    def __init__(
        self,
        device_id=None,
        assigned_hub=None,
        sub_status=None,
        created_date_time=None,
        last_update_date_time=None,
        etag=None,
    ):
        """
        :param device_id: Desired device id for the provisioned device
        :param assigned_hub: Desired  IoT Hub where the provisioned device is located
        :param assigned_hub: Desired  IoT Hub where the provisioned device is located
        :param sub_status: Substatus for 'Assigned' devices. Possible values are
        "initialAssignment", "deviceDataMigrated", "deviceDataReset"
        :param created_date_time: Registration create date time (in UTC).
        :param last_update_date_time: Last updated date time (in UTC).
        :param etag: The entity tag associated with the resource.
        """
        self.device_id = device_id
        self.assigned_hub = assigned_hub
        self.sub_status = sub_status
        self.created_date_time = created_date_time
        self.last_update_date_time = last_update_date_time
        self.etag = etag
