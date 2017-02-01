netmem
======


.. image:: https://img.shields.io/travis/rharder/netmem.svg?style=flat-square
    :target: https://travis-ci.org/rharder/netmem
    
Basic memory synchronization across the network in Python

This package has a network-synchronized dictionary that runs
on ``asyncio`` event loops.  It supports binding to the
dictionary similar to ``tk.Variable()`` and is also compatible
with ``tkinter`` and its event loops.

Data Structure
--------------

``NetworkMemory`` subclasses a Python dictionary, so you can access the
data within it as you do any dictionary object.  Additionally you can
bind listeners to NetworkMemory (because in fact it subclasses a
bindable dictionary, which is something I borrowed from other code
I wrote).


Examples
--------

Here is the smallest meaningful example I can come up with.
Run it on two different computers on the same network. ::

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

You can bind a listener to the ``NetworkMemory`` object to be notified when 
a value changes, such as when an update arrives over the network.  The listener
works like the following code snippet. ::

    def memory_changed(netmem_dict, key, old_val, new_val)
        print("Update  {}:{}".format(key, new_val))

    def main():
        mem = netmem.NetworkMemory()
        mem.add_listener(memory_changed)
        mem["foo"] = "bar"

The output from this would be the following ::

    Update foo:bar

Incidentally the underlying ``BindableDict`` class is pretty handy on its own, 
without even the network synchronizing capabilities.

