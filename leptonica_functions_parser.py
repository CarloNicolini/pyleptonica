# -*- coding: utf-8 -*-
    
    # "pyleptonica" is a Python wrapper to Leptonica Library
    # Copyright (C) 2010 João Sebastião de Oliveira Bueno <jsbueno@python.org.br>
    
    #This program is free software: you can redistribute it and/or modify
    #it under the terms of the Lesser GNU General Public License as published by
    #the Free Software Foundation, either version 3 of the License, or
    #(at your option) any later version.

    #This program is distributed in the hope that it will be useful,
    #but WITHOUT ANY WARRANTY; without even the implied warranty of
    #MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    #GNU General Public License for more details.

    #You should have received a copy of the Lesser GNU General Public License
    #along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
This file parses the C language functions and
generates a file that anotates calling parameteers and return types for all
those functions
"""
import re
lepton_source_dir = "/home/gwidion/build/leptonlib-1.67/src/"
target_file = "leptonica_functions.py"

def get_file_contents(file_name):
      infile = open(file_name)
      # This is different than what we ar doing for the header files
      text = infile.read()
      infile.close()
      return text
      
# Sample of leptonica C file to understand the parsing functions
"""

/*!
 *  pixAffineSampled()
 *
 *      Input:  pixs (all depths)
 *              vc  (vector of 6 coefficients for affine transformation)
 *              incolor (L_BRING_IN_WHITE, L_BRING_IN_BLACK)
 *      Return: pixd, or null on error
 *
 *  Notes:
 *      (1) Brings in either black or white pixels from the boundary.
 *      (2) Retains colormap, which you can do for a sampled transform..
 *      (3) For 8 or 32 bpp, much better quality is obtained by the
 *          somewhat slower pixAffine().  See that function
 *          for relative timings between sampled and interpolated.
 */
PIX *
pixAffineSampled(PIX        *pixs,
                 l_float32  *vc,
                 l_int32     incolor)
{
l_int32     i, j, w, h, d, x, y, wpls, wpld, color, cmapindex;

"""

def strip_comment(raw_comment):
    comment = ""
    for line in raw_comment.split("\n")[1:]:
        comment += line[2:] + "\n"
    return comment

def parse_file_comment(text):
    # Expression to capture file wide comment :
    expr = re.compile(r"^(\/\*\s*$.*?)^\s\*\/"  , re.MULTILINE| re.DOTALL)
    comment = expr.findall(text)
    if not comment:
        return ""
    return strip_comment(comment[0])

def parse_prototype(prototype_text):
    prototype = prototype_text.split("\n")
    counter = 0
    last_scaped = False
    # ins ome files tehre may be some preprocessor
    # directives between the comment and the function start
    while True:
        line = prototype[counter].strip()
        if line and (last_scaped or line[0] == "#") and line[-1] == "\\":
            counter += 1
            last_scaped = True
            continue
        if line and line[0] != "#" and not last_scaped:
            break
        counter += 1
        last_scaped = False
    prototype = prototype[counter:]
    prototype_text = " ".join(prototype)
    return_type = prototype[0].strip()
    function_name = prototype[1].split("(")[0].strip()
    parameters = []
    parameter_tokens = prototype_text.split("(",1)[-1].rsplit(")",1)[0].split(",")
    #print parameter_tokens
    for token in parameter_tokens:
        if token.strip():
            data_type, name = token.rsplit(None,1)
            parameters.append((data_type.strip(), name.strip()))
    return return_type, function_name, parameters 
    
    


def parse_functions(text):
    """We take advantage of the fact that all public C functions in leptonica are
    prefixed with /*! style comments - these functions are then parsed
    for their documentation, return types and parameter lists
    """
    functions = {}
    # chop everything between a /*! staring line and  a { starting line 
    doc_and_proto_expr = re.compile(r"^(\/\*\!.*?)^{", re.MULTILINE| re.DOTALL)
    doc_and_proto = doc_and_proto_expr.findall(text)
    for function in doc_and_proto:
        raw_comment, prototype = function.split("*/")
        comment = strip_comment(raw_comment)
        return_type, name, arg_list = parse_prototype(prototype)
        functions[name] = (arg_list, return_type, comment)
    return functions
        
    


def parse_file(file_name):
    text = get_file_contents(file_name)
    comment = parse_file_comment(text)
    functions = parse_functions(text)
    return comment, functions

# indented to fit inside the generated classes
function_template = '''
    leptonica.%(name)s.argtypes = [%(argtypes)s]
    leptonica.%(name)s.restype = %(restype)s
    
    @staticmethod
    def %(name)s(*args):
        """
        %(docstring)s
        """
        %(referenciation_code)s
        return leptonica.%(name)s(*args)
'''

class_template = '''
class %(file_name)s(object):
    """%(docstring)s"""
    %(functions)s

'''

file_template = """
import ctypes
from leptonica_structures import *

try:
    leptonica = ctypes.cdll.LoadLibrary("liblept.so")
except OSError:
    leptonica = ctypes.cdll.LoadLibrary("liblept.dll")

%(classes)s

__all__ = %(class_names)s + ["leptonica"]
"""


def main(file_names):
    modules = {}
    for file_name in file_names:
        module_name = file_name.rsplit(".",1)[0]
        modules[module_name] = parse_file(lepton_source_dir + file_name)
    functions = modules[module_name][1]
    for function in functions:
        print function, functions[function][1], functions[function][0]

if __name__ == "__main__":
    main(["utils.c"])