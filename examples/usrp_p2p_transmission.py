from typing import Dict, Tuple

import numpy as np

from usrp_client.system import System
from uhd_wrapper.utils.config import (
    RfConfig,
    TxStreamingConfig,
    RxStreamingConfig,
    MimoSignal,
)
from examples.helpers import createRandom, printDelays, plotP2pSiso, readArgs


def createSystem(
    fc: float, fs: float, txGain: float, rxGain: float, ipUsrp1: str, ipUsrp2: str
) -> System:
    rfConfig = RfConfig()
    rfConfig.rxAnalogFilterBw = 400e6
    rfConfig.txAnalogFilterBw = 400e6
    rfConfig.rxSamplingRate = fs
    rfConfig.txSamplingRate = fs
    rfConfig.rxGain = rxGain
    rfConfig.txGain = txGain
    rfConfig.rxCarrierFrequency = fc
    rfConfig.txCarrierFrequency = fc
    rfConfig.noRxStreams = 1
    rfConfig.noTxStreams = 1

    # ceate system
    system = System()
    system.newUsrp(ip=ipUsrp1, usrpName="usrp1").configureRfConfig(rfConfig)
    system.newUsrp(ip=ipUsrp2, usrpName="usrp2").configureRfConfig(rfConfig)
    return system


def createStreamingConfigs(
    txSignal: np.ndarray, noRxSamples: float
) -> Dict[str, Tuple[RxStreamingConfig, TxStreamingConfig]]:

    txStreamingConfig1 = TxStreamingConfig(
        sendTimeOffset=0.0, samples=MimoSignal(signals=[txSignal])
    )
    rxStreamingConfig1 = RxStreamingConfig(
        receiveTimeOffset=0.1, numSamples=int(noRxSamples)
    )

    txStreamingConfig2 = TxStreamingConfig(
        sendTimeOffset=0.1, samples=MimoSignal(signals=[txSignal])
    )
    rxStreamingConfig2 = RxStreamingConfig(
        receiveTimeOffset=0.0, numSamples=int(noRxSamples)
    )
    configs = {
        "usrp1": (rxStreamingConfig1, txStreamingConfig1),
        "usrp2": (rxStreamingConfig2, txStreamingConfig2),
    }
    return configs


def main() -> None:
    args = readArgs()
    system = createSystem(
        fc=args.carrier_frequency,
        fs=122.88e6,
        txGain=30,
        rxGain=30,
        ipUsrp1=args.usrp1_ip,
        ipUsrp2=args.usrp2_ip,
    )
    txSignal = createRandom(numSamples=int(20e3))
    streamingConfigs = createStreamingConfigs(txSignal=txSignal, noRxSamples=60e3)
    system.configureTx(usrpName="usrp1", txStreamingConfig=streamingConfigs["usrp1"][1])
    system.configureRx(usrpName="usrp1", rxStreamingConfig=streamingConfigs["usrp1"][0])

    system.configureTx(usrpName="usrp2", txStreamingConfig=streamingConfigs["usrp2"][1])
    system.configureRx(usrpName="usrp2", rxStreamingConfig=streamingConfigs["usrp2"][0])
    system.execute()
    samples = system.collect()
    printDelays(samples=samples, txSignal=txSignal)

    if args.plot:
        plotP2pSiso(samples)


if __name__ == "__main__":
    main()
