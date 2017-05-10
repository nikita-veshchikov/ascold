#!python3

__date__ = "02/2016"
__author__ = "Nikita Veshchikov"

import copy
from tracked_value import *
from warnings import *
from math import log, ceil

CONF_RND = 0
CONF_MASK = 1
CONF_CONST = 2

PARAM_TYPE = 0
PARAM_VAL = 1

HIGH = 1
LOW = 0

#TODO: X, Y, Z  = R27-26; R29-28; R31-30 

class Device:
	def __init__(self):
		self.pc = None # program counter / instruction pointer aka current instruciton index
		self.program = []
		self.sp = None # stack pointer
		self.stack = []
		self.registerNbr = 32
		self.registers = [TrackedValue() for i in range(self.registerNbr)]
		
		self.specialRegisters = {"X":(26,27), "Y":(28,29), "Z":(30,31)}
		
		# neighbour registers that were detected for AVR ATmega163
		self.neighbours = { 0:[i for i in range(1,32)],1:[i for i in range(2,32)],\
							2:[3],3:[2], 4:[5],5:[4], 6:[7],7:[6],\
							8:[9],9:[8], 10:[11],11:[10], 12:[13],13:[12], 14:[15],15:[14],\
							16:[17],17:[16], 18:[19],19:[18], 20:[21],21:[20], 22:[23],23:[22],\
							24:[25],25:[24], 26:[27],27:[26], 28:[29],29:[28], 30:[31],31:[30]}
		self.neighbours[1].append(0)
		self.bitStorage = TrackedValue()
		self.memory = {} # dict of "adr" -> TrackedValue or "label" -> TrackedValue
		
		
		self.unknownInstructionWarning = True
		self.unsafeInstructions = {"mov":self.mov, \
							"bst":self.bst, "bld":self.bld,\
							"push":self.push, "pop":self.pop, \
							"eor":self.combine, "and":self.combine, "or":self.combine,\
							"add":self.combine, "adc":self.combineCarry, "sub":self.combineCarry, "sbc":self.combine,\
							"mul":self.mulCombine, "muls":self.mulCombine, "mulsu":self.mulCombine,\
							"fmul":self.mulCombine, "fmuls":self.mulCombine, "fmulsu":self.mulCombine,\
							"cp":self.combine, "cpc":self.combineCarry,\
							"ldi":self.ldi, "lds":self.lds, "ld":self.ld, "sts":self.sts, "st":self.st}
		
		self.unsafeCarryWarning = True
		
		# these instructions chage positions of bits in a byte and can also chage the carry flag
		# if different mask shares are stored in different parts of a byte than it is potentially unsafe
		self.byteUnsafeWarning = True
		self.potentiallyUnsafe = {"swap", "lsr", "lsl", "ror", "rol", "asr"}
		
		# XXX all operations with Carry flag as potentially unsafe
		# TODO: BST, BLD (T as a normal register)
		
		# others should be safe
		
	def getRegStr(self):
		regStr = ""
		if self.pc is None:
			regStr = "[Unintialized Registers]"
		else:
			for i in range(self.registerNbr):
				regStr+= "R{0}\t{1}\n".format(i, self.registers[i])
		return regStr
	
	def getMemoryStr(self):
		memStr = ""
		if len(self.memory) == 0:
			memStr = "[Empty Memory]"
		else:
			for cellKey in self.memory:
				fmt = {"cell":cellKey, "val":self.memory[cellKey]}
				memStr+= "{cell:#04X}\t{val}\n".format(**fmt)
		return memStr
	
	def getProgramStr(self):
		programStr = ""
		if len(self.program) == 0:
			programStr = "[Unintialized Program]"
		else:
			for i in range(len(self.program)):
				programStr += str(self.program[i].line)
				if (i == self.pc):
					programStr += " <- [PC]"
				programStr+="\n"
		return programStr
		
	def getStackStr(self):
		stackStr = ""
		if self.sp is None:
			stackStr = "[Uninitialized Stack]"
		else:
			stackStr = "[\t]"
			if self.sp == len(self.stack):
				stackStr+=" <- [SP]"
			stackStr+="\n"
			for i in range(len(self.stack)-1, -1, -1):
				stackStr += str(self.stack[i])
				if (i == self.sp):
					stackStr += " <- [SP]"
				stackStr+="\n"
			
		return stackStr
		
	# printers
	def printRegisters(self):
		print(self.getRegStr())
	def printMemory(self):
		print(self.getMemoryStr())
	def printProgram(self):
		print(self.getProgramStr())
	def printStack(self):
		print(self.getStackStr())
	
	def __str__(self):
		if self.pc is None:
			return "[Uninitialized Device]"
		else:
			return self.getProgramStr()+self.getRegStr()+self.getMemoryStr()
	
	def loadProgram(self, program, config):
		""" program: list of instructions
			config: tuple (List of Rand, Dict of Masks)
			Masks: [adr/label] -> (ID, SHARE)
		"""
		
		self.pc = 0
		self.program = copy.copy(program)
		
		self.sp = 0
		self.stack = []
		
		for adr in config[CONF_RND]:
			self.memory[adr] = TrackedValue()
			self.memory[adr].setToRandom()
		
		
		for mask in config[CONF_MASK]:
			self.memory[mask[0]] = TrackedValue()
			self.memory[mask[0]].loadMask( (mask[1], mask[2]) )
	
	def runProgram(self):
		for instruction in self.program:
			#exec self.program[self.pc]
			try:
				self.handleInstruction(instruction)
			except Exception as e:
				print("At line", self.pc, " > ", instruction.line)
				print(e)
				
			self.pc+=1
			#print("-----------")
			#self.printProgram()
	
	# --------  -------- instructions -------- -------- 
	
	def handleInstruction(self, instruction):
		# instruction = program line
		if instruction.name in self.unsafeInstructions:
			if not (instruction.op2 is None):
				self.unsafeInstructions[instruction.name](instruction.op1, instruction.op2)
			elif not (instruction.op1 is None):
				self.unsafeInstructions[instruction.name](instruction.op1)
			else:
				self.unsafeInstructions[instruction.name]()
		else:
			if instruction.name in self.potentiallyUnsafe and self.byteUnsafeWarning:
				raise( Exception(createWarning("Unsafe if different shares are in different parts of a byte.\n"+\
											   "Is it a weird bitslice implementation?\n"+\
											   "To disable this warning use: \"dev.byteUnsafeWarning=False\"")) )
			elif self.unknownInstructionWarning:
				raise( Exception(createWarning("Instruction Not implemented.\n"+\
												"To disable this warning use: \"dev.unknownInstructionWarning=False\"")) )
	
	# ---- instruction handlers ----
	
	# neighbour test
	def checkNeighbours(self, regId):
		msg = "Potential neighbouring register Leakage!\n"
		for neighbourReg in self.neighbours[regId]:
			msg+= self.registers[regId].checkMaskCombination(self.registers[neighbourReg].masks)
		
		if(len(msg) != 0): # there is a neighbour problem
			raise (Exception(msg))
	
	# generic handlers
	def combine(self, op1, op2):
		self.registers[op1].combineWith(self.registers[op2])
	
	def combineCarry(self, op1, op2):
		if self.unsafeCarryWarning:
			print(createWarning("This instruction uses the Carry Flag!\nIt is potentially unsafe if CF contain secret shares.") )
			print("To disable this warning use: \"dev.unsafeCarryWarning=False\"")
			
		self.combine(self, op1, op2)
	
	def mulCombine(self, op1, op2):
		# MUL Rd, Rr =>  R1:R0 <- Rd * Rr
		exceptMsg = []
		tmp = TrackedValue()
		tmp.replaceBy(self.registers[op1])
		try:
			tmp.combineWith(self.registers[op2])
		except Exception as e:
			exceptMsg.append(str(e))
		try:
			self.registers[0].replaceBy(tmp)
		except Exception as e:
			exceptMsg.append(str(e)+" [reg 0]")
		try:
			self.registers[1].replaceBy(tmp)
		except Exception as e:
			exceptMsg.append(str(e)+" [reg 1]")
		
		raise( Exception("\n".join(exceptMsg)) )
		
	#special handlers
	def mov(self, regId1, regId2):
		self.checkNeighbours(regId1)
		self.checkNeighbours(regId2)
		self.registers[regId1].replaceBy(self.registers[regId2])
	
	def bst(self, regId, bit):
		self.checkNeighbours(regId)
		self.bitStorage.replaceBy(self.registers[regId])
		
	def bld(self, regId, bit):
		self.registers[regId].replaceBy(self.bitStorage)
	
	def getAdrFromSpecialRegister(self, reg): # X, Y or Z
		realRegs = self.specialRegisters[reg]
		highId, lowId = realRegs[HIGH], realRegs[LOW]
		
		# TODO
		# Here we suppose that we do not have any troubles with adresses
		# This is not necessairly the case!!!
		# if you have a neighbour matrix for adresses in memory this is the location for checks
		# other potential problems with adresses should be checked here
		
		if isinstance( self.registers[lowId].constVal, str ): # H and L should be of the same type
			res = self.registers[highId].constVal + self.registers[lowId].constVal # concatenate the two
		else: # should be int
			# concatenate the two INT values (shift high part to the left then add [using OR] the low part)
			#print(self.registers[lowId])
			res = (self.registers[highId].constVal << 8) | self.registers[lowId].constVal
			#( ceil(log(self.registers[lowId].constVal, 2)) ) ) | self.registers[lowId].constVal
		
		return res
	
	def ldi(self, regId, const):
		realId = regId
		if isinstance(regId, str):
			if len(regId) == 2: # [REG][High/Low], e.g. XH, XL or ZH, ZL
				if regId[1].lower() == 'h':
					realId = self.specialRegisters[regId[0]][HIGH]
				elif regId[1].lower() == 'l':
					realId = self.specialRegisters[regId[0]][LOW]
				else:
					raise(Exception("Unknown register {0}".format(regId)))
			else:
				raise(Exception("Unknown register {0}".format(regId)))
		self.checkNeighbours(realId)
		self.registers[realId].setToConst(const)
	
	def lds(self, regId, adr):
		self.checkNeighbours(regId)
		self.registers[regId].replaceBy(self.memory[adr])
	
	def ld(self, regId, adrReg):
		self.checkNeighbours(regId)
		adr = self.getAdrFromSpecialRegister(adrReg)
		self.registers[regId].replaceBy(self.memory[adr])
	
	def st(self, adrReg, regId):
		self.checkNeighbours(regId)
		adr = self.getAdrFromSpecialRegister(adrReg)
		self.memory[adr].replaceBy(self.registers[regId])
	
	def sts(self, adr, regId):
		self.checkNeighbours(regId)
		self.memory[adr].replaceBy(self.registers[regId])
	
	def push(self, regId):
		self.checkNeighbours(regId)
		if self.sp == len(self.stack): #using new memory cells
			self.stack.append(self.registers[regId])
		else: # some stack was already used and we are now rewriting on top of it
			self.stack[self.sp].replaceBy(self.registers[regId])
		self.sp += 1
	
	def pop(self, regId):
		self.checkNeighbours(regId)
		self.sp-=1
		self.registers[regId].replaceBy(self.stack[self.sp])
	
if __name__ == "__main__":
	class Instruction():
		def __init__(self, name, op1=None, op2=None):
			self.name = name
			self.op1 = op1
			self.op2 = op2
			self.line = name+" "+str(self.op1)+" "+str(self.op2)
		def __str__(self):
			return self.name+" "+str(self.op1)+" "+str(self.op2)
	
	print("-------- Device test --------")
	print(" ---- Simple empty device ---- ")
	dev = Device()
	dev.printRegisters()
	dev.printMemory()
	dev.printStack()
	dev.printProgram()
	
	print("---- Load simple program ----")
	program = [Instruction("mov", 0, 1),\
			   Instruction("mov", 4, 3),\
			   Instruction("mov", 3, 5),\
			   Instruction("and", 3, 4),\
			   Instruction("or",  1, 2),\
			   Instruction("eor", 1, 2),\
			   Instruction("inc", 4),\
			   Instruction("push", 4),\
			   Instruction("push", 4),\
			   Instruction("push", 6),\
			   Instruction("push", 4),\
			   Instruction("pop", 5),\
			   Instruction("pop", 7),\
			   Instruction("swap", 7),\
			   Instruction("mul", 8,9)]
			   
	config = ([], [])
	dev.loadProgram(program, config)
	#dev.printRegisters()
	#dev.printMemory()
	#dev.printProgram()
	print("-------- EXEC --------")
	dev.registers[0].loadMask(("a", 1))
	dev.registers[1].loadMask(("a", 0))
	dev.registers[2].loadMask(("a", 0))
	dev.registers[3].setToRandom()
	dev.registers[4].setToRandom()
	dev.registers[5].setToRandom()
	dev.registers[6].loadMask(("b", 1))
	dev.registers[7].loadMask(("b", 0))
	dev.registers[8].loadMask(("b", 0))
	dev.registers[9].loadMask(("a", 0))
	
	dev.runProgram()
	
	print("-------- EXEC LOAD/STORE --------")
	dev1 = Device()
	program = [
				Instruction("lds", 3, "adr1"),\
				Instruction("ldi", "XL", "adr2"),\
				Instruction("ldi", "XH", ""),\
				Instruction("ld", 4, "X"),\
				Instruction("ldi", "YL", "adr1"),\
				Instruction("ldi", "YH", ""),\
				Instruction("sts", "adr1", 1),\
				Instruction("st", "Y", 0)]
	
	dev1.loadProgram(program, config)
	
	dev1.memory["adr1"] = TrackedValue()
	dev1.memory["adr2"] = TrackedValue()
	dev1.memory["adr1"].loadMask(("a", 1))
	dev1.memory["adr2"].loadMask(("b", 1))
	dev1.registers[0].loadMask(("a", 1))
	dev1.registers[1].loadMask(("a", 0))
	
	
	dev1.runProgram()
	
	#print("Mem:")
	#dev1.printMemory()
	#print("Regs:")
	#dev1.printRegisters()
	
	print("-------- EXEC BIT LOAD/STORE --------")
	
	dev2 = Device()
	program = [
				Instruction("bst", 0, 1),\
				Instruction("bld", 1, 1),\
				Instruction("bld", 2, 1)]
	
	dev2.registers[0].loadMask(("a",1))
	dev2.registers[1].loadMask(("b",0))
	dev2.registers[2].loadMask(("a",0))
	dev2.loadProgram(program, config)
	
	dev2.runProgram()
	print("------------ END ------------")
	
	print("-------- EXEC MASKING XOR --------")
	
	dev3 = Device()
	program = [
				Instruction("add", 1, 2),\
				Instruction("add", 3, 4),\
				Instruction("eor", 0, 1),\
				Instruction("eor", 0, 3)]
	
	dev3.registers[0].setToRandom()
	dev3.registers[1].loadMask(("a",0))
	dev3.registers[2].loadMask(("b",1))
	dev3.registers[3].loadMask(("a",1))
	dev3.registers[4].loadMask(("b",0))
	dev3.loadProgram(program, config)
	
	dev3.runProgram()
	print("------------ END ------------")
	
	
