netmem
======

.. image:: https://img.shields.io/pypi/pyversions/netmem.svg
    :target: https://pypi.python.org/pypi/netmem
    :alt: Python versions supported

.. image:: https://img.shields.io/pypi/v/netmem.svg
    :target: https://pypi.python.org/pypi/netmem
    :alt: current version on PyPI

.. image:: https://img.shields.io/travis/rharder/netmem.svg?style=flat-square
    :target: https://travis-ci.org/rharder/netmem
    :alt: build status

Basic memory synchronization across the network in Python.

This package has a network-synchronized dictionary that runs
on ``asyncio`` event loops.  It supports binding to the
dictionary similar to ``tk.Variable()`` and is also compatible
with ``tkinter`` and its event loops.

Installation
------------

The easiest way is to just open your favorite terminal and type ::

    pip install netmem

Alternatively you can clone this repo and install it with ::

    python setup.py install

Requirements
------------

-  The amazing aiohttp library
-  Python v3.5+

The basis for ``netmem`` is asynchronous IO and event loops, so I
apologize to Python v2.x users and for that matter, Python v3.4.
Although Python v3.4 supports ``asyncio``, I really like
the ``async for`` and ``async with`` constructs introduced in v3.5,
and I use them in a number of places.  Since Python is already on
v3.6 at the time of this writing, I do not feel too terribly bad
leaving v3.4 behind.

Usage
-----

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


Data Structure
--------------

``NetworkMemory`` subclasses a Python dictionary, so you can access the
data within it as you do any dictionary object.  Additionally you can
bind listeners to NetworkMemory (because in fact it subclasses a
bindable dictionary, which is something I borrowed from other code
I wrote).
