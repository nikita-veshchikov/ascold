#!python3

__date__ = "02/2016"
__author__ = "Nikita Veshchikov"


import sys

# in order to be able to import code from another directory
sys.path.append("./device/")
sys.path.append("./parser/")
sys.path.append("./config_file/")

from parser_avr_8 import *
from device import *
from config import Configuration

def printProgram(program, fullObject=False):
	for line in program:
		if fullObject:
			print(line)
		else:
			print(line.line)

if len(sys.argv) < 3:
	print("Error! Missing argument: filename")
	print("Usage: python3", sys.argv[0], "<filename asm> <filename config>")
	exit(-1)


# Parsing the input
filenameCode = sys.argv[1]
filenameConfig = sys.argv[2]
parser = avr_8_parser(filenameCode)
program = parser.parse()

# TODO: config file
config = Configuration(filenameConfig) 

randAdr = config.get_rand_list_of_addr()
maskAdr = config.get_mask_list_of_addr()

#exit(0)

# initialize the device
device = Device()
device.loadProgram(program, {CONF_RND:randAdr, CONF_MASK:maskAdr})
print("-------- Initial state --------")
print("Code")
device.printProgram()
print("Memory")
device.printMemory()

device.runProgram()
print("End")
device.printRegisters()
