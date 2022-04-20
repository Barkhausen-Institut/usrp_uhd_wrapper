import sys
import argparse
sys.path.extend(["release_build/lib/", "debug_build/lib/", "build/lib/"])
import usrp_pybinding
from utils import RandomSignal, findFirstSampleInFrameOfSignal, dumpSamples

parser = argparse.ArgumentParser()
parser.add_argument("--tx-time-offset", type=float)
parser.add_argument("--rx-time-offset", type=float)
args = parser.parse_args()

NO_TX_SAMPLES = int(10e3)
NO_RX_SAMPLES = int(60e3)

txSignal = RandomSignal()
txSignal.create(NO_TX_SAMPLES, 1)

rfConfig = usrp_pybinding.RfConfig()    
rfConfig.txGain = [50]
rfConfig.rxGain = [40]
rfConfig.txCarrierFrequency = [2e9]
rfConfig.rxCarrierFrequency = [2e9]
rfConfig.txAnalogFilterBw = 400e6
rfConfig.rxAnalogFilterBw = 400e6
rfConfig.txSamplingRate = 50e6
rfConfig.rxSamplingRate = 50e6

rxStreamingConfig = usrp_pybinding.RxStreamingConfig()
rxStreamingConfig.noSamples = NO_RX_SAMPLES
rxStreamingConfig.receiveTimeOffset = args.rx_time_offset

txStreamingConfig = usrp_pybinding.TxStreamingConfig()
txStreamingConfig.samples = [txSignal.samples]
txStreamingConfig.sendTimeOffset = args.tx_time_offset

ip = "localhost"
usrp = usrp_pybinding.createUsrp(ip)
usrp.setRfConfig(rfConfig)
usrp.setTxConfig(txStreamingConfig)
usrp.setRxConfig(rxStreamingConfig)
_ = input("Press enter to synchronize devices and to continue")
usrp.setTimeToZeroNextPps()
usrp.execute(0.0)
samples = usrp.collect()
usrp.reset()
dumpSamples("rxSamples.csv", samples[0])
dumpSamples("txSamples.csv", txSignal.samples)
