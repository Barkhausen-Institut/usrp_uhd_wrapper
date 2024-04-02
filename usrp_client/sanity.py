from typing import List, Tuple
import sys
import logging
import argparse
import numpy as np
import matplotlib.pyplot as plt

from usrp_client import (System, RfConfig, UsrpClient,
                         TxStreamingConfig, RxStreamingConfig,
                         MimoSignal)

cmdlineArgs: argparse.Namespace


def _connectSystem(ips: List[str]) -> Tuple[System, List[UsrpClient]]:
    print("   Connecting USRPs...")

    system = System(logLevel=logging.WARN)
    clients = []
    for nr, ip in enumerate(ips):
        print("   usrp: ", ip, " ...")
        clients.append(system.newUsrp(usrpName=f"usrp{nr}", ip=ip))

    return system, clients


def _defaultRfConfig() -> RfConfig:
    Fs = cmdlineArgs.fs
    return RfConfig(txAnalogFilterBw=400e6,
                    rxAnalogFilterBw=400e6,
                    txSamplingRate=Fs,
                    rxSamplingRate=Fs,
                    txGain=cmdlineArgs.tx_gain,
                    rxGain=cmdlineArgs.rx_gain,
                    txCarrierFrequency=cmdlineArgs.fc,
                    rxCarrierFrequency=cmdlineArgs.fc,
                    noTxStreams=1,
                    noRxStreams=1,
                    txAntennaMapping=[cmdlineArgs.tx_port],
                    rxAntennaMapping=[cmdlineArgs.rx_port],
                    )


def _findFirstSampleInFrameOfSignal(frame: np.ndarray, txSignal: np.ndarray) -> int:
    correlation = np.abs(np.correlate(frame, txSignal))
    return np.argsort(correlation)[-1]


def _calculateSNR(txSignal: np.ndarray, rxSignal: np.ndarray, peak: int) -> float:
    dcOffset = np.mean(rxSignal)
    rxSignal = rxSignal - dcOffset
    end = peak+len(txSignal)
    sigPart = rxSignal[peak:end]
    noisePart = rxSignal[end:end+1000]
    rxPow = np.mean(abs(sigPart) ** 2)
    rxNoise = np.mean(abs(noisePart) ** 2)

    return 10 * np.log10((rxPow-rxNoise)/rxNoise)


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
    snrs = []

    for i in range(3):

        client.configureTx(TxStreamingConfig(sendTimeOffset=0.0,
                                             samples=MimoSignal(signals=[signal])))
        client.configureRx(RxStreamingConfig(receiveTimeOffset=0.0,
                                             noSamples=2*len(signal)))

        client.executeImmediately()
        rxSig = client.collect()
        if cmdlineArgs.plot:
            plt.plot(abs(rxSig[0].signals[0]))
            plt.show()

        rx = rxSig[0].signals[0]
        peak = _findFirstSampleInFrameOfSignal(rx, signal)
        peaks.append(peak)
        snrs.append(_calculateSNR(signal, rx, peak))

    peakDiff = max(peaks) - min(peaks)
    print("   Found peaks: ", peaks)
    print("   SNRs       : ", snrs)
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
    snrs = []

    for i in range(3):

        system.configureTx("usrp0", TxStreamingConfig(sendTimeOffset=0.0,
                                                      samples=MimoSignal(signals=[signal])))
        system.configureRx("usrp1", RxStreamingConfig(receiveTimeOffset=0.0,
                                                      noSamples=2*len(signal)))

        system.execute()
        rxSig = system.collect()

        if cmdlineArgs.plot:
            plt.plot(abs(rxSig["usrp1"][0].signals[0]))
            plt.show()

        rx = rxSig["usrp1"][0].signals[0]
        peak = _findFirstSampleInFrameOfSignal(rx, signal)
        peaks.append(peak)
        snrs.append(_calculateSNR(signal, rx, peak))

    peakDiff = max(peaks) - min(peaks)
    print("   Found peaks: ", peaks)
    print("   SNRs       : ", snrs)
    if peakDiff > 5:
        print("   Peaks too far apart!. Check if antennas are connected")
        print("ERROR")
        return False
    else:
        print("SUCCESS")
        return True


def parseArgs() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run several sanity tests against USRPs",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    group = parser.add_argument_group("Test selection")
    group.add_argument("--sync", action="store_true",
                       help="Run the synchronization test against all USRPs",
                       default=False)
    group.add_argument("--trx", action="store_true",
                       help="Run a transmission from first to second USRP in <ips>",
                       default=False)
    group.add_argument("--single", action="store_true",
                       help="Run a transmission on a single USRP",
                       default=False)
    group.add_argument("--all", default=False, action='store_true',
                       help="Run all sanity tests")
    group.add_argument("--plot", action='store_true', default=False,
                       help="Plot received signals")

    group = parser.add_argument_group("USRP configuration")
    group.add_argument("--ips", required=True, nargs="+",
                       help="List of IPs to check",
                       default=argparse.SUPPRESS,
                       metavar="ip")
    group.add_argument("--fc", required=False, default=3.7e9,
                       help="Carrier frequency in Hz", type=float)
    group.add_argument("--tx-gain", required=False,
                       default=20, help="TX gain in dB", type=float)
    group.add_argument("--rx-gain", required=False,
                       default=20, help="RX gain in dB", type=float)
    group.add_argument("--fs", required=False, default=245.76e6, type=float,
                       help="Sampling rate in Hz")
    group.add_argument("--tx-port", required=False, default=0,
                       help="TX antenna port", type=int)
    group.add_argument("--rx-port", required=False, default=0,
                       help="RX antenna port", type=int)

    return parser.parse_args()


def main() -> None:
    global cmdlineArgs
    args = parseArgs()
    cmdlineArgs = args

    success = True
    if args.sync or args.all:
        success = success & checkSynchronization(ips=args.ips)
    if args.trx or args.all:
        success = success & checkTrx(ips=args.ips)
    if args.single or args.all:
        success = success & checkSingle(ip=args.ips[0])

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
