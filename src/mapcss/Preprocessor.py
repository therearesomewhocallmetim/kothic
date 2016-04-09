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
        self.variables = dict()
        self.text = ""
        self.base_folder = ""
        self.blocks = []
        self.filepath = realpath(filepath)
        self.base_folder = realpath(dirname(filepath))

    def process(self):
        self.readfile()

        self.text = COMMENT.sub("", self.text)
        self.process_variables()
        self.process_imports()
        # self._print_vars()

        self.process_blocks()

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
                logging.warning("Variable redeclaration, setting the new value: \n{}\nold: {}\nnew: {}\nFirst declared in {}".format(key, self.variables[key][0], other_variables[key][0], self.variables[key][1]))
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




if __name__ == "__main__":
    prep = Preprocessor("../../testdata/clear/style-clear/test.mapcss")

    prep.process()
    prep.substitute_variables()




