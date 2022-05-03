from typing import Tuple

import numpy as np

from usrp_client.system import System
from uhd_wrapper.utils.config import RfConfig, TxStreamingConfig, RxStreamingConfig
from examples.helpers import createRandom, printDelays, plot, readArgs


def createSystem(
    fc: float, fs: float, txGain: float, rxGain: float, ipUsrp1: str, ipUsrp2: str
) -> System:
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
    system.addUsrp(rfConfig=rfConfig, ip=ipUsrp1, usrpName="usrp1")
    system.addUsrp(rfConfig=rfConfig, ip=ipUsrp2, usrpName="usrp2")
    return system


def createStreamingConfigs(
    streamingOffset: float,
    txSignal: np.ndarray,
    noRxSamples: float,
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
    system = createSystem(
        fc=args.carrier_frequency,
        fs=245e6,
        txGain=35,
        rxGain=35,
        ipUsrp1=args.usrp1_ip,
        ipUsrp2=args.usrp2_ip,
    )
    txSignal = createRandom(noSamples=int(20e3))
    txStreamingConfig1, rxStreamingConfig1, rxStreamingConfig2 = createStreamingConfigs(
        streamingOffset=0.0,
        txSignal=txSignal,
        noRxSamples=60e3,
    )

    for _ in range(10):
        system.configureTx(usrpName="usrp1", txStreamingConfig=txStreamingConfig1)
        system.configureRx(usrpName="usrp1", rxStreamingConfig=rxStreamingConfig1)

        system.configureRx(usrpName="usrp2", rxStreamingConfig=rxStreamingConfig2)

        system.execute()
        samples = system.collect()
        printDelays(samples, txSignal)
        if args.plot:
            plot(samples)
            break


if __name__ == "__main__":
    main()
