# -------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Prepare development environment
"""

import glob
import os
import sys
import argparse
from subprocess import check_call, CalledProcessError


def pip_command(command, error_ok=False):
    try:
        print("Executing: " + command)
        check_call([sys.executable, "-m", "pip"] + command.split())
        print()

    except CalledProcessError as err:
        print(err)
        if not error_ok:
            sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Prepare environment")
    parser.add_argument(
        "--no_dev",
        dest="dev_mode",
        action="store_false",
        help="Setup environment for running and testing ONLY",
    )
    args = parser.parse_args()

    ns_packages = [os.path.dirname(p) for p in glob.glob("azure*nspkg/setup.py")]
    packages = [
        os.path.dirname(p)
        for p in glob.glob("azure*/setup.py")
        if os.path.dirname(p) not in ns_packages
    ]

    # Install nspkgs first (2.7 only)
    if sys.version_info < (3, 0, 0):
        for package_name in ns_packages:
            pip_command("install -e {}".format(package_name))

    # Install packages
    for package_name in packages:
        pip_command("install -e {}".format(package_name))

    # Install other development environment dependencies
    pip_command("install -r requirements.txt")
    if args.dev_mode:
        print("Installing pre-commit")
        check_call("pre-commit install")
