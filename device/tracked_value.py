#!python3

__date__ = "02/2016"
__author__ = "Nikita Veshchikov"

"""
This module represents an abstract value TrackedValue that is used by the simulator.
The value could be a constant, a random value or a set of combined mask shares.
A combinaiton of masks could also be combined with a random value.
"""

import copy
from maskWarnings import *

# mask-tuple (ID, SHARE)
ID = 0
SHARE = 1

class TrackedValue:
	def __init__(self):
		self.masks = {} # structure: {maskId0: set(share0, share1,..), maskId1: set(share0, share1, ..)}
		self.random = False
		self.randomVal = None
		self.const = False
		self.constVal = None
	
	def setToRandom(self, val=None):
		msg = self.checkRandCombinaiton(True, val)
		
		self.random = True
		self.randomVal = val
		self.const = False
		self.constVal = None
		self.masks = {}
		
		if msg!= "":
			raise(Exception(msg))
		
	def setToConst(self, val=None):
		self.random = False
		self.randomVal = None
		self.const = True
		self.constVal = val
		self.masks = {}
	
	def addRandom(self, val = None):
		
		msg = self.checkRandCombinaiton(True, val)
		self.random = True
		self.randomVal = val
		self.const = False
		
		if msg!= "":
			raise(Exception(msg))
	
	def checkValueCombination(self, otherValue):
		
		msg=[]
		tmp = self.checkRandCombinaiton(otherValue.random, otherValue.randomVal)
		if len(tmp) != 0:
			msg.append(tmp)
		
		
		if len(msg) != 0 or (not self.random and not otherValue.random): # rand problems
			tmp = self.checkMaskCombination(otherValue.masks)
			if len(tmp) != 0:
				msg.append(tmp)
		
		return "\n".join(msg)
	
	def checkRandCombinaiton(self, otherRand, otherRandVal):
		msg = ""
		if (self.random and otherRand) and (self.randomVal == otherRandVal):
			if (self.randomVal is None or otherRandVal is None):
				msg = createWarning("Potential combination of identical random values!") 
			elif (self.randomVal is not None) and (otherRandVal is not None):
				msg = createWarning("Combining identical random values!")	
		
		return msg
	
	def checkMaskCombination(self, masks):
		"""Check potential problems while combining two values"""
		messages = []
		
		for m in masks:
			if m in self.masks:
				intersection = self.masks[m] & masks[m]
				union = self.masks[m] | masks[m]
				if len(union)!=0:
					if len(intersection)!=0:
						messages.append( createWarning("Mask share {0} of '{1}' is already in {2}".format(intersection, m, self)) )
					else:
						messages.append( createWarning("Mask share {0} of '{1}' is already in {2}".format(self.masks[m], m, self)) )
		
		return "\n".join(messages)
	
	def combineWith(self, trackedVal):
		
		msg = self.checkValueCombination(trackedVal)
		self.const = False
		self.constVal = None
		
		if self.randomVal is None:
			self.randomVal = trackedVal.randomVal	
		
		self.random |= trackedVal.random
		
		for m in trackedVal.masks:
			if m in self.masks:
				self.masks[m] |= trackedVal.masks[m]
			else:
				self.masks[m] = trackedVal.masks[m]
		
		if msg!="":
			raise MaskingComplaint(msg)
	
	def loadMask(self, mask):
		"""loads a mask (ID, SHARE) in a memory cell"""
		msg = self.checkMaskCombination({mask[ID]:set({mask[SHARE]})})
		self.const = False
		self.constVal = None
		self.random = False
		self.randomVal = None
		self.masks = {mask[ID]:set({mask[SHARE]})}
		
		if msg!="":	
			raise MaskingComplaint(msg)
	
	def replaceBy(self, trackedVal):
		msg = self.checkValueCombination(trackedVal)
		self.const = trackedVal.const
		self.constVal = trackedVal.constVal
		self.random = trackedVal.random
		self.randomVal = trackedVal.randomVal
		self.masks = copy.deepcopy(trackedVal.masks)
		
		if msg!="":
			raise MaskingComplaint(msg)
	
	def isRandom(self):
		return self.random
	def isConst(self):
		return self.const
	
	def __str__(self):
		result = ""
		if self.const:
			if self.constVal is None:
				result+= "[const]"
			else:
				result+= "[const:%s]" % ( str(self.constVal) )
		if self.random:
			if self.randomVal is None:
				result+= "[rand]"
			else:
				result+= "[rand:%s]" % ( str(self.randomVal) )
		if len(self.masks) != 0:
			result+= "({0})".format(self.masks)
		if len(result) == 0:
			result = "[Not initialized]"
		
		return result



### Module Testing ###

def test_LoadMask(mask, val):
	print("LOAD :\t", mask)
	try:
		val.loadMask(mask)
	except Exception as e:
		print(e)
	print("Value :\t", val)
	return val

def test_Combine(val1, val2):
	print("Combine :\t", val1, "\t", val2)
	try:
		val1.combineWith(val2)
	except Exception as e:
		print(e)
	print("Result :\t", val1)
	return val1

def test_Replace(val1, val2):
	print("Assigning :\t", val1, "<-", val2)
	try:
		val1.replaceBy(val2)
	except Exception as e:
		print(e)
	print("Result :\t", val1)
	return val1

def test_setToRandom(val1, r=None):
	m = "[unknown]" if r is None else str(r)
	print("Assigning :\t", val1, "<- rand:", m)
	try:
		val1.setToRandom(r)
	except Exception as e:
		print(e)
	print("Result :\t", val1)
	return val1

def test_addRandom(val1, r=None):
	m = "[unknown]" if r is None else str(r)
	print("Assigning :\t", val1, "<- rand:", m)
	try:
		val1.addRandom(r)
	except Exception as e:
		print(e)
	print("Result :\t", val1)
	return val1

if __name__ == "__main__" :
	print("-------- TrackedValue test --------")
	print("---- Simple ----")
	val = TrackedValue()
	print("Empty init:", val)
	val = test_setToRandom(val)
	print("Val:", val)
	val.setToConst()
	print("Val:", val)
	
	print("---- Load one mask share ----")
	mask1 = ("a",2)
	mask2 = ("b",1)
	mask3 = ("c",0)
	mask4 = ("a",0)
	mask5 = ("c",1)
	mask6 = ("d",0)
	
	val = test_LoadMask(mask1, val)
	val = test_LoadMask(mask2, val)
	val = test_LoadMask(mask1, val)
	val = test_LoadMask(mask4, val)
	val = test_LoadMask(mask3, val)
	val = test_LoadMask(mask3, val)
	val = test_addRandom(val)
	val = test_LoadMask(mask3, val)
	val = test_addRandom(val)
	val = test_LoadMask(mask5, val)
	
	print("---- Combine Values ----")
	
	val1 = TrackedValue()
	val2 = TrackedValue()
	val1.loadMask(mask1)
	val2.loadMask(mask2)
	val1 = test_Combine(val1, val2)
	val2.loadMask(mask3)
	val1 = test_Combine(val1, val2)
	val1 = test_Combine(val1, val2)
	val2.loadMask(mask4)
	val1 = test_Combine(val1, val2)
	val2.loadMask(mask5)
	val2 = test_addRandom(val2)
	val1 = test_Combine(val1, val2)
	val3 = TrackedValue()
	val3.loadMask(mask4)
	val2 = TrackedValue()
	val2.loadMask(mask6)
	val2 = test_Combine(val2, val3)
	
	val1 = test_Combine(val1, val2)
	
	print("---- Replace Value ----")
	
	val1 = TrackedValue()
	val2 = TrackedValue()
	val3 = TrackedValue()
	val1.loadMask(mask1)
	val2.loadMask(mask2)
	val1 = test_Replace(val1, val2)
	val2.loadMask(mask3)
	val1 = test_Replace(val1, val2)
	val1 = test_Replace(val1, val2)
	val3.loadMask(mask5)
	val1 = test_Replace(val1, val3)
	val2.loadMask(mask4)
	val2 = test_addRandom(val2, "RAND1")
	val1 = test_Replace(val1, val2)
	val3 = TrackedValue()
	val3.loadMask(mask4)
	val2 = TrackedValue()
	val2.loadMask(mask6)
	val2 = test_Replace(val2, val3)
	
	val1 = test_Replace(val1, val2)
	
	print("---- Randomness test ----")
	val1 = TrackedValue()
	val2 = TrackedValue()
	val3 = TrackedValue()
	val1 = test_setToRandom(val1, "r1")
	val2 = test_setToRandom(val2, "r1")
	val3 = test_setToRandom(val3, "r2")
	val1 = test_Replace(val1, val2)
	val1 = test_Combine(val1, val3)
	
	# ---
	val1 = test_setToRandom(val1, "r1")
	val2.loadMask(mask1)
	val2 = test_addRandom(val2, "r1")
	val1 = test_Replace(val1, val2)
	
	# ---
	val3.loadMask(mask4)
	val1 = test_Combine(val1, val3)
	
	
	print ("---------------- End ----------------")
