
from .rpc_client import UsrpClient
from .system import System
from uhd_wrapper.utils.config import MimoSignal, TxStreamingConfig, RxStreamingConfig, RfConfig


def _get_version() -> str:
    from uhd_wrapper.versioning import versionFromFile, versionFromPackage
    from os.path import join, dirname

    try:
        return versionFromFile(join(dirname(__file__), "../setup.py"),
                               "VERSION = ")
    except FileNotFoundError:
        return versionFromPackage("usrp-uhd-client")


__version__ = _get_version()


__all__ = ["UsrpClient", "System",
           "MimoSignal",
           "TxStreamingConfig",
           "RxStreamingConfig",
           "RfConfig"]
