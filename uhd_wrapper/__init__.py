

def _get_version() -> str:
    from uhd_wrapper.versioning import versionFromFile, versionFromPackage
    from os.path import join, dirname

    try:
        return versionFromFile(join(dirname(__file__), "../setup.py"),
                               "VERSION = ")
    except FileNotFoundError:
        return versionFromPackage("usrp-uhd-server")


__version__ = _get_version()
