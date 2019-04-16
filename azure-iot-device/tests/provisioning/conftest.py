# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------

import sys
import pytest

# These fixtures are shared between sync and async clients
from .client_fixtures import transport

collect_ignore = []

# Ignore Async tests if below Python 3.5
