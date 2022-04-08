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

Before use, run, from repository root directory
```bash
python hardware_tests/send_signal_localhost.py
```

It sends and receives a random signal (can easily be modified) of length `10k` samples via localhost. Afterwards, it calculates where the transmitted signal can be found in the received signal. It should print `62` (+-2). This corresponds to the delay, with the defined rf config, between transmitting and receiving. Check the file, it should be self-explanatory.

# For Developers

In the `snippets` directory, snippets can be found. As the testing capabilities for the hardware are strongly limited, the snippets are meant for evaluating the hardware. Feel free to play around with it!