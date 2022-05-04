# Purpose

This repo wraps the UHD for our X410. It contains the **client as well as the server**. The client is to be used by the user for signal processing purposes and sending the commands to the USRP, which serves as a server.

Current versions of server are running on 192.168.189.131/134. **If you want to run code as a client against USRPs, only use these USRPs at the moment.**

# Install

On the usrp (server):
Install libzmq beforehand.

1. `git clone <this repo>`
2. `python3 -m venv env && . env/bin/activate`
3. `pip install -e .`
4. `cd usrp_uhd_wrapper && mkdir build`
5. `cd build`
6. `cmake -DCMAKE_BUILD_TYPE=Release ..`
7. `make`
8. `make install`
9. `ctest -V` to check if the tests pass

To start the usrp server as a service, run:

1. `systemctl start rpc-server.service`
2. `systemctl enable rpc-server.service`

For the client:

1. Ensure that you use at least python3.9.
2. Create and activate virtual env (on linux: `python -m venv env && . env/bin/activate`)
3. `pip install -e .`
4. **For running tests:** `pip install -r requirements_tests.txt && pytest usrp_client/`

# Use

After install, there are two python packages installed: `usrp_client` serving as the client that sends commands (e.g. RF config, samples, etc.) to the usrp server. The `uhd_wrapper.utils` package contains dataclasses for the configurations (module `config`, check there!) and some serialization functions in the `serialization` module.

We implemented a multidevice setup with SISO only. It is easily extendible however. The examples below will explain its usage until further documentaiton will follows.

**Note**: Ensure that the usrp server is started:

ssh to usrp.

1. `cd <repo>`
2. `. env/bin/activate`
3. `python start_usrp_server.py`


## Examples

The **examples** directory contains two examples. In each example file, we will print when the sent signal can be found in the received frame. The printed delay should be more or less (i.e. +- 5 sampels) deterministic, depending on sample rate. All examples are to be run from the client side. **Port 5555 is being used.** We add the option to plot signals. Examples should be self-explanatory.

**usrp_p2p_transmission**: Sends random signal from Usrp1 to Usrp2, check file.

Usage:

```bash
$ cd <repo>
$ . env/bin/activate
$ python examples/usrp_p2p_transmission.py --usrp1-ip <ip> --usrp2-ip <ip> --carrier-frequency <carrier-frequency> --plot
```

**jcas**: Implements the JCAS scenario, but using a random signal instead.
Usage:

```bash
$ cd <repo>
$ . env/bin/activate
$ python examples/jcas.py --usrp1-ip <ip> --usrp2-ip <ip> --carrier-frequency <carrier-frequency> --plot
```

Sends a random signal from USRP1 to USRP2, while receiving at USRP1 as well. If `--plot` argument is omitted, the signal will be sent/received 10 times a row.



## hardware_tests

We have some hardware tests, for testing/debugging purposes mainly. **However, we hve one test with transmits a chirp localhost**. This code is to be run on the USRP directly and uses the python binding of the UHD wrapper. Call on the usrp:

```bash
$ cd <repo>
$ . env/bin/activate
$ cd uhd_wrapper
$ python hardware_tests/transmit_chirp_localhost.py --bandwidth <bandwidth> --carrier-frequency <carrier-frequency>
```

`bandwidth` denotes the bandwidth of the chirp, starting at `f0 = bandwidth/2` until `f1 = bandwidth/2`.

**Note**: The Usrp should be stopped for this purpose!


# For Developers

In the `snippets` directory, snippets can be found. As the testing capabilities for the hardware are strongly limited, the snippets are meant for evaluating the hardware. Feel free to play around with it!

We also have a **debug** folder that contains some files to be used for debugging:

- tx_stream: streams white noise (mean 0, std 2) that may be analysed with the specci. **note**: undeflow occurs, i.e. samples are not buffered fast enough into the fpga. No clue how this can be fixed. however, we hope that the results are still valid...

## Start usrp server

