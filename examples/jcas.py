from typing import Tuple

import numpy as np

from usrp_client.system import System
from uhd_wrapper.utils.config import (
    RfConfig,
    TxStreamingConfig,
    RxStreamingConfig,
    MimoSignal,
)
from examples.helpers import createRandom, printDelays, plot, readArgs


def createSystem(
    fc: float, fs: float, txGain: float, rxGain: float, ipUsrp1: str, ipUsrp2: str
) -> System:
    """This functions creates a system.

    The USRPs themselves can only be accessd via the `System` class. If you want
    to access a new USRP, you have to create a System beforehand and call the function
    `addUsrp`. The radio frontend configuration is defined using the `RfConfig` dataclass,
    cf. below.
    """
    # create configurations
    rfConfig = RfConfig()
    rfConfig.rxAnalogFilterBw = 400e6
    rfConfig.txAnalogFilterBw = 400e6
    rfConfig.rxSamplingRate = fs
    rfConfig.txSamplingRate = fs
    rfConfig.rxGain = rxGain
    rfConfig.txGain = txGain
    rfConfig.rxCarrierFrequency = fc
    rfConfig.txCarrierFrequency = fc

    system = System()
    system.addUsrp(rfConfig=rfConfig, ip=ipUsrp1, usrpName="usrp1")
    system.addUsrp(rfConfig=rfConfig, ip=ipUsrp2, usrpName="usrp2")
    return system


def createStreamingConfigs(
    streamingOffset: float,
    txSignal: np.ndarray,
    noRxSamples: float,
) -> Tuple[TxStreamingConfig, RxStreamingConfig, RxStreamingConfig]:
    """The streaming configuration itself is created here.

    If you want to transmit and receive samples, you have to define a config.
    Both classes assume a certain offset relative to an implementation-defined timepoint
    in the near future. This timepoint is the same for all streaming configs, such that
    two configs with the same offset refer to exactly the same time in the future. Offset
    can be zero.
    Further, you can define the samples to send and the number of samples to receive.
    """
    txStreamingConfig1 = TxStreamingConfig(
        sendTimeOffset=streamingOffset, samples=MimoSignal(signals=[txSignal])
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
        # we send the streaming configs to the USRPs
        system.configureTx(usrpName="usrp1", txStreamingConfig=txStreamingConfig1)
        system.configureRx(usrpName="usrp1", rxStreamingConfig=rxStreamingConfig1)

        system.configureRx(usrpName="usrp2", rxStreamingConfig=rxStreamingConfig2)

        # this command resets the internal USRP clocks to t=0
        # (cf. documentation of createStreamingConfigs) and synchronizes the USRPs.
        # samples are buffered
        system.execute()
        samples = system.collect()
        # samples are collected from all USRPs.

        printDelays(samples, txSignal)
        if args.plot:
            plot(samples)
            break


if __name__ == "__main__":
    main()
