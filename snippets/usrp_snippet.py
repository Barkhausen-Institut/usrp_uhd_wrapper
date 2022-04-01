import sys
sys.path.extend(["release_build/lib/", "debug_build/lib/", "build/lib/"])
import pymod
import numpy as np

rfConfig = pymod.RfConfig()    
rfConfig.txGain = [50];
rfConfig.rxGain = [30];
rfConfig.txCarrierFrequency = [2e9];
rfConfig.rxCarrierFrequency = [2e9];
rfConfig.txAnalogFilterBw = 400e6;
rfConfig.rxAnalogFilterBw = 400e6;
rfConfig.txSamplingRate = 10e6;
rfConfig.rxSamplingRate = 10e6;

rxStreamingConfig = pymod.RxStreamingConfig()
rxStreamingConfig.noSamples = int(60e3);
rxStreamingConfig.receiveTimeOffset = 2.0;

ip = "localhost"
usrp = pymod.createUsrp(ip)
usrp.setRfConfig(rfConfig)
usrp.setRxConfig(rxStreamingConfig)
usrp.setTimeToZeroNextPps()
samples = usrp.execute(0.0)
breakpoint()