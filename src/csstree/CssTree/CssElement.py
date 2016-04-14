from __future__ import print_function

import logging
import logging.config


class CssElement:
    def __init__(self, tag, zoom, selectors, subclass):
        self.tag = tag
        self.zoom = zoom
        self.selectors = selectors #[]
        self.subclass = subclass

    def __repr__(self):
        return "{}|z{}::{}".format(self.tag, self.zoom, self.subclass)