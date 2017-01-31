#!/usr/bin/env python3
"""
Represents a variable that can bind listeners to changes in its state,
similar to the tkinter.StringVar, IntVar, etc classes.

This is an extract from the code available at http://github.com/rharder/handy
"""

import logging

__author__ = "Robert Harder"
__email__ = "rob@iharder.net"
__date__ = "5 Dec 2016"
__license__ = "Public Domain"


class BindableDict(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.log = logging.getLogger(__name__ + '.' + self.__class__.__name__)
        self.__listeners = []
        self._changes = []
        self._suspend_notifications = False

    def __getitem__(self, key):
        val = super().__getitem__(key)
        return val

    def __setitem__(self, key, new_val):
        self.set(key, new_val)

    def set(self, key, new_val, force_notify=False):
        old_val = self.get(key)
        super().__setitem__(key, new_val)
        if old_val != new_val or force_notify:
            self._changes.append((key, old_val, new_val))
            self._notify_listeners()

    def mark_changed(self, key):
        """
        Triggers notification to listeners for a certain key, regardless of
        any change to the key.  The listeners will get their callback with
        both old_val and new_val being the same.

        Can be handy if the key's value is an object with internal changes,
        such as an array or another dictionary.

        :param key: the key to alert listeners to
        """
        val = self.get(key)
        self._changes.append((key, val, val))
        self._notify_listeners()

    def __repr__(self):
        dictrepr = super().__repr__()
        return "{}({})".format(type(self).__name__, dictrepr)

    def __str__(self):
        return super().__repr__()

    def update(self, *args, **kwargs):
        with self:
            for k, v in dict(*args, **kwargs).items():
                self[k] = v

    def add_listener(self, listener):
        """
        Registers listener as a callable object (a function or lambda generally) that will be
        notified when the value of this variable changes.

        The options value_only and no_args are mutually exclusive.  If both are set
        to True, then it is unspecified which form of notification will occur: one
        argument or no arguments.

        The listener will be called with four arguments and should have a signature like this:

            def memory_changed(netmem_dict, key, old_val, new_val):
                ...

        :param listener: the listener to notify
        :param bool value_only: listener will be notified with only one argument, the new value
        :param bool no_args: listener will be notified with no arguments
        """
        self.__listeners.append(listener)

    def remove_listener(self, listener):
        """
        Removes listener from the list of callable objects that are notified when the value changes

        :param listener: the listener to remove
        """
        if listener in self.__listeners:
            self.__listeners.remove(listener)

    def remove_all_listeners(self):
        """
        Removes all listeners that are registered to be notified when the value changes.
        """
        self.__listeners.clear()

    def _notify_listeners(self):
        """
        Internal method to notify the list of listeners.
        """

        if not self._suspend_notifications:
            changes = self._changes.copy()
            self._changes.clear()
            for listener in self.__listeners:
                for key, old_val, new_val in changes:
                    listener(self, key, old_val, new_val)

    def __enter__(self):
        """ For use with Python's "with" construct. """
        self._suspend_notifications = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """ For use with Python's "with" construct. """
        self._suspend_notifications = False
        self._notify_listeners()

    def tk_var(self, key):
        """ Returns a tk.Var object that is two-way bound to a particular key in this dictionary. """
        import tkinter as tk
        tkvar = tk.Variable()
        tkvar.trace("w", lambda _, __, ___, v=tkvar: self.set(key, tkvar.get()))

        def _listener(bdict, changed_key, old_val, new_val):
            if changed_key == key:
                tkvar.set(new_val)

        self.add_listener(_listener)
        return tkvar
