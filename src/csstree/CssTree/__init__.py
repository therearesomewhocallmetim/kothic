from __future__ import print_function

import logging
import CssElement




class CssTree:
    def __init__(self, min_zoom=1, max_zoom=19):
        self.subtrees_by_zoom = {}
        for i in range(min_zoom, max_zoom + 1):
            self.subtrees_by_zoom[i] = CssSubtree()

        pass

    def add(self, csselement):
        self.subtrees_by_zoom[csselement.zoom].add(csselement)
        a = CssElement("a", "b", "c", "d")




class CssSubtree:
    def __init__(self):
        self.branches_by_tag = {}
        pass

    def add(self, csselement):
        pass


class CssNode:
    def __init__(self):
        pass