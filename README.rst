netmem
======
Basic memory synchronization across the network in Python

This package has a network-synchronized dictionary that runs
on ```asyncio``` event loops.  It supports binding to the
dictionary similar to ```tk.Variable()``` and is also compatible
with ```tkinter``` and its event loops.

Example
-------

Here is the smallest meaningful example I can come up with.
Run it on two different computers on the same network.

::

    import tkinter as tk
    import netmem

    def main():
        print("Run this on two different computers.")
        mem = netmem.NetworkMemory()
        mem.connect_on_new_thread(netmem.UdpConnector(local_addr=("225.0.0.1", 9991)))

        tk1 = tk.Tk()
        lbl = tk.Label(tk1, text="Favorite operating system:")
        lbl.pack()
        txt = tk.Entry(tk1, textvariable=mem.tk_var("fav_os"))
        txt.pack()

        tk1.mainloop()


    if __name__ == "__main__":
        main()

