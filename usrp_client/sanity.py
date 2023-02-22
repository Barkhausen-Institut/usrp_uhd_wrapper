from typing import List
import sys
import logging
import argparse

from usrp_client import System

def checkSynchronization(ips: List[str]) -> bool:
    """Check if the USRPs are reachable and are synchronized to the same clock

    Args:
        ips: List of IP-Adresses of the USRPs to check, where the RPC server needs to run.

    Return:
        True if all is reachable and correctly cabled. False otherwise
    """

    print("Checking Timing Synchronization between USRP... ")
    print("   Connecting USRPs...")

    system = System(logLevel=logging.WARN)
    for nr, ip in enumerate(ips):
        print("   usrp: ", ip, " ...")
        system.newUsrp(usrpName=f"usrp{nr}", ip=ip)

    print("   Synchronizing USRPs")
    system.resetFpgaTimes()
    system.synchronizeUsrps()

    print("   FPGA times after reset: ", system.getCurrentFpgaTimes())

    syncValid = system.synchronisationValid()
    if syncValid:
        print("SUCCESS")
        return True
    else:
        print("ERROR, sync could not be established!")
        return False


def parseArgs() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run several sanity tests against USRPs")
    parser.add_argument("--sync", action="store_true",
                        help="Run the synchronization test against all USRPs",
                        default=False)
    parser.add_argument("--ips", required=True, nargs="+",
                        help="List of IPs to check")

    return parser.parse_args()


def main() -> None:
    args = parseArgs()
    success = True
    if args.sync:
        success = success & checkSynchronization(ips=args.ips)

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
