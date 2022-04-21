# Purpose
 
This repo wraps the UHD for our X410. It contains the **client as well as the server**. The client is to be used by the user for signal processing purposes and sending the commands to the USRP, which serves as as server.

# Install

On the usrp:

1. `git clone <this repo>`
2. `cd usrp_uhd_rapper && mkdir build`
3. `cd build`
4. `cmake -DCMAKE_BUILD_TYPE=Release ..`
5. `make`
6. `ctest -V` to check if the tests pass

For the client:

1. Ensure that you use at least python3.9.
2. Create and activate virtual env (on linux: `python -m venv env && . env/bin/activate`)
3. `pip install -e .`
4. **For running tests:** `pip install -r requirements_tests.txt && python -m pytests tests/`

# Prerequisites

Usrp:
- libzmq

# Use

Client:

After install, there are two python packages installed: `usrp_client` serving as the client that sends commands (e.g. RF config, samples, etc.) to the usrp server. The `utils` package contains dataclasses for the configurations (module `config`, check there!) and some serialization functions in the `serialization` module. 

# For Developers

In the `snippets` directory, snippets can be found. As the testing capabilities for the hardware are strongly limited, the snippets are meant for evaluating the hardware. Feel free to play around with it!

We also have a **debug** folder that contains some files to be used for debugging:

- tx_stream: streams white noise (mean 0, std 2) that may be analysed with the specci. **note**: undeflow occurs, i.e. samples are not buffered fast enough into the fpga. No clue how this can be fixed. however, we hope that the results are still valid...