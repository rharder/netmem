#!/usr/bin/env python3
""" An example using tkinter and UDP connections. """

import logging
import sys
import tkinter as tk

from tkinter_tools import BindableTextArea

sys.path.append("..")  # because "examples" directory is sibling to the package
import netmem

__author__ = "Robert Harder"
__email__ = "rob@iharder.net"
__date__ = "31 Jan 2017"
__license__ = "Public Domain"


# During development:
# logging.basicConfig(level=logging.ERROR)
# logging.getLogger(__name__).setLevel(logging.INFO)
# logging.getLogger("netmem").setLevel(logging.INFO)


class NetMemApp():
    def __init__(self, root, connector):
        self.window = root
        root.title("NetMem {}".format(str(connector)))
        self.log = logging.getLogger(__name__)

        # Data
        self.netmem = netmem.NetworkMemory()
        self.key_var = tk.StringVar()
        self.val_var = tk.StringVar()
        self.data_var = tk.StringVar()

        # View / Control
        self.create_widgets()

        # Connections
        self.netmem.add_listener(self.memory_updated)
        self.netmem.connect_on_new_thread(connector)

        self.key_var.set("pet")
        self.val_var.set("cat")

    def create_widgets(self):
        lbl_key = tk.Label(self.window, text="Key:")
        lbl_key.grid(row=0, column=0, sticky=tk.E)
        txt_key = tk.Entry(self.window, textvariable=self.key_var)
        txt_key.grid(row=0, column=1, sticky=tk.W + tk.E)
        txt_key.bind('<Return>', lambda x: self.update_button_clicked())

        lbl_val = tk.Label(self.window, text="Value:")
        lbl_val.grid(row=1, column=0, sticky=tk.E)
        txt_val = tk.Entry(self.window, textvariable=self.val_var)
        txt_val.grid(row=1, column=1, sticky=tk.W + tk.E)
        txt_val.bind('<Return>', lambda x: self.update_button_clicked())

        lbl_score = tk.Label(self.window, text="Also demonstrate binding a tk.Var to key 'score':")
        lbl_score.grid(row=3, column=0, sticky=tk.E)
        txt_score = tk.Entry(self.window, textvariable=self.netmem.tk_var("score"))
        txt_score.grid(row=3, column=1, sticky=tk.W + tk.E)

        btn_update = tk.Button(self.window, text="Update key/value pair", command=self.update_button_clicked)
        btn_update.grid(row=2, column=0, columnspan=2)

        self.txt_data = BindableTextArea(self.window, textvariable=self.data_var, width=30, height=5)
        self.txt_data.grid(row=4, column=0, columnspan=2)

    def update_button_clicked(self):
        key = self.key_var.get()
        val = self.val_var.get()
        self.log.info("Button clicked. Key: {}, Value: {}".format(key, val))
        if key == "exit":
            print("exit: CLOSING ALL CONNECTORS")
            self.netmem.close_all()
        else:
            self.netmem.set(key, val)

    def memory_updated(self, netmem_dict: netmem.NetworkMemory, key, old_val, new_val):
        self.data_var.set(str(netmem_dict))


def main():
    tk1 = tk.Tk()
    program1 = NetMemApp(tk1, netmem.UdpConnector(local_addr=("225.0.0.1", 9991),
                                                  remote_addr=("225.0.0.2", 9992)))

    tk2 = tk.Toplevel()
    program2 = NetMemApp(tk2, netmem.UdpConnector(local_addr=("225.0.0.2", 9992),
                                                  remote_addr=("225.0.0.1", 9991)))

    tk1.mainloop()


if __name__ == "__main__":
    main()
