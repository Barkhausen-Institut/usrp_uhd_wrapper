# Purpose

In **hardware_tests**, we provide some files that may be used to test the hardware directly using the python binding for the UHD wrapper only. These are to be executed on the USRP with the RPC server being stopped.

**Sending samples localhost**:

Before use, run, from repository root directory
```bash
python3 hardware_tests/send_signal_localhost.py
```

It sends and receives a random signal (can easily be modified) of length `10k` samples via localhost. Afterwards, it calculates where the transmitted signal can be found in the received signal. It should print `62` (+-2). This corresponds to the delay, with the defined RF config, between transmitting and receiving. Check the file, it should be self-explanatory.

**Multi device sync:**

From your laptop, run `tmux` and split it into two panes. `ssh` into two usrps and pull this repository. Run...

... on usrp 1

```bash
python3 hardware_tests/multi_device_sync.py --tx-time-offset 2.0 --rx-time-offset 2.5
```

... on usrp 2
```bash
python3 hardware_tests/multi_device_sync.py --rx-time-offset 2.0 --tx-time-offset 2.5
```

Afterwards, synchronize the panes via `Ctrl B` and then `:setw synchronize-panes on`. If asked, press any button to synchronize the usrps. A random signal is sent from usrp 1 to usrp 2. **The synchronization is valid, if the transmitted signal starts at sample 62 +- 1 in the received frame**. For debugging purposes, the samples are dumped in `rxSamples.csv` and `txSamples.csv` in the root directory. **Copy txSamples.csv from usrp1 and rxSamples.csv from usrp2 and correlate them**.