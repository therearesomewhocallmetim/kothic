# a very simple test to compare two resulting files

import filecmp

string = ""

if not filecmp.cmp("../testdata/initial.txt.txt", "../testdata/output.txt.txt"):
    string = "NOT "

print("The files are {}the same".format(string))
