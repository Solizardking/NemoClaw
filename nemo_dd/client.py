"""SDK bootstrap for NeMo Data Designer.

Reads NMP_BASE_URL from the environment (defaults to the local platform
deployment at http://localhost:8080) and connects to the `default` workspace.
"""

import os

from nemo_platform import NeMoPlatform


def get_sdk(workspace: str = "default") -> NeMoPlatform:
    base_url = os.environ.get("NMP_BASE_URL", "http://localhost:8080")
    return NeMoPlatform(base_url=base_url, workspace=workspace)
