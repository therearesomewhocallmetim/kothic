from __future__ import print_function
from os.path import exists
import logging
import re
import logging_config # Used to configure logging, you don't have to call anything from it.
from os.path import dirname, realpath, join
from Util import StringWithSource

IMPORT = re.compile(r'^\s*?@import\s*?\(\s*?\"(.*?)\"\s*?\)\s*?;', re.DOTALL | re.MULTILINE)
COMMENT = re.compile(r'/\*.*?\*/', re.DOTALL)
VARIABLE = re.compile(r'^\s*(@(?!import).*?)\s*?:\s*?(.*?);', re.DOTALL | re.MULTILINE)
BLOCK = re.compile(r'^\s*([^@{]*\{.*?\})', re.DOTALL | re.MULTILINE)

"""
We also need to remember where a certain block comes from so that we could warn about duplicate declarations
"""
class Preprocessor:

    def __init__(self, filepath, is_recursive=False, write_to_file=False, already_imported=[]):
        self.blocks = []
        self.variables = {}
        self.text = ""
        self.base_folder = ""
        self.blocks = [] # list of tuples (block, imported_from_url)
        self.filepath = realpath(filepath)
        self.base_folder = realpath(dirname(filepath))
        self.is_recursive = is_recursive
        self.write_to_file = write_to_file
        self.already_imported = already_imported


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

        if not self.is_recursive:
            self.substitute_variables()

        if self.write_to_file:
            self.write()

    def write(self):
        with open("{}.preprocessed".format(self.filepath), "w") as out_file:
            out_file.writelines(map(lambda x : "{} /* {} */\n\n".format(x[0], x[1]), self.blocks))


    def process_blocks(self):
        blocks = BLOCK.findall(self.text)
        for b in blocks:
            self.blocks.append((re.sub("\s+", " ", b), self.filepath))


    def _print_vars(self):
        for var in self.variables:
            print("~{} : {} ({})".format(var, self.variables[var].string, self.variables[var].source))
        print("Finished vars")



    def process_variables(self):
        variables = VARIABLE.findall(self.text)
        for var in variables:
            #self.variables[var[0].strip()] = (var[1].strip(), self.filepath)
            self.variables[var[0].strip()] = StringWithSource(var[1].strip(), self.filepath)


    def process_imports(self):
        imports = IMPORT.findall(self.text)
        for imp in imports:
            imp_path = realpath(join(self.base_folder, imp))
            if imp_path in self.already_imported:
                continue
            preprocessor = Preprocessor(imp_path, is_recursive=True, already_imported=self.already_imported)
            preprocessor.process()
            self.blocks.extend(preprocessor.blocks)
            self.merge_variables(preprocessor.variables)
            self.already_imported.append(imp_path)
            self.already_imported.extend(preprocessor.already_imported)


    def merge_variables(self, other_variables):
        for key in other_variables:
            if key in self.variables:
                logging.warning("Variable redeclaration, setting the new value: \n{}\nold: {}\nnew: {}\nFirst declared in {}\nRedeclared in {}"
                                .format(key, self.variables[key].string, other_variables[key].string, self.variables[key].source, other_variables[key].source))
            first_declared = other_variables[key].source if key not in self.variables else self.variables[key].source
            self.variables[key] = StringWithSource(other_variables[key].string, first_declared)


    def substitute_variables(self):
        substituted_blocks = []

        variable_keys = self.variables.keys()
        variable_keys.sort(key=len, reverse=True) #reverse sort the var names by
        # length so that we don't substitute parts of longer var names with values from vars with shorter names

        for block, imported_from in self.blocks:
            for var in variable_keys:
                block = block.replace(var, self.variables[var].string)
            substituted_blocks.append((block, imported_from))
            if "@" in block:
                logging.warning("Unbound variable found in block {}".format(block))

        self.blocks = substituted_blocks


    def readfile(self):
        if not exists(self.filepath):
            logging.error("The file {file} doesn't exist!".format(file=self.filepath))
            exit(1)

        with open(self.filepath) as f:
            self.text = f.read()
