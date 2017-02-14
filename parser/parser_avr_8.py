#!python3
# avr 8 parser

from pyparsing import Word, Optional, OneOrMore, Group, ParseException, ZeroOrMore, delimitedList, Suppress, Or
from collections import namedtuple, defaultdict

# constants

digits = "0123456789"
caps = "ABCDEFGHIJKLMNOPQRSTUVWXYZ" 

ins_avr = Word(caps.lower())
param = Word(caps + caps.lower() + digits + "+")

nameIns = ins_avr.setResultsName("name_ins")
paramIns = param.setResultsName("param_ins")

avr_8_ins = namedtuple('avr_8_ins', 'name op1 op2 line')

# classes

class avr_8_parser:

	def __init__(self, input_file):
		self.input_file = input_file
		
	def sanitize_asm_file(self, file_in):
		""" 
		This method prepares an input file 
		before parsing by replacing unconfortable 
		characters not related to our grammar.
		"""
		default_sep = "\n"

		with open (self.input_file, "r") as myfile:
			string_in = myfile.read()

		ins_list = list(filter(None, [i.strip() for i in string_in.split(default_sep)]))

		return ins_list

	

	def parse_line(self, string_in):
		"""
		parse_line returns a tuple of name, op1, op2 based on an line
		of AVR-8 assembly code.
		"""
		COMMA = Suppress(",")
	
		avr_elem_simp = (ins_avr + param).setResultsName("ins_group_simp")
		avr_elem = (ins_avr + param + COMMA + param).setResultsName("ins_group")
		list_of_avr_elem = Or(avr_elem | avr_elem_simp) + ZeroOrMore(Or(avr_elem | avr_elem_simp))

		return list_of_avr_elem.parseString(string_in)


	def parsed_line_to_obj(self, parsed_line, line):	
		"""
		parsed_line_to_obj transforms a list of processed 
		lines of assembly code into an map with keys 
		'name op1 op2'.
		"""
		ins_t = parsed_line[0]
		operand_1 = parsed_line[1]
		
		if len(parsed_line) == 2:
		 operand_2 = "EMPTY" 
		else:
			operand_2 = parsed_line[2]

		# Remove + from e.g. 'X+' and 
		# adds it to the name of the
		# instruction.
		
		if operand_1.endswith('+'):
			operand_1 = operand_1[:-1]
			ins_t = ins_t + "+"
		
		if operand_2.endswith('+'):
			operand_2 = operand_2[:-1]
			ins_t = ins_t + "+"

		# Remove r from registers name.

		if operand_1.startswith('r'):
			operand_1 = int(operand_1[1:])
		
		if operand_2.startswith('r'):
			operand_2 = int(operand_2[1:])

		#If the operands are an hex value,
		#cast the string to int.
		if not isinstance(operand_1, int):
			if operand_1.startswith('0x'):
				#operand_1 = operand_1[2:]
				operand_1 = int(operand_1[2:], 16)
		if not isinstance(operand_2, int):
			if operand_2.startswith('0x'):
				operand_2 = int(operand_2[2:], 16)
				#operand_2 = operand_2[2:]
				
		return (avr_8_ins(name=ins_t, op1=operand_1, op2=operand_2, line=line))

	def parse(self):
		if self.input_file is None:
			return None
		else:
			return self.parse_file(self.input_file)

	def parse_file(self, input_file):
		"""
		parse_file processes a file containing AVR-8 instructions and
		transform them into a list of maps according to the "name, 
		op1, op2" format.
		"""
		# Sanitize input file

		ins_list = self.sanitize_asm_file(input_file)
		
		if ins_list[-1] == "": # lst[-1] : gives last elem
			ins_list.pop()

		# Parse instructions line per line

		obj_list = []

		for line in ins_list:
			parsed_line = self.parse_line(line)
			obj = self.parsed_line_to_obj(parsed_line, line)
			obj_list.append(obj)

		return obj_list
	
if __name__ == "__main__":

	eg_parser = avr_8_parser("asm_expls/parser_test.s")
	obj_list = eg_parser.parse()

	for i in obj_list:
		print (i)

