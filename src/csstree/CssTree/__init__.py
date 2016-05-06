from __future__ import print_function
import logging
from CssElement import CssElement

WILDCARD = "*"
TAGS = ["node", "line", "way", "area"]


class CssTree:
    def __init__(self, min_zoom=1, max_zoom=19):
        self.root_nodes_by_zoom = {}
        for i in range(min_zoom, max_zoom + 1):
            self.root_nodes_by_zoom[i] = CssNode(None, None, root=True)


    def add(self, node):
        self.root_nodes_by_zoom[node.element.zoom].add(node)


    def finilize_tree(self):
        for tag in TAGS:
            for zoom, subtree in self.root_nodes_by_zoom.iteritems():
                subtree.add(CssNode(CssElement(tag, zoom, [], None), []))
        self.trickle_down_styles()


    def trickle_down_styles(self):
        for zoom, subtree in self.root_nodes_by_zoom.iteritems():
            subtree.trickle_down_styles()


    def write(self):
        with open("../../out/inflated.mapcss", "w") as out_file:
            for zoom, subtree in self.root_nodes_by_zoom.iteritems():
                out_file.write("   /* === ZOOM {} === */\n\n".format(zoom))
                subtree.write(out_file)


class CssNode:
    def __init__(self, element, styles, root=False):
        self.children = []
        self.element = element
        self.styles = styles # {<str>: <StringWithSource>}
        self.parent = None
        self.am_root = root


    def write(self, out_file):
        if not self.is_root():
            out_file.write("{} {{\n".format(self.element))
            if self.styles:
                for attr, val in self.styles.iteritems():
                    # out_file.write("    {}: {}; /* {} */\n".format(attr, val.string, val.source)) #our old Kothic doesn't like comments on the same line as an attribute
                    out_file.write("    {}: {};\n".format(attr, val.string))
            out_file.write("}\n\n")

        for child in self.children:
            child.write(out_file)


    def is_root(self):
        return self.am_root


    def can_adopt(self, node):
        if self.is_root():
            return True
        return self.element.can_adopt(node.element)


    def add(self, node):
        if not self.can_adopt(node):
            return False

        if not self.children: #self has no children,
            self.children.append(node)
            node.parent = self
            return True
        else:
            for child in self.children:
                if child.can_adopt(node):
                    return child.add(node) # self has children, and one of the children can adopt the new node

            # none of the children could adopt the new node, maybe the node can adopt the children (or some of them)
            possible_children_for_the_node = []
            for child in self.children:
                if node.can_adopt(child):
                    possible_children_for_the_node.append(child)

            if possible_children_for_the_node: #if there are children that can be adopted by the node
                for child in possible_children_for_the_node:
                    self.children.remove(child)
                    node.add(child)
                    child.parent = node
            self.children.append(node)
            node.parent = self
            return True


    def trickle_down_styles(self):
        for child in self.children:
            child.inherit_styles(self.styles)
            child.trickle_down_styles()


    def inherit_styles(self, styles):
        if not styles:
            return
        for attr, value in styles.iteritems():
            if attr in self.styles:
                logging.info("Rewriting a value from a higher element, {}: {} -> {}".format(attr, value.string, self.styles[attr].string))
                continue
            self.styles[attr] = value


    def __repr__(self):
        # children_repr = "".join(map(lambda x: str(x), self.children))
        return str(self.element)

if __name__ == "__main__":
    node1 = CssNode(CssElement("tag", "10", ["a", "b", "c"], None), [])
    node2 = CssNode(CssElement("tag", "10", ["a", "b", "c", "d"], None), [])
    node3 = CssNode(CssElement("*", "10", ["a", "b", "c", "d"], None), [])

# node|z19

    css_subtree = CssNode(None, None, root=True)
    print(css_subtree.add(node2))
    print(css_subtree.add(node1))
    print(css_subtree.add(node3))

    print(css_subtree)

    # print(node1.can_adopt(node2))