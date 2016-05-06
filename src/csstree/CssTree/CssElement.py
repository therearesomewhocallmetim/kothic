WILDCARD = "*"

class CssElement:
    def __init__(self, tag, zoom, selectors, subclass):
        self.tag = tag
        self.zoom = zoom
        self.selectors = selectors #[]
        self.subclass = subclass


    def __repr__(self):
        return self._my_str_repr()


    def _my_str_repr(self, must_sort=False):
        selectors = self.selectors
        if must_sort:
            selectors = sorted(selectors)

        str_selectors = "".join(selectors) if selectors else ""
        str_subclass = "::{}".format(self.subclass) if self.subclass else ""
        return "{}|z{}{}{}".format(self.tag, self.zoom, str_selectors, str_subclass)


    def __eq__(self, other):
        return (isinstance(other, self.__class__)
                    and self.__dict__ == other.__dict__)


    def __ne__(self, other):
        return not self.__eq__(other)


    def __hash__(self):
        return hash(self._my_str_repr(must_sort=True))


    def can_adopt(self, css_element):
        if self.zoom != css_element.zoom:
            return False
        #my tag must be * or the same as theirs, my subclass must be * or the same as theirs, and my selectors must count less than theirs and be a subset of theirs.
        if self.tag != WILDCARD and self.tag != css_element.tag:
            return False
        if self.subclass != WILDCARD and self.subclass != css_element.subclass:
            return False
        if len(self.selectors) >= len(css_element.selectors):
            return False
        if not set(self.selectors).issubset(css_element.selectors):
            return False

        return True





if __name__ == "__main__":
    e1 = CssElement("line", 14, ["[piste:type=downhill]", "[piste:difficulty=intermediate]"], "")
    e2 = CssElement("line", 14, ["[piste:type=downhill]"], "")

    print(e1.can_adopt(e1))
    print(e1.can_adopt(e2))
    print(e2.can_adopt(e1))
            # class CssBlock:
#     def __init__(self, element, styles):
#         self.element = element
#         self.styles = styles
