import os
import subprocess

from .rpc_client import UsrpClient
from .system import System
from uhd_wrapper.utils.config import MimoSignal, TxStreamingConfig, RxStreamingConfig, RfConfig


def _get_version():
    thisDir = os.path.dirname(__file__)
    versionFile = os.path.join(thisDir, '../VERSION')
    if os.path.exists(versionFile):
        versionStr = open(versionFile).read().strip()
        gitOut = subprocess.run((f"git -C {thisDir} diff --quiet").split())
        if gitOut.returncode != 0:
            versionStr += '-dirty'

        print(versionStr)
        return versionStr


__version__ = _get_version()


__all__ = ["UsrpClient", "System",
           "MimoSignal",
           "TxStreamingConfig",
           "RxStreamingConfig",
           "RfConfig"]
