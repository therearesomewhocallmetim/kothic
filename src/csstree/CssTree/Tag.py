@DeprecationWarning
class Tag:
    def __init__(self, tag, zoom, selectors=[], subclass=None):
        self.tag = tag
        self.selectors = selectors
        self.subclass = subclass
        self.zoom = zoom

    def __repr__(self):
        str_selectors = "".join(map(lambda x: "[{}]".format(x), self.selectors)) if self.selectors else ""
        str_subclass = "::{}".format(self.subclass) if self.subclass else ""
        return "{}|z{}{}{}".format(self.tag, self.zoom, str_selectors, str_subclass)
