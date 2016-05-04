from __future__ import print_function

import logging
from CssElement import CssElement
# from CssElement import CssBlock



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

    def add_all(self, blocks):

        for block in blocks:
            pass


    def add(self, node):
        if node.element.tag not in self.branches_by_tag:
            self.branches_by_tag[node.element.tag] = node
            return True

        if node.can_adopt(self.branches_by_tag[node.element.tag]):
            node.add(self.branches_by_tag[node.element.tag])
            self.branches_by_tag[node.element.tag] = node
            return True

        return self.branches_by_tag[node.element.tag].add(node)

    def __repr__(self):
        ret = []
        for tag in self.branches_by_tag:
            ret.append(str(self.branches_by_tag[tag]))
        return "\n".join(ret)




class CssNode:
    def __init__(self, element, styles):
        self.children = [] #list of nodes
        self.element = element #CssElement
        self.parent = None #if parent is none, i am root.
        self.styles = styles # must be StringWithSource
        pass

    def can_adopt(self, node):
        # or self.element.subclass != node.element.subclass \
        if self.element.tag != node.element.tag and self.element.tag != "*" \
                or self.element.zoom != node.element.zoom \
                or len(self.element.selectors) >= len(node.element.selectors):
            return False

        for i, sel in enumerate(self.element.selectors):
            if sel != node.element.selectors[i]:
                return False

        return True
        pass

    def add(self, node):
        if self.can_adopt(node):
            if not self.children: #self has no children,
                self.children.append(node)
                return True
            else:
                for child in self.children:
                    if child.can_adopt(node):
                        return child.add(node) # self has children, and one of the children can adopt the new node

                # none of the children could adopt the node, maybe the node can adopt the children (or some of them)
                possible_children_for_the_node = []
                for child in self.children:
                    if node.can_adopt(child):
                        possible_children_for_the_node.append(child)

                if possible_children_for_the_node: #if there are children that can be adopted by the node
                    for child in possible_children_for_the_node:
                        self.children.remove(child)
                        node.add(child)
                    self.children.append(node)
                    return True

        return False


    def __repr__(self):
        children_repr = "".join(map(lambda x: str(x), self.children))
        return "{}{}\n{}".format("  ", self.element, children_repr)

if __name__ == "__main__":
    node1 = CssNode(CssElement("tag", "10", ["a", "b", "c"], None), [])
    node2 = CssNode(CssElement("tag", "10", ["a", "b", "c", "d"], None), [])
    node3 = CssNode(CssElement("*", "10", ["a", "b", "c", "d"], None), [])

    css_subtree = CssSubtree()
    print(css_subtree.add(node2))
    print(css_subtree.add(node1))
    print(css_subtree.add(node3))

    print(css_subtree)

    # print(node1.can_adopt(node2))