from typing import Any

import tkinter

from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.backend_bases import key_press_handler
from matplotlib.figure import Figure

import numpy as np

from usrp_client import System, MimoSignal, TxStreamingConfig, RxStreamingConfig, RfConfig

usrpSystem = System()
rfConfig = RfConfig()
rfConfig.rxAnalogFilterBw = 400e6
rfConfig.txAnalogFilterBw = 400e6
rfConfig.txSamplingRate = 245.76e6
rfConfig.rxSamplingRate = 245.76e6
rfConfig.txGain = 50
rfConfig.rxGain = 50
rfConfig.txCarrierFrequency = 8e9
rfConfig.rxCarrierFrequency = 8e9
rfConfig.noRxStreams = 1
rfConfig.noTxStreams = 1

device = usrpSystem.newUsrp(ip="192.168.189.133", usrpName="usrp1")
device.configureRfConfig(rfConfig)

root = tkinter.Tk()
root.wm_title("Embedding in Tk")

fig = Figure(figsize=(5, 4), dpi=100)
t = np.linspace(0, 1, 10000)
txSignal = (0.5*np.sin(50*np.pi*t)).astype(complex)
line = fig.add_subplot(111).plot(t, np.array([txSignal.real, txSignal.imag]).T)

canvas = FigureCanvasTkAgg(fig, master=root)  # A tk.DrawingArea.
canvas.draw()
canvas.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)

toolbar = NavigationToolbar2Tk(canvas, root)
toolbar.update()
canvas.get_tk_widget().pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)


def on_key_press(event: Any) -> None:
    print("you pressed {}".format(event.key))
    key_press_handler(event, canvas, toolbar)

    if event.key == 'q':
        _quit()


canvas.mpl_connect("key_press_event", on_key_press)


def _quit() -> None:
    root.quit()     # stops mainloop

    # this is necessary on Windows to prevent
    # Fatal Python Error: PyEval_RestoreThread: NULL tstate
    root.destroy()


def _transmit() -> None:
    usrpSystem.configureTx("usrp1", TxStreamingConfig(sendTimeOffset=0,
                                                      samples=MimoSignal(signals=[txSignal])))

    usrpSystem.configureRx("usrp1", RxStreamingConfig(receiveTimeOffset=0,
                                                      numSamples=len(t)))
    usrpSystem.execute()
    rx = usrpSystem.collect()

    line[0].set_data(t, rx["usrp1"][0].signals[0].real)
    line[1].set_data(t, rx["usrp1"][0].signals[0].imag)
    canvas.draw()


button1 = tkinter.Button(master=root, text="Quit", command=_quit)
button1.pack(side=tkinter.BOTTOM)

button2 = tkinter.Button(master=root, text="Transmit", command=_transmit)
button2.pack(side=tkinter.BOTTOM)

tkinter.mainloop()
