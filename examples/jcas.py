from typing import Any, Tuple
import argparse

import numpy as np

from usrp_client.system import System
from uhd_wrapper.utils.config import RfConfig, TxStreamingConfig, RxStreamingConfig
from examples.helpers import createRandom, printDelays, plot


def readArgs() -> Any:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--plot",
        action="store_true",
        help="Plot received singals in time and frequency",
    )
    args = parser.parse_args()
    return args


def createSystem(fc: float, fs: float, txGain: float, rxGain: float) -> System:
    # create configurations
    rfConfig = RfConfig()
    rfConfig.rxAnalogFilterBw = 400e6
    rfConfig.txAnalogFilterBw = 400e6
    rfConfig.rxSamplingRate = fs
    rfConfig.txSamplingRate = fs
    rfConfig.rxGain = [rxGain]
    rfConfig.txGain = [txGain]
    rfConfig.rxCarrierFrequency = [fc]
    rfConfig.txCarrierFrequency = [fc]

    system = System()
    system.addUsrp(rfConfig=rfConfig, ip="192.168.189.131", usrpName="usrp1")
    system.addUsrp(rfConfig=rfConfig, ip="192.168.189.133", usrpName="usrp2")
    return system


def createStreamingConfigs(
    streamingOffset: float, txSignal: np.ndarray, noRxSamples: float
) -> Tuple[TxStreamingConfig, RxStreamingConfig, RxStreamingConfig]:
    txStreamingConfig1 = TxStreamingConfig(
        sendTimeOffset=streamingOffset, samples=[txSignal]
    )
    rxStreamingConfig1 = RxStreamingConfig(
        receiveTimeOffset=streamingOffset, noSamples=int(noRxSamples)
    )
    rxStreamingConfig2 = RxStreamingConfig(
        receiveTimeOffset=streamingOffset, noSamples=int(noRxSamples)
    )
    return txStreamingConfig1, rxStreamingConfig1, rxStreamingConfig2


def main() -> None:
    args = readArgs()
    system = createSystem(fc=2e9, fs=245e6, txGain=35, rxGain=35)
    txSignal = createRandom(noSamples=int(20e3))
    txStreamingConfig1, rxStreamingConfig1, rxStreamingConfig2 = createStreamingConfigs(
        streamingOffset=0.0,
        txSignal=txSignal,
        noRxSamples=60e3,
    )
    from time import time

    startTime = time()
    for _ in range(10):
        system.configureTx(usrpName="usrp1", txStreamingConfig=txStreamingConfig1)
        system.configureRx(usrpName="usrp1", rxStreamingConfig=rxStreamingConfig1)

        system.configureRx(usrpName="usrp2", rxStreamingConfig=rxStreamingConfig2)

        system.execute()
        samples = system.collect()
        print(time() - startTime)
        printDelays(samples, txSignal)
        if args.plot:
            plot(samples)
            break


if __name__ == "__main__":
    main()
