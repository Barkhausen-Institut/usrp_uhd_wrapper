from typing import List, Tuple
import sys
import logging
import argparse
import numpy as np

from usrp_client import (System, RfConfig, UsrpClient,
                         TxStreamingConfig, RxStreamingConfig,
                         MimoSignal)


def _connectSystem(ips: List[str]) -> Tuple[System, List[UsrpClient]]:
    print("   Connecting USRPs...")

    system = System(logLevel=logging.WARN)
    clients = []
    for nr, ip in enumerate(ips):
        print("   usrp: ", ip, " ...")
        clients.append(system.newUsrp(usrpName=f"usrp{nr}", ip=ip))

    return system, clients


def _defaultRfConfig() -> RfConfig:
    Fs = 245.76e6
    return RfConfig(txAnalogFilterBw=400e6,
                    rxAnalogFilterBw=400e6,
                    txSamplingRate=Fs,
                    rxSamplingRate=Fs,
                    txGain=20,
                    rxGain=20,
                    txCarrierFrequency=3.7e9,
                    rxCarrierFrequency=3.7e9,
                    noTxAntennas=1,
                    noRxAntennas=1)


def _findFirstSampleInFrameOfSignal(frame: np.ndarray, txSignal: np.ndarray) -> int:
    correlation = np.abs(np.correlate(frame, txSignal))
    return np.argsort(correlation)[-1]


def checkSynchronization(ips: List[str]) -> bool:
    """Check if the USRPs are reachable and are synchronized to the same clock

    Args:
        ips: List of IP-Adresses of the USRPs to check, where the RPC server needs to run.

    Return:
        True if all is reachable and correctly cabled. False otherwise
    """

    print("Checking Timing Synchronization between USRP... ")
    system, _ = _connectSystem(ips)

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


def checkSingle(ip: str) -> bool:
    print("Starting simple Single-USRP TX-Rx-Test...")
    client = UsrpClient.create(ip=ip)

    rfConfig = _defaultRfConfig()
    client.configureRfConfig(rfConfig)

    signal = np.random.rand(1000) - 0.5
    peaks = []

    for i in range(3):

        client.configureTx(TxStreamingConfig(sendTimeOffset=0.0,
                                             samples=MimoSignal(signals=[signal])))
        client.configureRx(RxStreamingConfig(receiveTimeOffset=0.0,
                                             noSamples=2*len(signal)))

        client.executeImmediately()
        rxSig = client.collect()

        peaks.append(_findFirstSampleInFrameOfSignal(rxSig[0].signals[0], signal))

    peakDiff = max(peaks) - min(peaks)
    print("   Found peaks: ", peaks)
    if peakDiff > 5:
        print("   Peaks too far apart!. Check if antennas are connected")
        print("ERROR")
        return False
    else:
        print("SUCCESS")
        return True


def checkTrx(ips: List[str]) -> bool:
    print("Starting simple Multi-USRP TX-Rx-Test...")
    system, clients = _connectSystem(ips[:2])

    rfConfig = _defaultRfConfig()
    clients[0].configureRfConfig(rfConfig)
    clients[1].configureRfConfig(rfConfig)

    signal = np.random.rand(1000) - 0.5
    peaks = []

    for i in range(3):

        system.configureTx("usrp0", TxStreamingConfig(sendTimeOffset=0.0,
                                                      samples=MimoSignal(signals=[signal])))
        system.configureRx("usrp1", RxStreamingConfig(receiveTimeOffset=0.0,
                                                      noSamples=2*len(signal)))

        system.execute()
        rxSig = system.collect()

        peaks.append(_findFirstSampleInFrameOfSignal(rxSig["usrp1"][0].signals[0], signal))

    peakDiff = max(peaks) - min(peaks)
    print("   Found peaks: ", peaks)
    if peakDiff > 5:
        print("   Peaks too far apart!. Check if antennas are connected")
        print("ERROR")
        return False
    else:
        print("SUCCESS")
        return True


def parseArgs() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run several sanity tests against USRPs")
    parser.add_argument("--sync", action="store_true",
                        help="Run the synchronization test against all USRPs",
                        default=False)
    parser.add_argument("--trx", action="store_true",
                        help="Run a transmission from first to second USRP in <ips>",
                        default=False)
    parser.add_argument("--single", action="store_true",
                        help="Run a transmission on a single USRP",
                        default=False)
    parser.add_argument("--ips", required=True, nargs="+",
                        help="List of IPs to check")

    return parser.parse_args()


def main() -> None:
    args = parseArgs()
    success = True
    if args.sync:
        success = success & checkSynchronization(ips=args.ips)
    if args.trx:
        success = success & checkTrx(ips=args.ips)
    if args.single:
        success = success & checkSingle(ip=args.ips[0])

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
