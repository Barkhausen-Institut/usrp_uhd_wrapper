Synchronisation
===============

If a :py:class:`usrp_client.system.System` consists of multiple USRPs, their clocks and their carrier frequencies
need to be synchronized. We assume that the USRPs have a `PPS in` port that accepts Pulse Per Second (PPS) signals. This signal is provided by an external device.

The USRPs have a built-in trigger that detects PPS signals. Once a PPS signal arrives,
the internal USRP time can be set to zero.