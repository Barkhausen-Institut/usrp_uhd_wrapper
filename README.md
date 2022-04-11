# Purpose
 
# Installation

This repo wraps the UHD for our X410. It is run on the USRP itself and offers an API via ZeroMQ.

# Install

On the usrp:

1. `git clone <this repo>`
2. `mkdir build && cd build`
3. `cmake ..`
4. `make`

# Use

**We strongly recommend, before use, to run some (hardware) tests!**

**Sending sampling localhost:**
Before use, run, from repository root directory
```bash
python3 hardware_tests/send_signal_localhost.py
```

It sends and receives a random signal (can easily be modified) of length `10k` samples via localhost. Afterwards, it calculates where the transmitted signal can be found in the received signal. It should print `62` (+-2). This corresponds to the delay, with the defined rf config, between transmitting and receiving. Check the file, it should be self-explanatory.

**Multi device sync:**

from your laptop, run `tmux` and split it into two panes. `ssh` into two usrps and pull this repository. Run for each usrp

```bash
python3 hardware_tests/multi_device_sync.py
```

Afterwards, synchronize the panes via `Ctrl B` and then `:setw synchronize-panes on`. If asked, press any button to synchronize the usrps. A random signal is sent from usrp 1 to usrp 2. **The synchronization is valid, if the transmitted signal starts at sample 62 +- 1 in the received frame**. For debugging purposes, the samples are dumped in `rxSamples.csv` and `txSamples.csv` in the root directory.

**note:** as soon as the ZeroMQ client is implemented, this process will be improved, without the need of opening `tmux`!

# For Developers

In the `snippets` directory, snippets can be found. As the testing capabilities for the hardware are strongly limited, the snippets are meant for evaluating the hardware. Feel free to play around with it!