from typing import Any, Dict, Union
import argparse

import numpy as np

from usrp_client.system import System
from uhd_wrapper.utils.config import RfConfig, TxStreamingConfig, RxStreamingConfig
from examples.helpers import createRandom, printDelays, plot


def readArgs() -> Any:
    parser = argparse.ArgumentParser()
    parser.add_argument("--usrp1-ip", type=str, help="IP of first USRP")
    parser.add_argument("--usrp2-ip", type=str, help="IP of second USRP")
    parser.add_argument(
        "--carrier-frequency", type=float, help="Carrier frequency of sent signal"
    )
    parser.add_argument(
        "--plot",
        action="store_true",
        help="Plot received singals in time and frequency",
    )
    args = parser.parse_args()
    return args


def createSystem(
    fc: float, fs: float, txGain: float, rxGain: float, ipUsrp1: str, ipUsrp2: str
) -> System:
    rfConfig = RfConfig()
    rfConfig.rxAnalogFilterBw = 400e6
    rfConfig.txAnalogFilterBw = 400e6
    rfConfig.rxSamplingRate = fs
    rfConfig.txSamplingRate = fs
    rfConfig.rxGain = [rxGain]
    rfConfig.txGain = [txGain]
    rfConfig.rxCarrierFrequency = [fc]
    rfConfig.txCarrierFrequency = [fc]

    # ceate system
    system = System()
    system.addUsrp(rfConfig=rfConfig, ip=ipUsrp1, usrpName="usrp1")
    system.addUsrp(rfConfig=rfConfig, ip=ipUsrp2, usrpName="usrp2")
    return system


def createStreamingConfigs(
    txSignal: np.ndarray, noRxSamples: float
) -> Dict[str, Dict[str, Union[RxStreamingConfig, TxStreamingConfig]]]:

    txStreamingConfig1 = TxStreamingConfig(sendTimeOffset=0.0, samples=[txSignal])
    rxStreamingConfig1 = RxStreamingConfig(
        receiveTimeOffset=0.1, noSamples=int(noRxSamples)
    )

    txStreamingConfig2 = TxStreamingConfig(sendTimeOffset=0.1, samples=[txSignal])
    rxStreamingConfig2 = RxStreamingConfig(
        receiveTimeOffset=0.0, noSamples=int(noRxSamples)
    )
    configs = {
        "usrp1": {"rx": rxStreamingConfig1, "tx": txStreamingConfig1},
        "usrp2": {"rx": rxStreamingConfig2, "tx": txStreamingConfig2},
    }
    return configs


def main() -> None:
    args = readArgs()
    system = createSystem(
        fc=args.carrier_frequency,
        fs=245e6 / 2,
        txGain=35,
        rxGain=35,
        ipUsrp1=args.usrp1_ip,
        ipUsrp2=args.usrp2_ip,
    )
    txSignal = createRandom(noSamples=int(20e3))
    streamingConfigs = createStreamingConfigs(txSignal=txSignal, noRxSamples=60e3)
    system.configureTx(
        usrpName="usrp1", txStreamingConfig=streamingConfigs["usrp1"]["tx"]
    )
    system.configureRx(
        usrpName="usrp1", rxStreamingConfig=streamingConfigs["usrp1"]["rx"]
    )

    system.configureTx(
        usrpName="usrp2", txStreamingConfig=streamingConfigs["usrp2"]["tx"]
    )
    system.configureRx(
        usrpName="usrp2", rxStreamingConfig=streamingConfigs["usrp2"]["rx"]
    )
    system.execute()
    samples = system.collect()
    printDelays(samples=samples, txSignal=txSignal)

    if args.plot:
        plot(samples)


if __name__ == "__main__":
    main()
