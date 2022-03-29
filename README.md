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

Launch the `usrp_snippet` file. It creates a Usrp and is meant for testing purposes. 
