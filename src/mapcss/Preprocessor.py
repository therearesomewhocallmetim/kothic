from __future__ import print_function
from os.path import exists
import logging
import re
import logging_config # Used to configure logging, you don't have to call anything from it.
from os.path import dirname, realpath, join

IMPORT = re.compile(r'^\s*?@import\s*?\(\s*?\"(.*?)\"\s*?\)\s*?;', re.DOTALL | re.MULTILINE)
COMMENT = re.compile(r'/\*.*?\*/', re.DOTALL)
VARIABLE = re.compile(r'^\s*(@(?!import).*?)\s*?:\s*?(.*?);', re.DOTALL | re.MULTILINE)
BLOCK = re.compile(r'^\s*([^@{]*\{.*?\})', re.DOTALL | re.MULTILINE)


class Preprocessor:

    def __init__(self, filepath):
        self.blocks = []
        self.variables = {}
        self.text = ""
        self.base_folder = ""
        self.blocks = []
        self.filepath = realpath(filepath)
        self.base_folder = realpath(dirname(filepath))


    def clean(self):
        self.text = COMMENT.sub("", self.text)
        self.text = IMPORT.sub("", self.text)
        self.text = VARIABLE.sub("", self.text)
        self.text = BLOCK.sub("", self.text)
        self.text = re.sub("\s*", "", self.text)


    def process(self):
        self.readfile()

        self.text = COMMENT.sub("", self.text)
        self.process_variables()
        self.process_imports()
        self.process_blocks()

        self.clean()
        if self.text:
            logging.warning("Some text in the mapcss file couldn't be parsed:\n{}\n{}".format(self.filepath, self.text))


    def process_blocks(self):
        blocks = BLOCK.findall(self.text)
        for b in blocks:
            self.blocks.append(re.sub("\s+", " ", b))


    def _print_vars(self):
        for var in self.variables:
            print("~{} : {} ({})".format(var, self.variables[var][0], self.variables[var][1]))
        print("Finished vars")

    def process_variables(self):
        variables = VARIABLE.findall(self.text)
        for var in variables:
            self.variables[var[0].strip()] = (var[1].strip(), self.filepath)


    def process_imports(self):
        imports = IMPORT.findall(self.text)
        for imp in imports:
            preprocessor = Preprocessor(realpath(join(self.base_folder, imp)))
            preprocessor.process()
            self.blocks.extend(preprocessor.blocks)
            self.merge_variables(preprocessor.variables)


    def merge_variables(self, other_variables):
        for key in other_variables:
            if key in self.variables:
                logging.warning("Variable redeclaration, setting the new value: \n{}\nold: {}\nnew: {}\nFirst declared in {}\nRedeclared in {}"
                                .format(key, self.variables[key][0], other_variables[key][0], self.variables[key][1], other_variables[key][1]))
            first_declared = other_variables[key][1] if key not in self.variables else self.variables[key][1]
            self.variables[key] = (other_variables[key][0], first_declared)


    def substitute_variables(self):
        substituted_blocks = []

        for block in self.blocks:
            for var in self.variables:
                block = block.replace(var, self.variables[var][0])
            substituted_blocks.append(block)
            if "@" in block:
                logging.warning("Unbound variable found in block {}".format(block))

        self.blocks = substituted_blocks


    def readfile(self):
        if not exists(self.filepath):
            logging.error("The file {file} doesn't exist!".format(file=self.filepath))
            exit(1)

        with open(self.filepath) as f:
            self.text = f.read()



BLOCK_SPLITTER = re.compile(r'([^@{]*)\s*\{(.*?)\}', re.DOTALL | re.MULTILINE)

class BlockSplitter:

    def __init__(self, preprocessed_blocks):
        self.blocks = preprocessed_blocks
        self.split_blocks = {} # selector : list of attributes

    def clean_split_by(self, string, separator):
        return filter(lambda x: x != "", map(lambda x: x.strip(), string.split(separator)))

    def split_commas(self):

        comma_split_blocs = {}
        for block in self.blocks:
            found = BLOCK_SPLITTER.findall(block)
            for entry in found:
                keys = self.clean_split_by(entry[0], ",")
                attributes = self.clean_split_by(entry[1], ";")
                for key in keys:
                    if key in comma_split_blocs:
                        comma_split_blocs[key].extend(attributes)
                    else:
                        comma_split_blocs[key] = attributes


        print(comma_split_blocs)

        pass





if __name__ == "__main__":
    prep = Preprocessor("../../testdata/clear/style-clear/test.mapcss")
    prep.process()
    prep.substitute_variables()

    block_splitter = BlockSplitter(prep.blocks)
    block_splitter.split_commas()




