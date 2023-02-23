
from .rpc_client import UsrpClient
from .system import System
from uhd_wrapper.utils.config import MimoSignal, TxStreamingConfig, RxStreamingConfig, RfConfig


def _get_version() -> str:
    import os
    import re
    import subprocess

    thisDir = os.path.dirname(__file__)
    versionFile = os.path.join(thisDir, '../setup.py')
    if os.path.exists(versionFile):
        pattern = "VERSION = "
        versionLine = next(r.strip() for r in open(versionFile).readlines() if pattern in r)
        versionStr = versionLine.replace(pattern, "").replace("\"", "").strip()
        if not re.match(r"^\d+\.\d+\.\d+$", versionStr):
            raise ValueError("Version string not in correct format: ", versionStr)

        try:
            gitOut = subprocess.run((f"git -C {thisDir} diff --quiet").split())
            if gitOut.returncode != 0:
                versionStr += '-dirty'
        except Exception:
            pass

    else:
        import pkg_resources  # type: ignore
        try:
            versionStr = pkg_resources.get_distribution("usrp-uhd-client").version
        except pkg_resources.DistributionNotFound:
            versionStr = "unknown"

    return versionStr


__version__ = _get_version()


__all__ = ["UsrpClient", "System",
           "MimoSignal",
           "TxStreamingConfig",
           "RxStreamingConfig",
           "RfConfig"]
