# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

import pytest
from azure.iot.device.iothub.models import MethodRequest, MethodResponse


class TestMethodRequest(object):
    @pytest.mark.skip(reason="Not implemented")
    def test_initializes_with_attributes(self):
        pass

    @pytest.mark.skip(reason="Not implemented")
    def test_name_property_is_read_only(self):
        pass

    @pytest.mark.skip(reason="Not implemented")
    def test_payload_property_is_read_only(self):
        pass


class TestMethodResponse(object):
    @pytest.mark.it("Initializes with parameters set")
    @pytest.mark.skip(reason="Not Implemented")
    def test_initializes_with_attributes(self):
        pass

    # TODO: test for payload, both dict, json, etc.
    # TODO: test for creating methodresponse from methodrequest
