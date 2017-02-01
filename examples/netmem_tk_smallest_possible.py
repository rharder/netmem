#!/usr/bin/env python3
""" An example using tkinter and UDP connections. """

import sys
import tkinter as tk

sys.path.append("..")  # because "examples" directory is sibling to the package
import netmem

__author__ = "Robert Harder"
__email__ = "rob@iharder.net"
__date__ = "31 Jan 2017"
__license__ = "Public Domain"


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
