from dataclasses import fields
from typing import List
import json

from uhd_wrapper.utils.serialization import (
    SerializedComplexArray,
)
from uhd_wrapper.usrp_pybinding import (
    Usrp,
    TxStreamingConfig,
    RxStreamingConfig,
)
from uhd_wrapper.usrp_pybinding import RfConfig as RfConfigBinding
from uhd_wrapper.utils.config import RfConfig, MimoSignal


def RfConfigFromBinding(rfConfigBinding: RfConfigBinding) -> RfConfig:
    c = RfConfig()
    for field in fields(RfConfig):
        setattr(c, field.name, getattr(rfConfigBinding, field.name))
    return c


def RfConfigToBinding(rfConfig: RfConfig) -> RfConfigBinding:
    cBinding = RfConfigBinding()
    for field in fields(RfConfig):
        setattr(cBinding, field.name, getattr(rfConfig, field.name))
    return cBinding


class UsrpServer:
    def __init__(self, usrp: Usrp) -> None:
        self.__usrp = usrp

        # Forward all calls from this object to __usrp. However,
        # do not forward calls which are explicitely implemented
        # in the class. These methods usually require advanced
        # serialization.
        methods = [method for method in dir(usrp)
                   if callable(getattr(usrp, method))]
        for m in methods:
            if not hasattr(self, m):
                print("Setting up automatic call forwarding to", m)
                setattr(self, m, getattr(self.__usrp, m))

    def getVersion(self) -> str:
        import uhd_wrapper
        return uhd_wrapper.__version__

    def configureTx(
            self, sendTimeOffset: float, samples: List[SerializedComplexArray],
            numRepetitions: int
    ) -> None:
        mimoSignal = MimoSignal.deserialize(samples)
        self.__usrp.setTxConfig(

            TxStreamingConfig(
                samples=mimoSignal.signals,
                sendTimeOffset=sendTimeOffset,
                numRepetitions=numRepetitions
            )
        )

    def configureRx(self, jsonStr: str) -> None:
        self.__usrp.setRxConfig(RxStreamingConfig.schema().loads(jsonStr))

    def configureRfConfig(self, serializedRfConfig: str) -> None:
        self.__usrp.setRfConfig(
            RfConfigToBinding(RfConfig.deserialize(serializedRfConfig))
        )

    def collect(self) -> List[List[SerializedComplexArray]]:
        mimoSignals = [MimoSignal(signals=c) for c in self.__usrp.collect()]
        return [s.serialize() for s in mimoSignals]

    def getRfConfig(self) -> str:
        return RfConfigFromBinding(self.__usrp.getRfConfig()).serialize()
