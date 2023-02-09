from typing import List, Tuple, Dict

import numpy as np

from usrp_client.system import System
from uhd_wrapper.utils.config import (
    RfConfig,
    TxStreamingConfig,
    RxStreamingConfig,
    MimoSignal,
)
from examples.helpers import (
    createRandom,
    readArgs,
    findFirstSampleInFrameOfSignal,
    plotMimo,
)


def printDelays(samples: Dict[str, List[MimoSignal]], txSignal: MimoSignal) -> None:
    for antIdx in range(4):
        txSignalStartUsrp2, _ = findFirstSampleInFrameOfSignal(
            samples["usrp2"][0].signals[antIdx], txSignal.signals[antIdx]
        )
        print(
            f"Transmitted signal at antenna {antIdx} from usrp1 starts at"
            f"sample {txSignalStartUsrp2} in usrp2"
        )


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
    rfConfig.noRxAntennas = 4
    rfConfig.noTxAntennas = 4

    # ceate system
    system = System()
    system.addUsrp(ip=ipUsrp1, usrpName="usrp1").configureRfConfig(rfConfig)
    system.addUsrp(ip=ipUsrp2, usrpName="usrp2").configureRfConfig(rfConfig)
    return system


def createStreamingConfigs(
    txSignal: MimoSignal, noRxSamples: float
) -> Tuple[TxStreamingConfig, RxStreamingConfig]:

    txStreamingConfig1 = TxStreamingConfig(sendTimeOffset=0.0, samples=txSignal)

    rxStreamingConfig2 = RxStreamingConfig(
        receiveTimeOffset=0.0, noSamples=int(noRxSamples)
    )
    return txStreamingConfig1, rxStreamingConfig2


def createTxSignal() -> Tuple[MimoSignal, MimoSignal]:
    # create signal
    signalLength = 5000
    signalStarts = [int(10e3), int(20e3), int(30e3), int(40e3)]
    antTxSignals = [
        createRandom(signalLength),
        createRandom(signalLength),
        createRandom(signalLength),
        createRandom(signalLength),
    ]
    paddedAntTxSignals = []
    for antSignal, signalStart in zip(antTxSignals, signalStarts):
        s = np.zeros(int(55e3), dtype=np.complex64)
        s[signalStart + np.arange(antSignal.size)] = antSignal
        paddedAntTxSignals.append(s)
    return MimoSignal(signals=paddedAntTxSignals), MimoSignal(signals=antTxSignals)


def main() -> None:
    args = readArgs()
    system = createSystem(
        fc=args.carrier_frequency,
        fs=12.288e6,
        txGain=30,
        rxGain=30,
        ipUsrp1=args.usrp1_ip,
        ipUsrp2=args.usrp2_ip,
    )
    paddedMimoSignals, unpaddedMimoSignals = createTxSignal()
    txStreamingConfig1, rxStreamingConfig2 = createStreamingConfigs(
        txSignal=paddedMimoSignals, noRxSamples=55e3
    )
    system.configureTx(usrpName="usrp1", txStreamingConfig=txStreamingConfig1)
    system.configureRx(usrpName="usrp2", rxStreamingConfig=rxStreamingConfig2)
    system.execute()
    samples = system.collect()
    printDelays(samples, unpaddedMimoSignals)

    if args.plot:
        plotMimo(samples, "usrp2")


if __name__ == "__main__":
    main()
