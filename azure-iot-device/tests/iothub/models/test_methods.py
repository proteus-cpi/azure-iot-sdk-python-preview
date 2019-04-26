# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

import pytest
from azure.iot.device.iothub.models import MethodRequest, MethodResponse

dummy_rid = 1
dummy_name = "name"
dummy_payload = "{'MethodPayload': 'somepayload'}"


@pytest.mark.describe("Method Request")
class TestMethodRequest(object):
    @pytest.mark.it("Instantiates with 'request_id' as a read-only property")
    def test_request_id_property_is_read_only(self):
        m_req = MethodRequest(dummy_rid, dummy_name, dummy_payload)
        new_rid = 2

        with pytest.raises(AttributeError):
            m_req.request_id = new_rid
        assert m_req.request_id != new_rid
        assert m_req.request_id == dummy_rid

    @pytest.mark.it("Instantiates with 'name' as a read-only property")
    def test_name_property_is_read_only(self):
        m_req = MethodRequest(dummy_rid, dummy_name, dummy_payload)
        new_name = "new_name"

        with pytest.raises(AttributeError):
            m_req.name = new_name
        assert m_req.name != new_name
        assert m_req.name == dummy_name

    @pytest.mark.it("Instantiates with 'payload' as a read-only property")
    def test_payload_property_is_read_only(self):
        m_req = MethodRequest(dummy_rid, dummy_name, dummy_payload)
        new_payload = "{'NewPayload': 'somenewpayload'}"

        with pytest.raises(AttributeError):
            m_req.payload = new_payload
        assert m_req.payload != new_payload
        assert m_req.payload == dummy_payload


class TestMethodResponse(object):
    @pytest.mark.it("Initializes with parameters set")
    @pytest.mark.skip(reason="Not Implemented")
    def test_initializes_with_attributes(self):
        pass

    # TODO: test for payload, both dict, json, etc.
    # TODO: test for creating methodresponse from methodrequest
