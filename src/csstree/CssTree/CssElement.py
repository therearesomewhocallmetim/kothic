class CssElement:
    def __init__(self, tag, zoom, selectors, subclass):
        self.tag = tag
        self.zoom = zoom
        self.selectors = selectors #[]
        self.subclass = subclass

    def __repr__(self):
        str_selectors = "".join(self.selectors) if self.selectors else ""
        str_subclass = "::{}".format(self.subclass) if self.subclass else ""
        return "{}|z{}{}{}".format(self.tag, self.zoom, str_selectors, str_subclass)

