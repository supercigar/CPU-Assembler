# -*- coding: utf-8 -*-
"""
Created on Fri Apr 17 10:38:54 2020

@author: Andreas
"""

import re
import os
import json

RE_HEX = r"(0x([\dABCDEF]+))"
RE_BIN = r"(0b([\dABCDEF]+))"
RE_EMPTY_LINES = r"^\s*\n"
RE_COMMENT = r"((//|;|--).*)"
RE_INTERMEDIATE = r"(\w+)(.+\$)"

def unify_words(program):
    try:
        numbers, values = list(map(list, zip(*re.findall(RE_HEX, program))))
        values = list(map(lambda i: str(int(i, 16)), values))
        for pair in sorted(zip(numbers, values), key=lambda s: -len(s[0])):
            program = re.sub(*pair, program)
        numbers, values = list(map(list, zip(*re.findall(RE_BIN, program))))
        values = list(map(lambda i: str(int(i, 2)), values))
        for pair in sorted(zip(numbers, values), key=lambda s: -len(s[0])):
            program = re.sub(*pair, program)
    except ValueError:
        pass
    return program

def clean(program):
    program = re.sub(RE_EMPTY_LINES, "", program, flags=re.M)
    program = re.sub(RE_COMMENT, "", program)
    return program.strip()

def replace_labels(program):
    new_program = ""
    pc = 0
    labels = {}
    for i, line in enumerate(program.split('\n')):
        if ':' in line:
            labels[line.strip()[:-1]] = pc
        else:
            new_program += line + '\n'
            pc += 1

    for label, value in labels.items():
        new_program = new_program.replace(label, str(value))
    return new_program.strip()


def expound_intermediate(program):
    return re.sub(RE_INTERMEDIATE, r"\1i\2", program)

def lazy_int(s):
    try:
        return int(s)
    except ValueError:
        return s

replacement = {'rv': "{:01X}{:04X}",
               'r' : "{:01X}{}0000",
               'v' : "0{:04X}{}",
               ''  : "00000"}
def insert_bytecodes(program, opcodes):
    new_program = ""
    for op, arg1, arg2 in re.findall(r"^(\w+) (\d+) ?\$?(\d+)?", program, flags=re.M):
        new_program += opcodes[op]["bytecode"] + replacement[opcodes[op]["type"]].format(lazy_int(arg1), lazy_int(arg2))
        new_program += '\n'

    return new_program

def bytecode_to_vhdl(program):
    prefix = "signal PROG : ram_type := ("
    suffix = 'others => x"0000000");'
    content = ""
    for line in program.split('\n'):
        if line != '':
            content += 'x"{:07x}", '.format(int(line, 16))
    return prefix + content + suffix

def bytecode_to_ram_init(program, filepath, comment):
    comment = "; Compiled from {}\n; {}\n".format(filepath, comment)
    prefix = "memory_initialization_radix=16;\nmemory_initialization_vector=\n"
    content = ""
    for i, line in enumerate(program.split('\n')):
        if line != '':
            content += "{:07x},\n".format(int(line, 16))
    content = content[:-2] + ";"
    return comment + prefix + content

def assemble(program, opcodes):
    return insert_bytecodes(replace_labels(expound_intermediate(unify_words(clean(program)))), opcodes)

def assemble_to_ram(iFile, opcodes, oFile=None, comment=''):
    opcodes = json.load(opcodes)
    program = iFile.read()
    program = expound_intermediate(unify_words(clean(program)))
    program = insert_bytecodes(replace_labels(program), opcodes)
    program = bytecode_to_ram_init(program, iFile.name, comment)
    if oFile is None:
        oFile = open(os.path.splitext(iFile.name)[0] + ".coe", 'w')
    oFile.write(program)
    oFile.close()
    iFile.close()
    return program

if __name__ == "__main__":
    import json
    opcodes = json.load(open("../opcodes.json"))
    file = open("../examples/fibonacci.asm")
    test = assemble_to_ram(file, open("../opcodes.json", 'r'), None)