from typing import Any


def fillDummyRfConfig(conf: Any) -> Any:
    """Used for testing. Fills a dummy Rf Config."""
    conf.txCarrierFrequency = 2e9
    conf.txGain = 30
    conf.txAnalogFilterBw = 200e6
    conf.txSamplingRate = 20e6
    conf.noTxAntennas = 1

    conf.rxCarrierFrequency = 2.5e9
    conf.rxGain = 40
    conf.rxAnalogFilterBw = 100e6
    conf.rxSamplingRate = 30e6
    conf.noRxAntennas = 1
    return conf
