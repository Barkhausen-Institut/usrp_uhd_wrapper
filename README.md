# Purpose

This repo wraps the [Universal Hardware Driver](https://github.com/EttusResearch/uhd) (UHD) for [USRP X410](https://www.ni.com/de-de/support/model.ettus-usrp-x410.html). Since the authors of UHD point out that the driver is device-independent, this wrapper should support other USRPs out-of-the-box as well. It is to be noted that the configuration is different for the USRPs, therefore, some modifications most likely need to be made for other USRPs

We cover the following use-case: The USRP can be used with the full-mimo setup, i.e. four transmitting and four receiving antennas. The user creates the signal on his/her laptop, sends them **as bursts** to the USRP via network and collects the received samples. Post-processing happens on the laptop of the user. **We strongly emphasize that this wrapper is not meant for streaming. On top of that, USRPs are mainly designed for streaming use-cases. Therefore some adjustments had to be made to the wrapper.**

This repository contains the **client as well as the server code**. The client is to be used by the user for signal processing purposes and sending the commands to the USRP, which serves as a server. The server code is to be deployed on the USRP. Once built and installed, the USRP does not need to be touched again.

# Documentation

Documentation can be found [here](https://barkhausen-institut.github.io/usrp_uhd_wrapper/index.html).

Read this in conjunction with our example files located in **examples/**!

# Getting Started

## USRP is already setup

Assume somebody already deployed the USRP server code (cf. Install section) and gives you the IP address of the USRPs you may use. As a first step, you want to transmit some samples from USRP1 to USRP2.

Follow the Steps of Install/Client below to install the client. Afterwards proceed to the Examples section.

## USRP is not setup

`ssh` to the USRP and follow the steps of Install/Server below. Afterwards proceed with the steps of the previous section. Ensure that the USRP was restarted.

# Install

## Server
For installing the server on the USRP (needs to be done only once per USRP):

1. `git clone <this repo> && cd <repo>`
2. `python3 -m venv env && . env/bin/activate`
3. `pip install -e .`
4. `cd uhd_wrapper && mkdir build`
5. `cd build`
6. `cmake -DCMAKE_BUILD_TYPE=Release ..`
7. `make -j4`
8. `make install`
9. `ctest -V` to check if the tests pass

To start the usrp server as a service, run: `systemctl enable rpc-server.service`. Restart.
The USRP server needs a minute to start.

## Client

1. Ensure that you use at least python3.9.
2. Create and activate virtual env (on linux: `python -m venv env && . env/bin/activate`)
3. `pip install -e .`
4. **For running tests:** `pip install -r requirements_tests.txt`

# Before Use

We provide integration tests, i.e. we run tests against the hardware covering some easy usecases (e.g., joint communication and sensing (JCAS), local transmission, peer-to-peer-transmission...). If you want to execute them, the environment variables `USRP1_IP` and `USRP2_IP` with the corresponding IP need to be set. Execute the command `pytest .` or, if you just want to execute the hardware-related tests: `pytest . -m "hardware"`. **It is highly recommended to execute these tests before conducting your measurements**:

On client side:

```bash
$ cd <repo>
$ . env/bin/activate
$ USRP1_IP=<usrp1-ip> USRP2_IP=<usrp2-ip> pytest . -m "hardware"
$ pytest .
```

# Use

After install, there are two python packages installed: `usrp_client` serving as the client that sends commands (e.g. radio frontend (RF) config, samples, etc.) to the USRP server. The `uhd_wrapper.utils` package contains dataclasses for the configurations (module `config`) and some serialization functions in the `serialization` module.

Assuming you installed the client, always activate the virtual environment via:

```bash
$ cd <repo>
$ . env/bin/activate
```

**Note**: If you restart the USRP, the server needs a minute to start.

## Examples

The **examples** directory contains some examples. In each example file, we will print if the sent signal can be found in the received frame. The printed delay should be more or less (i.e. +- 5 sampels) deterministic, depending on sample rate. All examples are to be run from the client side. **Port 5555 is used.** We add the option to plot signals. Examples should be self-explanatory.

**localhost_transmission**: Sends random signal from a dedicated USRP to itself, check file.

Usage:

```bash
$ python examples/localhost_transmission.py --usrp1-ip <ip> --carrier-frequency <carrier-frequency> --plot
```

**usrp_p2p_transmission**: Sends random signal from Usrp1 to Usrp2, check file.

Usage:

```bash
$ python examples/usrp_p2p_transmission.py --usrp1-ip <ip> --usrp2-ip <ip> --carrier-frequency <carrier-frequency> --plot
```

**JCAS**: Implements the JCAS scenario, but using a random signal instead.
Usage:

```bash
$ python examples/jcas.py --usrp1-ip <ip> --usrp2-ip <ip> --carrier-frequency <carrier-frequency> --plot
```

Sends a random signal from USRP1 to USRP2, while receiving at USRP1 as well. If `--plot` argument is omitted, the signal will be sent/received 10 times a row.

**mimo_p2p_transmission**: Implements a 4x4 MIMO scenario.
Usage:

```bash
$ python examples/mimo_p2p_transmission.py --usrp1-ip <ip> --usrp2-ip <ip> --carrier-frequency <carrier-frequency> --plot
```

Creates four random signals, that are distributed to the antennas. They are shifted by 10k samples. Usrp2 receives the signals at four antennas.

## hardware_tests

We have some hardware tests, for testing/debugging purposes mainly. Samples are dumped as well for better analysis. They are to be run from the USRP directly. Files are located in the **hardware_tests** folder.

**Note**: The Usrp service should be stopped for this purpose!


# For Developers

In the `snippets` directory, snippets can be found. As the testing capabilities for the hardware are strongly limited, the snippets are meant for evaluating the hardware. 

We also have a **debug** folder that contains some files to be used for debugging:

- tx_stream: streams white noise (mean 0, std 2) that may be analysed with a spectrum analyzer. **Note**: Underflow occurs, i.e. samples are not buffered fast enough into the FPGA. To verify if a signal is sent at all, this is sufficient however

# Change History

- `0.0-siso-jcas`: One antenna for transmitting and receiving is supported. Further, we support receiving and transmitting at one USRP with a second USRP receiving only. This covers the usecase of JCAS.
- `0.1-mimo`: Full-fledged MIMO support.