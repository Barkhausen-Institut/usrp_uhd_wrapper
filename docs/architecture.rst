Software Architecture
=====================

.. image:: software_architecture.png

On the laptop (henceforth called "client"), signal processing is performed using python.
Via API calls, configurations are passed to the :py:class:`Usrp Client <usrp_client.rpc_client.UsrpClient>`.

Under the hood, the Usrp client uses a RPC client for performing remote procedure calls.
We use `ZeroRpc <https://github.com/0rpc/zerorpc-python>`_ that uses `ZeroMQ <https://zeromq.org/>`_ 
as a communication protocol. This communication protocol is widely used for high-throughput
systems.

On the USRP, we run the :py:mod:`RPC server <uhd_wrapper.rpc_server>` which is managed
by the :py:class:`USRP server <uhd_wrapper.rpc_server.UsrpServer>`.
In order perform the actual calls against the USRP device, we wrapped the `UH driver <https://github.com/EttusResearch/uhd>`_.
To ease the integration into the server, we created a python binding.

In the picture above, third party modules are depicted by grey boxes, whereas custom code is
highlighted with blue boxes.