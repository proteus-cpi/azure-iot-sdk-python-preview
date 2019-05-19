# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

import sys
import pytest

# These fixtures are shared between sync and async clients
from .client_fixtures import auth_provider, transport
from tests.common.pipeline_test_fixtures import callback, fake_error, event

collect_ignore = []

# Ignore Async tests if below Python 3.5
if sys.version_info < (3, 5):
    collect_ignore.append("aio")
    collect_ignore.append("test_inbox_manager_async_inboxes.py")
