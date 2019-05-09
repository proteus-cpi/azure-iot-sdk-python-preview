# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

import logging
from azure.iot.device.common.transport import pipeline_ops_base
from azure.iot.device.common.transport.pipeline_stages_base import PipelineStage
from . import pipeline_ops_iothub


class UseSkAuthProvider(PipelineStage):
    """
    PipelineStage which handles operations on a Shared Key Authentication Provider.

    Operations Handled:
    * SetAuthProvider

    Operations Produced:
    * SetAuthProviderArgs
    * SetSasToken

    This stage handles SetAuthProvider operations.  It parses the connection
    string into it's constituant parts and generates a sas token to pass down.  It
    uses SetAuthProviderArgs to pass the connection string args and the ca_cert
    from the Authentication Provider, and it uses SetSasToken to pass down the
    generated sas token.  After passing down the args and the sas token, this stage
    completes the SetAuthProvider operation.

    All other operations are passed down.
    """

    def _run_op(self, op):
        if isinstance(op, pipeline_ops_iothub.SetAuthProvider):
            auth_provider = op.auth_provider
            self.run_ops_serial(
                pipeline_ops_iothub.SetAuthProviderArgs(
                    device_id=auth_provider.device_id,
                    module_id=auth_provider.module_id,
                    hostname=auth_provider.hostname,
                    gateway_hostname=getattr(auth_provider, "gateway_hostname", None),
                    ca_cert=getattr(auth_provider, "ca_cert", None),
                ),
                pipeline_ops_base.SetSasToken(sas_token=auth_provider.get_current_sas_token()),
                callback=op.callback,
            )
        else:
            self.continue_op(op)
