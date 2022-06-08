Synchronisation
===============

If a :py:class:`usrp_client.system.System` consists of multiple USRPs, their clocks and their carrier frequencies
need to be synchronized. We assume that the USRPs have a `PPS in` port that accepts Pulse Per Second (PPS) signals. This signal is provided by an external device.

The USRPs have a built-in trigger that detects PPS signals. Once a PPS signal arrives,
the internal USRP time can be set to zero.

Upon calling :py:mod:`usrp_client.system.System.execute`, the client queries the USRPs FPGA time. If the time
differences between the different FPGA times are above `System.syncThresholdSec`, we request
the UHD to set the FPGA time to zero upon the next PPS edge. It is to be noted that ZeroMQ,
which is the communication protocol we use, does not support broadcast with acknowledgements.
We found a workaround which entails a certain latency between each message of the "broadcast".
Therefore, after synchronisation we query the FPGA times again and check if the FPGA times
are equal up to the threshold. If not, we synchronize again up to `System.syncAttempts` times.
We wait `System.timeBetweenSyncAttempts` seconds for the next synchronisation attempt.

After `System.syncTimeOut` seconds we check if the synchronisation is still valid.

You may check the :py:class:`documentation of the System class <usrp_client.system.System>`

The radio frequencies need to be synchronized again. This does not need to be triggered
however.
