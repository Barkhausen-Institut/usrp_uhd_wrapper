
def versionFromFile(fileName: str, pattern: str) -> str:
    """Extract the version from a file.

    Searches for pattern, extracts the version string from the first line matching the pattern

    Args:
        fileName: file to open
        pattern: pattern to look for, e.g. "VERSION ="

    Raises:
        FileNotFoundError if the file cannot be opened
        ValueError: If the line with the pattern is not found or has wrong format.
    """

    import os
    import re
    import subprocess

    thisDir = os.path.dirname(fileName)

    if os.path.exists(fileName):
        pattern = "VERSION = "
        versionLine = next(r.strip() for r in open(fileName).readlines() if pattern in r)
        versionStr = versionLine.replace(pattern, "").replace("\"", "").strip()
        if not re.match(r"^\d+\.\d+\.\d+$", versionStr):
            raise ValueError("Version string not in correct format: ", versionStr)

        try:
            gitOut = subprocess.run((f"git -C {thisDir} diff --quiet").split())
            if gitOut.returncode != 0:
                versionStr += '-dirty'
        except Exception:
            pass

        return versionStr
    else:
        raise FileNotFoundError(fileName)


def versionFromPackage(packageName: str) -> str:
    """Extract version from the pkg_resources

    Args:
        packageName: package to look for within pkg_resources.get_distribution

    Returns:
        If package is found: version of that package. Otherwise "unknown"
    """
    import pkg_resources
    try:
        return pkg_resources.get_distribution(packageName).version
    except pkg_resources.DistributionNotFound:
        return "unknown"
