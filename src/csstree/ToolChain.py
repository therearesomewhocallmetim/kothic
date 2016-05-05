from __future__ import print_function
from Preprocessor import Preprocessor
from BlockSplitter import BlockSplitter
from BlockSplitter import Block
from CssTree import CssTree
from CssTree import CssNode

if __name__ == "__main__":

    print("Toolchain")

    prep = Preprocessor("../../testdata/clear/style-clear/test.mapcss", write_to_file=True)
    prep.process()
    print("Toolchain, num blocks: {}".format(len(prep.blocks)))
    # prep.substitute_variables()



    block_splitter = BlockSplitter(prep.blocks, write_to_file=True)
    block_splitter.process()

    css_tree = CssTree()
    for zoom in block_splitter.blocks_by_zoom_level:
        for block in block_splitter.blocks_by_zoom_level[zoom]:
            css_node = CssNode(block, block_splitter.blocks_by_zoom_level[zoom][block])
            css_tree.add(css_node)





    # for zoom in block_splitter.blocks_by_zoom_level:
    #     print("Zoom {}".format(zoom))
    #     selectors = map(lambda x: x.selectors, block_splitter.blocks_by_zoom_level[zoom])
    #     selectors = sorted(selectors, key=len)
    #     # for block in block_splitter.blocks_by_zoom_level[zoom]:
    #         # selectors = sorted(block.selectors, key = lambda x: len(x))
    #     for selector in selectors:
    #         print("> {}".format(selector))

    print("hello")