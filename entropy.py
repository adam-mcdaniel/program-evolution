from sage import *
import random

program = [SetRegister(1), ForLoop([IncrementTape(), IncrementRegister(), Move(1)])]

number = input('Enter a number: ')

tm = SageVirtualMachine(program, [])
tape = Tape(1000)
tm.run(tape, 100000)
print(tape.tape)
