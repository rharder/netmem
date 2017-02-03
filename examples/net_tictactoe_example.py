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
__date__ = "2 Feb 2017"
__license__ = "Public Domain"


class TicTacToeApp:
    # Keys
    PLAYER_NAME = [None, "player1_name", "player2_name"]  # value type: string
    CURRENT_PLAYER_NUM = "curr_player_num"  # value type: int
    MARKERS = [None, "X", "O"]
    # Game board is defined as x:y coordinates saved as a key, eg, "0:2"

    def __init__(self, root, connector):
        self.window = root
        root.title("TicTacToe {}".format(str(connector)))
        self.log = logging.getLogger(__name__)

        # Data
        self.netmem = netmem.NetworkMemory()

        # View
        self._grid_buttons = None  # type: [[tk.Button]
        self.create_widgets()

        # Connections
        self.netmem.connect_on_new_thread(connector)
        self.netmem.add_listener(self._netmem_changed)
        self.reset_game()

    def create_widgets(self):
        # Player names text fields will be bound to their key in the NetworkMemory dictionary
        row = 0
        for i in range(2):
            lbl = tk.Label(self.window, text="Player {} Name:".format(i + 1))
            lbl.grid(row=row, column=0)
            txt = tk.Entry(self.window, textvariable=self.netmem.tk_var(self.PLAYER_NAME[i + 1]))
            txt.grid(row=row, column=1)
            row += 1

        # Current Player Number is bound to its key in the NetworkMemory dictionary
        lbl = tk.Label(self.window, text="Current Player:")
        lbl.grid(row=row, column=0)
        lbl = tk.Label(self.window, textvariable=self.netmem.tk_var(self.CURRENT_PLAYER_NUM))
        lbl.grid(row=row, column=1, sticky=tk.W)
        row += 1

        # Reset
        btn = tk.Button(self.window, text="Restart", command=self.reset_button_clicked)
        btn.grid(row=row, column=0, columnspan=2)
        row += 1

        # Grid of buttons has their marker bound to a key in the dictionary
        # using a "x:y" scheme
        gridframe = tk.Frame(self.window)
        gridframe.grid(row=row, column=0, columnspan=2, sticky="nsew")
        self._grid_buttons = [[None for _ in range(3)] for _ in range(3)]
        for x in range(3):
            for y in range(3):
                var = self.netmem.tk_var("{}:{}".format(x, y))
                self._grid_buttons[x][y] = tk.Button(gridframe, textvariable=var,
                                                     command=partial(self._grid_button_clicked, x, y))
                self._grid_buttons[x][y].grid(row=y, column=x, sticky="nsew")
        row += 1

    def reset_button_clicked(self):
        self.reset_game()

    def reset_game(self):
        with self.netmem:
            for x in range(3):
                for y in range(3):
                    self.netmem["{}:{}".format(x, y)] = " "
                    # self._grid[x][y].config("state", tk.NORMAL)
                    self._grid_buttons[x][y]["state"] = tk.NORMAL
            self.netmem[self.CURRENT_PLAYER_NUM] = 1

    def _grid_button_clicked(self, x, y):
        print("grid_button_clicked x={}, y={}".format(x, y))
        if self.netmem.get("{}:{}".format(x,y), "") not in self.MARKERS:
            curr_ply_num = self.netmem[self.CURRENT_PLAYER_NUM]
            marker = self.MARKERS[curr_ply_num]
            self.netmem["{}:{}".format(x, y)] = marker
            self.netmem[self.CURRENT_PLAYER_NUM] = (curr_ply_num % 2) + 1
            # self._grid_buttons[x][y]["state"] = tk.DISABLED
            winner = self._check_if_win()
            if winner:
                print("WINNER", winner)
                for x in range(3):
                    for y in range(3):
                        self._grid_buttons[x][y]["state"] = tk.DISABLED

    def _netmem_changed(self, nm, key, old_val, new_val):
        winner = self._check_if_win()
        if winner:
            print("WINNER", winner)
            for x in range(3):
                for y in range(3):
                    self._grid_buttons[x][y]["state"] = tk.DISABLED


    def _three_win(self, three_markers):
        marker_set = set(three_markers)
        if len(marker_set) == 1:
            marker = marker_set.pop()
            if marker in self.MARKERS:
                return marker
        return False

    def _vertical_win(self, x):
        markers = []
        for y in range(3):
            markers.append(self.netmem["{}:{}".format(x,y)])
        return self._three_win(markers)

    def _horizontal_win(self, y):
        markers = []
        for x in range(3):
            markers.append(self.netmem["{}:{}".format(x, y)])
        return self._three_win(markers)

    def _diagonal_forward_win(self):
        markers = []
        for xy in range(3):
            markers.append(self.netmem["{}:{}".format(xy, 2-xy)])
        return self._three_win(markers)

    def _diagonal_back_win(self):
        markers = []
        for xy in range(3):
            markers.append(self.netmem["{}:{}".format(xy, xy)])
        return self._three_win(markers)

    def _check_if_win(self):
        for x in range(3):
            for y in range(3):
                wins = [self._vertical_win(x), self._horizontal_win(y),
                        self._diagonal_forward_win(), self._diagonal_back_win()]
                winner = set([z for z in wins if z])
                if winner:
                    return winner
        return False

def main():
    tk1 = tk.Tk()
    program1 = TicTacToeApp(tk1, netmem.UdpConnector(local_addr=("225.0.0.1", 9991),
                                                     remote_addr=("225.0.0.2", 9992)))

    tk2 = tk.Toplevel()
    program2 = TicTacToeApp(tk2, netmem.UdpConnector(local_addr=("225.0.0.2", 9992),
                                                     remote_addr=("225.0.0.1", 9991)))

    # Hack, just to watch the memory
    ws_conn = netmem.WsServerConnector()
    program2.netmem.connect_on_new_thread(ws_conn)
    print("View memory at {}".format(ws_conn.url_html_view))

    tk1.mainloop()


if __name__ == "__main__":
    main()
