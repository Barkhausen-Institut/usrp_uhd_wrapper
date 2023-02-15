

def _get_version() -> str:
    import os
    import subprocess

    thisDir = os.path.dirname(__file__)
    versionFile = os.path.join(thisDir, '../VERSION')
    if os.path.exists(versionFile):
        versionStr = open(versionFile).read().strip()
        try:
            gitOut = subprocess.run((f"git -C {thisDir} diff --quiet").split())
            if gitOut.returncode != 0:
                versionStr += '-dirty'
        except Exception:
            pass

    else:
        import pkg_resources  # type: ignore
        try:
            versionStr = pkg_resources.get_distribution("usrp-uhd-server").version
        except pkg_resources.DistributionNotFound:
            versionStr = "unknown"

    return versionStr


__version__ = _get_version()
