#!/usr/bin/env python

import curses
import logging
l = logging.getLogger('memcurses.memcurses')
l.setLevel('DEBUG')

from .mem import Mem

class MemCurses(object):
    def __init__(self, screen, pid=None):
        self._mem = Mem(pid=pid)
        self._screen = screen

        l.info("MemCurses initialized. Screen is %dx%d", self.height, self.width)
        self._maps = self._mem.maps
        self.views = [ MemViewSelect(self, "Region Selection", [ str(m) for m in self._maps ], self._create_hex_view) ]

        self._screen.nodelay(True)
        self._screen.keypad(True)

    def _create_hex_view(self, selector, line, idx): #pylint:disable=unused-argument
        self._screen.clear()
        self.views.append(MemViewHex(self, self._maps[idx]))

    @property
    def height(self):
        return self._screen.getmaxyx()[0]

    @property
    def width(self):
        return self._screen.getmaxyx()[1]

    def draw(self):
        #self._screen.erase()
        l.debug("Drawing %d views", len(self.views))
        for v in self.views:
            v.draw()
        curses.doupdate()

    def input(self):
        v = None

        l.debug("memcurses input")
        c = self._screen.getch()
        if c == ord('q'):
            l.debug("... quitting")
            return False
        elif c == ord('X'):
            l.debug("... closing %r", self.views[-1])
            self.views[-1].close()
            self._screen.clear()
        elif c == curses.KEY_RESIZE:
            l.debug("... window resized")
            self._screen.clear()
        elif c == curses.KEY_F2:
            self._screen.clear()
            self.views.append(MemViewDebug(self))
        else:
            l.debug("... ungetting %r", c)
            curses.ungetch(c)

        for v in reversed(self.views):
            l.debug("Input to %r", v)
            r = v.input()
            if r is None:
                l.debug("... it handled it")
                break
            elif isinstance(r, MemView):
                l.debug("... it created %r", r)
                self.views.append(r)
                self._screen.clear()
                break

        return True

    def cleanup(self):
        new_views = [ v for v in self.views if not v._closed ]
        #closed_views = [ v for v in self.views if v._closed ]
        #for v in closed_views:
        #   v._window.clear()
        if len(new_views) != len(self.views):
            self._screen.clear()

        self.views = new_views

    def interact(self):
        while True:
            if len(self.views) == 0:
                return

            # update the memory map
            self._maps = self._mem.maps

            if not self.input():
                return
            self.cleanup()
            self.draw()

from .memview import MemView
from .views import MemViewSelect, MemViewHex, MemViewDebug
