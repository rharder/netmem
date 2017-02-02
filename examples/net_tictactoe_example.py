#!/usr/bin/env python3
""" A network tic tac toe example. """

import logging
import sys
import tkinter as tk
from functools import partial

sys.path.append("..")  # because "examples" directory is sibling to the package
import netmem

__author__ = "Robert Harder"
__email__ = "rob@iharder.net"
__date__ = "31 Jan 2017"
__license__ = "Public Domain"


class TicTacToeApp:
    # Keys
    PLAYER_NAME = [None, "player1_name", "player2_name"]  # value type: string
    CURRENT_PLAYER_NUM = "curr_player_num"  # value type: int
    GAME_BOARD = "game_board"  # value type: 3x3 2D array of ints (0,1,2)
    MARKERS = [" ", "X", "O"]

    def __init__(self, root, connector):
        self.window = root
        root.title("TicTacToe {}".format(str(connector)))
        self.log = logging.getLogger(__name__)

        # Data
        self.netmem = netmem.NetworkMemory()
        self._grid_vars = [[tk.StringVar() for _ in range(3)] for _ in range(3)]

        # View
        self._grid = None  # type: [[tk.Button]
        self.create_widgets()

        # Initial Values
        self.netmem[self.GAME_BOARD] = [[" " for _ in range(3)] for _ in range(3)]
        self.netmem[self.CURRENT_PLAYER_NUM] = 1

        # Connections
        self.netmem.connect_on_new_thread(connector)
        self.netmem.add_listener(self.netmem_changed)

    def create_widgets(self):
        # Player names
        row = 0
        for i in range(2):
            lbl = tk.Label(self.window, text="Player {} Name:".format(i + 1))
            lbl.grid(row=row, column=0)
            txt = tk.Entry(self.window, textvariable=self.netmem.tk_var(self.PLAYER_NAME[i + 1]))
            txt.grid(row=row, column=1)
            row += 1

        # Current Player Number
        lbl = tk.Label(self.window, text="Current Player:")
        lbl.grid(row=row, column=0)
        lbl = tk.Label(self.window, textvariable=self.netmem.tk_var(self.CURRENT_PLAYER_NUM))
        lbl.grid(row=row, column=1, sticky=tk.W)
        row += 1

        # Grid
        gridframe = tk.Frame(self.window)
        gridframe.grid(row=row, column=0, columnspan=2, sticky="nsew")
        self._grid = [[None for _ in range(3)] for _ in range(3)]
        for x in range(3):
            for y in range(3):
                self._grid[x][y] = tk.Button(gridframe, textvariable=self._grid_vars[x][y],
                                             command=partial(self.grid_button_clicked, x, y))
                self._grid[x][y].grid(row=y, column=x, sticky="nsew")
        row +=1

    def grid_button_clicked(self, x, y):
        print("grid_button_clicked x={}, y={}".format(x,y))
        curr_ply_num = self.netmem[self.CURRENT_PLAYER_NUM]
        marker = self.MARKERS[curr_ply_num]
        self.netmem[self.GAME_BOARD][x][y] = marker
        self.netmem.mark_as_changed(self.GAME_BOARD)

    def netmem_changed(self, nm, key, old_val, new_val):
        if key == self.GAME_BOARD:
            for x in range(3):
                for y in range(3):
                    marker = nm[self.GAME_BOARD][x][y]
                    self._grid_vars[x][y].set(marker)


def main():
    tk1 = tk.Tk()
    program1 = TicTacToeApp(tk1, netmem.UdpConnector(local_addr=("225.0.0.1", 9991),
                                                     remote_addr=("225.0.0.2", 9992)))

    tk2 = tk.Toplevel()
    program2 = TicTacToeApp(tk2, netmem.UdpConnector(local_addr=("225.0.0.2", 9992),
                                                     remote_addr=("225.0.0.1", 9991)))

    tk1.mainloop()


if __name__ == "__main__":
    main()
