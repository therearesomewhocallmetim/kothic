from __future__ import print_function
from Preprocessor import Preprocessor
from BlockSplitter import BlockSplitter


if __name__ == "__main__":

    print("Toolchain")

    prep = Preprocessor("../../testdata/clear/style-clear/test.mapcss", write_to_file=True)
    prep.process()
    print("Toolchain, num blocks: {}".format(len(prep.blocks)))
    # prep.substitute_variables()



    block_splitter = BlockSplitter(prep.blocks, write_to_file=True)
    block_splitter.process()
