import argparse

import uhd_wrapper.usrp_pybinding as usrp_pybinding
from uhd_wrapper.hardware_tests.utils import (
    Chirp,
    findFirstSampleInFrameOfSignal,
    dumpSamples,
)


parser = argparse.ArgumentParser()
parser.add_argument("--bandwidth", type=float, help="Bandwidth in Hz of chirp")
parser.add_argument(
    "--carrier-frequency", type=float, help="Carrier frequency of chirp"
)
args = parser.parse_args()

NO_TX_SAMPLES = int(10e3)
NO_RX_SAMPLES = int(60e3)
usrp = usrp_pybinding.createUsrp("localhost")

txSignal = Chirp(
    fStart=-args.bandwidth / 2, fStop=args.bandwidth / 2, fSampling=args.bandwidth
)
txSignal.create(NO_TX_SAMPLES, 1)

rfConfig = usrp_pybinding.RfConfig()
rfConfig.txGain = [20]
rfConfig.rxGain = [20]
rfConfig.txCarrierFrequency = [args.carrier_frequency]
rfConfig.rxCarrierFrequency = [args.carrier_frequency]
rfConfig.txAnalogFilterBw = 400e6
rfConfig.rxAnalogFilterBw = 400e6
rfConfig.txSamplingRate = args.bandwidth
rfConfig.rxSamplingRate = args.bandwidth

rxStreamingConfig = usrp_pybinding.RxStreamingConfig()
rxStreamingConfig.noSamples = NO_RX_SAMPLES
rxStreamingConfig.receiveTimeOffset = 2.0

txStreamingConfig = usrp_pybinding.TxStreamingConfig()
txStreamingConfig.samples = [txSignal.samples]
txStreamingConfig.sendTimeOffset = 2.0

usrp.setRfConfig(rfConfig)
usrp.setRxConfig(rxStreamingConfig)
usrp.setTxConfig(txStreamingConfig)
usrp.setTimeToZeroNextPps()
usrp.execute(0.0)
samples = usrp.collect()
usrp.reset()

# post-process
signalStartSample = findFirstSampleInFrameOfSignal(samples[0], txSignal.samples)
print(f"The siganl starts at sample {signalStartSample}")

# Optional: dump samples for plotting purposes.
dumpSamples("rxSamples.csv", samples[0])
dumpSamples("txSamples.csv", txSignal.samples)
