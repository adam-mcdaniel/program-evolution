import random
from copy import deepcopy, copy
import numpy as np
from scipy.stats import entropy
from time import time
import sys
import math


class Tape:
    def __init__(self, length=256, blank_symbol=0, head_position=0):
        self.tape = [blank_symbol] * length
        self.head_position = head_position
        self.register = self.blank_symbol = blank_symbol
        self.max_steps = 20000
        self.steps = 0
        self.deref_stack = []
        self.tm = None
        self.env = {}
    
    def __getitem__(self, index):
        # Check if index is out of bounds
        if index >= len(self.tape):
            # If so, fill with blank symbols
            if index >= self.max_steps:
                raise RuntimeError("Maximum number of steps exceeded")
            self.tape += [self.blank_symbol] * (index - len(self.tape) + 1)
        elif index < 0:
            return self.blank_symbol
        return self.tape[index]
        
    def __setitem__(self, index, value):
        # Check if index is out of bounds
        if index >= len(self.tape):
            # If so, fill with blank symbols
            self.tape += [self.blank_symbol] * (index - len(self.tape) + 1)
        elif index < 0:
            return
        self.tape[index] = value

    def add_env(self, key, value):
        self.env[key] = value
    
    def get_env(self, key):
        if key not in self.env:
            return None
        return self.env[key]

    def get(self):
        return self[self.head_position]
    
    def set(self, value):
        self[self.head_position] = int(value)

    def move_head(self, direction):
        if type(direction) == str:
            direction = direction.upper()
            if direction == 'L':
                self.head_position -= 1
            elif direction == 'R':
                self.head_position += 1
        elif type(direction) == int:
            self.head_position += direction
        else:
            raise TypeError("Direction must be a string ('l' or 'r') or signed integer (number of steps), not " + str(type(direction)) + " " + str(direction))
    
    def set_head_position(self, position):
        self.head_position = int(position)

    def get_head_position(self):
        return int(self.head_position)
    
    def __eq__(self, other):
        return self.tape == other.tape and self.head_position == other.head_position and self.register == other.register and self.blank_symbol == other.blank_symbol and self.deref_stack == other.deref_stack
    
    def __str__(self):
        return str(self.tape)

    def __repr__(self):
        return str(self.tape)

    def __len__(self):
        return len(self.tape)

class TuringMachine:
    def __init__(self, operations, input=None):
        self.operations = operations
        self.input = input
        self.output = []
        self.step_position = 0

    def get_int(self):
        if len(self.input) == 0:
            return 0
        return int(self.input.pop(0))

    def get_char(self):
        if len(self.input) == 0:
            return chr(0)
        return self.input.pop(0)
    
    def run(self, tape, steps=1000):
        tape.max_steps = steps
        tape.steps = 0
        tape.tm = self
        try:
            for operation in self.operations:
                operation.checked_apply(tape)
        except RuntimeError as e:
            if str(e) == "Maximum number of steps exceeded":
                tape.tm = None
                return tape
            else:
                raise e
        tape.tm = None
        self.operations = []
        self.input = None
        tape.env = None
        return tape
    
    def step(self, tape, max_steps=20000):
        tape.tm = self
        tape.max_steps = max_steps
        if self.step_position >= tape.max_steps:
            raise RuntimeError("Maximum number of steps exceeded")
        elif self.step_position < 0:
            raise RuntimeError("Steps cannot be negative")
        elif self.step_position >= len(self.operations):
            return tape
        self.operations[self.step_position].checked_apply(tape)
        self.step_position += 1
        return tape

class Operation:
    def checked_apply(self, tape):
        tape.steps += 1
        if tape.steps > tape.max_steps:
            raise RuntimeError("Maximum number of steps exceeded")
        self.apply(tape)

    def apply(self, tape):
        pass

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.__dict__ == other.__dict__

    def __str__(self):
        return self.__class__.__name__ + "()"
    
    def __repr__(self):
        return str(self)

class SetTape(Operation):
    def __init__(self, value):
        self.value = value
    
    def apply(self, tape):
        tape.set(self.value)

    def __str__(self):
        return self.__class__.__name__ + f"({self.value})"

class SetRegister(Operation):
    def __init__(self, value):
        self.value = value
    
    def apply(self, tape):
        tape.register = self.value

    def __str__(self):
        return self.__class__.__name__ + f"({self.value})"

class Restore(Operation):
    def apply(self, tape):
        tape.register = tape.get()

class Move(Operation):
    def __init__(self, direction):
        self.direction = direction
    
    def apply(self, tape):
        tape.move_head(self.direction)

    def __str__(self):
        return self.__class__.__name__ + f"({self.direction})"

class MoveRight(Move):
    def __init__(self, steps):
        self.steps = steps

    def apply(self, tape):
        tape.move_head(self.steps)

    def __str__(self):
        return self.__class__.__name__ + f"({self.steps})"
    
class MoveLeft(Move):
    def __init__(self, steps):
        self.steps = steps

    def apply(self, tape):
        tape.move_head(-self.steps)

    def __str__(self):
        return self.__class__.__name__ + f"({self.steps})"

class Add(Operation):
    def apply(self, tape):
        tape.register += tape.get()

class Subtract(Operation):
    def apply(self, tape):
        tape.register -= tape.get()

class Multiply(Operation):
    def apply(self, tape):
        tape.register *= tape.get()

class Divide(Operation):
    def apply(self, tape):
        try:
            tape.register /= tape.get()
        except ZeroDivisionError:
            tape.register = 0

class WhileLoop(Operation):
    def __init__(self, operations=[]):
        self.operations = operations
    
    def apply(self, tape):
        while tape.register != 0:
            if len(self.operations) == 0:
                break
            for operation in self.operations:
                operation.checked_apply(tape)

    def __str__(self):
        return self.__class__.__name__ + f"({self.operations})"

class If(Operation):
    def __init__(self, then_operations=[]):
        self.then_operations = then_operations
    
    def apply(self, tape):
        if tape.register != 0:
            for operation in self.then_operations:
                operation.checked_apply(tape)

    def __str__(self):
        return self.__class__.__name__ + f"({self.then_operations})"

class IfElse(Operation):
    def __init__(self, then_operations=[], else_operations=[]):
        self.then_operations = then_operations
        self.else_operations = else_operations
    
    def apply(self, tape):
        if tape.register != 0:
            for operation in self.then_operations:
                operation.checked_apply(tape)
        else:
            for operation in self.else_operations:
                operation.checked_apply(tape)

    def __str__(self):
        return self.__class__.__name__ + f"({self.then_operations}, {self.else_operations})"

class Dereference(Operation):
    def __init__(self, operations=[]):
        self.operations = operations
    
    def apply(self, tape):
        if len(self.operations) > 0:
            old_head = tape.get_head_position()
            new_head = int(tape.get())
            tape.move_head(int(new_head - old_head))
            for operation in self.operations:
                operation.checked_apply(tape)
            tape.set_head_position(old_head)
        else:
            tape.deref_stack.append(tape.head_position)
            tape.head_position = int(tape.get())

    def __str__(self):
        if self.operations:
            return self.__class__.__name__ + f"({self.operations})"
        else:
            return self.__class__.__name__ + "()"

class Reference(Operation):
    def apply(self, tape):
        if len(tape.deref_stack) > 0:
            tape.head_position = tape.deref_stack.pop()
        else:
            tape.head_position = 0

class PutChar(Operation):
    def apply(self, tape):
        try:
            tape.tm.output.append(chr(tape.register))
        except:
            pass

class PutInt(Operation):
    def apply(self, tape):
        tape.tm.output.append(tape.register)

class GetInt(Operation):
    def apply(self, tape):
        if tape.tm.input is not None:
            tape.register = tape.tm.get_int()
        else:
            tape.register = int(input(""))

class GetChar(Operation):
    def apply(self, tape):
        try:
            if tape.tm.input is not None:
                tape.register = tape.tm.get_char()
            else:
                tape.register = ord(input(""))
        except ValueError:
            tape.register = 0

class Where(Operation):
    def apply(self, tape):
        tape.register = tape.head_position

class Save(Operation):
    def apply(self, tape):
        tape.set(tape.register)

class Allocate(Operation):
    def apply(self, tape):
        tape.register = len(tape.tape)
        tape.tape.extend([0] * (int(tape.register) + 32))

class IsNonNegative(Operation):
    def apply(self, tape):
        tape.register = tape.register >= 0

class Index(Operation):
    def apply(self, tape):
        tape.register += tape.get()

class Function(Operation):
    def __init__(self, name=None, operations=[]):
        self.name = name
        self.operations = operations
    
    def apply(self, tape):
        if self.name is not None and tape.get_env(self.name) is None:
            tape.add_env(self.name, self.operations)

    def __str__(self):
        return self.__class__.__name__ + f"({self.name}, {self.operations})"

class Call(Operation):
    def __init__(self, name=None):
        self.name = name
    
    def apply(self, tape):
        name = self.name
        if self.name is None:
            if int(tape.register) == tape.register:
                name = int(tape.register)
        try:
            f = tape.get_env(name)
            if f is not None:
                for operation in f:
                    operation.checked_apply(tape)
            else:
                # pass
                raise Exception("Error: Function " + str(name) + " not found")
        except KeyError:
            # pass
            raise Exception("Error: Function " + str(name) + " not found")

    def __str__(self):
        if self.name is None:
            return super().__str__()
        return self.__class__.__name__ + f"({self.name})"

def parse(code, token_start=0, fun_id=0, depth=0):
    tokens = code.split()
    operations = []
    i = token_start
    while i < len(tokens):
        token = tokens[i]
        if token == 'fun':
            body, i = parse(code, i + 1, fun_id + 1, operations)
            operations.append(Function(fun_id, body))
            fun_id += 1
        elif token == 'while':
            body, i = parse(code, i + 1, fun_id, operations)
            operations.append(WhileLoop(body))
        elif token == 'if':
            then_body, i = parse(code, i + 1, fun_id, operations)
            if tokens[i] == 'else':
                else_body, i = parse(code, i + 1, fun_id, operations)
                operations.append(IfElse(then_body, else_body))
            elif tokens[i] == 'end':
                operations.append(If(then_body))
            else:
                print("Error: Expected else or end")
        elif token == 'else':
            return operations, i
        elif token == 'end':
            return operations, i
        elif token == 'call':
            operations.append(Call())
        elif token == 'put':
            if tokens[i+1] == 'stdout.char' and tokens[i+2] == '#0':
                operations.append(PutChar())
                i += 2
            elif tokens[i+1] == 'stdout.int' and tokens[i+2] == '#0':
                operations.append(PutInt())
                i += 2
            else:
                print("Error: Unknown put operation")
        elif token == 'get':
            if tokens[i+1] == 'stdin.int' and tokens[i+2] == '#0':
                operations.append(GetInt())
                i += 2
            elif tokens[i+1] == 'stdin.char' and tokens[i+2] == '#0':
                operations.append(GetChar())
                i += 2
            else:
                print("Error: Unknown get operation")
        elif token == 'set':
            i += 1
            n = int(tokens[i])
            operations.append(SetRegister(n))
        elif token == 'add':
            operations.append(Add())
        elif token == 'sub':
            operations.append(Subtract())
        elif token == 'mul':
            operations.append(Multiply())
        elif token == 'div':
            operations.append(Divide())
        # elif token == 'rem':
        #     operations.append(Arithmetic(Arithmetic.REMAINDER))
        elif token == 'deref':
            operations.append(Dereference())
        elif token == 'ref':
            operations.append(Reference())
        elif token == 'ret':
            pass
        elif token == 'alloc':
            operations.append(Allocate())
        elif token == 'index':
            operations.append(Index())
        elif token == 'where':
            operations.append(Where())
        elif token == 'gez':
            operations.append(IsNonNegative())
        elif token == 'sav':
            operations.append(Save())
        elif token == 'res':
            operations.append(Restore())
        elif token == 'mov':
            direction = int(tokens[i+1])
            if direction >= 0:
                operations.append(MoveRight(direction))
            else:
                operations.append(MoveLeft(-direction))
            i += 1
        else:
            print(f"Unknown token: {token}")
        i += 1
    return operations, i


# Genome looks like a list of numbers like so:
# [1, 2, 3, [4, 5, [6, 7], [8, 9], 10], 11, 12, [[13, 14, 15], 16, [17]]]
# This is a list of operations, where the numbers are the indices of the operations.
# The lists of operations are the blocks of operations.
class Genome:
    def __init__(self, operations, genome=None, fitness_function=None):
        self.operations = operations
        self.fitness_function = fitness_function
        self._fitness = None

        if genome is None:
            self.genome = []
        else:
            self.genome = genome

    def get_size(self):
        total = 0
        for gene in self.genome:
            if type(gene) == list:
                total += Genome(self.operations, gene).get_size()
            else:
                total += 1
        return total

    def set_fitness_function(self, fitness_function):
        self.fitness_function = fitness_function

    def from_operations(ops, operation_set, fun_id=0):
        # Derive the genome list from the operations. This works by taking the operations,
        # finding their index in the operations list, and then replacing the operation with
        # the index.
        genome = []
        op_types = [type(op) for op in operation_set]
        for op in ops:
            operation_type = type(op)
            idx = op_types.index(operation_type)
            if operation_type in [WhileLoop, If]:
                body = [idx]
                body.extend(Genome.from_operations(op.operations, operation_set).genome)
                genome.append(body)
            elif operation_type == Function:
                body = [idx, op.name]
                body.extend(Genome.from_operations(op.operations, operation_set, fun_id+1).genome)
                genome.append(body)
            elif operation_type == IfElse:
                then_body = Genome.from_operations(op.then_operations, operation_set).genome
                else_body = Genome.from_operations(op.else_operations, operation_set).genome
                genome.append([idx, list(then_body), list(else_body)])
            elif operation_type == MoveLeft:
                genome.append([idx, op.steps])
            elif operation_type == MoveRight:
                genome.append([idx, op.steps])
            elif operation_type == SetRegister:
                genome.append([idx, op.value])
            else:
                genome.append(idx)

        return Genome(operation_set, genome)
    
    def get_operation(self, index):
        return self.operations[index]
    
    def mutate(self, mutation_rate):
        self._fitness = None
        if random.random() < 0.5:
            for i in range(len(self.genome)):
                if random.random() < mutation_rate:
                    if type(self.genome[i]) == list:
                        self.genome[i] = list(Genome(self.operations, deepcopy(self.genome[i])).mutate(mutation_rate).genome)
                    else:
                        self.genome[i] = random.randint(0, len(self.operations) - 1)
        else:
            for i in range(random.randint(1, 5)):
                if random.random() < 0.5:
                    if random.random() < 0.5:
                        self.insert_random_gene()
                    else:
                        self.remove_random_gene()
                else:
                    if random.random() < 0.5:
                        self.swap_random_gene()
                    else:
                        self.modify_random_gene()

        return self
            
    def crossover(self, other):
        # Randomly select a crossover point.
        index = random.randint(0, min(len(self.genome) - 1, len(other.genome) - 1))
        # Create two new genomes by swapping the genes after the crossover point.
        return Genome(self.operations, self.genome[:index] + other.genome[index:], fitness_function=self.fitness_function), Genome(self.operations, other.genome[:index] + self.genome[index:], fitness_function=self.fitness_function)

    def crossover_splits(self, other):
        result = []
        for a, b in zip(self.genome, other.genome):
            if type(a) == list and type(b) == list:
                result.append(Genome(self.operations, a).crossover_splits(Genome(self.operations, b)).genome)
            else:
                if random.random() < 0.5:
                    result.append(a)
                else:
                    result.append(b)
        return Genome(self.operations, result, fitness_function=self.fitness_function)

    def remove_random_gene(self):
        for i in range(len(self.genome)):
            if random.random() < 2 / len(self.genome):
                if type(self.genome[i]) == list:
                    if random.random() < 0.5:
                        self.genome[i] = list(Genome(self.operations, self.genome[i]).remove_random_gene().genome)
                    else:
                        del self.genome[i]
                else:
                    del self.genome[i]
                return self
        return self
    
    def insert_random_gene(self):
        for i in range(len(self.genome)):
            if random.random() < 2 / len(self.genome):
                if type(self.genome[i]) == list:
                    self.genome[i] = list(Genome(self.operations, self.genome[i]).insert_random_gene().genome)
                else:
                    self.genome.insert(i, random.randint(0, len(self.operations) - 1))
                return self
        self.genome.append(random.randint(0, len(self.operations) - 1))
        return self
    
    def swap_random_gene(self):
        for i in range(len(self.genome)):
            if random.random() < 2 / len(self.genome):
                if type(self.genome[i]) == list:
                    self.genome[i] = list(Genome(self.operations, self.genome[i]).swap_random_gene().genome)
                else:
                    self.genome[i] = random.randint(0, len(self.operations) - 1)
                return self
        return self
    
    def modify_random_gene(self):
        for i in range(len(self.genome)):
            if random.random() < 2 / len(self.genome):
                if type(self.genome[i]) == list:
                    self.genome[i] = list(Genome(self.operations, self.genome[i]).modify_random_gene().genome)
                else:
                    self.genome[i] = min(self.genome[i] + random.randint(-1, 1), len(self.operations) - 1)
                return self
        return self

    def into_operations(self):
        func_count = 0
        operations = []
        for operation in self.genome:
            if type(operation) == list:
                # Get whether this is supposed to be a loop, deref, or function
                if len(operation) == 0:
                    continue
                if type(operation[0]) == list:
                    operations.extend(Genome(self.operations, operation[0]).into_operations())
                    operations.extend(Genome(self.operations, operation[1:]).into_operations())
                    continue
                operation_type = type(self.get_operation(operation[0]))

                if operation_type == WhileLoop:
                    operations.append(WhileLoop(Genome(self.operations, operation[1:]).into_operations()))
                elif operation_type == If:
                    operations.append(If(Genome(self.operations, operation[1:]).into_operations()))
                elif operation_type == MoveRight:
                    operations.append(MoveRight(operation[1]))
                elif operation_type == MoveLeft:
                    operations.append(MoveLeft(operation[1]))
                elif operation_type == SetRegister:
                    if len(operation) == 2:
                        operations.append(SetRegister(operation[1]))
                    else:
                        raise Exception('SetRegister with no value')
                elif operation_type == IfElse:
                    if len(operation) == 3:
                        operations.append(IfElse(Genome(self.operations, operation[1]).into_operations(), Genome(self.operations, operation[2]).into_operations()))
                    # elif len(operation) == 2:
                    #     operations.append(If(Genome(self.operations, operation[1]).into_operations()))
                    else:
                        raise Exception('IfElse with no value')
                        # operations.append(If(Genome(self.operations, operation[1:]).into_operations()))
                elif operation_type == Function:
                    operations.append(Function(int(operation[1]), Genome(self.operations, operation[2:]).into_operations()))
                    # func_count += 1
                else:
                    # print("Unknown operation type", operation_type)
                    operations.extend(Genome(self.operations, operation[:]).into_operations())
            else:
                if operation >= len(self.operations):
                    raise IndexError(f"Operation index {operation} is out of range")
                operations.append(self.get_operation(operation))
                
        return operations
    
    def copy(self):
        return Genome(deepcopy(self.operations), deepcopy(self.genome), fitness_function=deepcopy(self.fitness_function))

    def fitness(self):
        if self._fitness is not None:
            return self._fitness

        if self.fitness_function is not None:
            self._fitness = self.fitness_function(deepcopy(self))
            return self._fitness
        else:
            raise Exception("No fitness function defined")

    def evaluate(self, input=None, max_steps=100000):
        tape = Tape()
        tm = TuringMachine(deepcopy(self.into_operations()), input)
        tm.run(tape, steps=max_steps)
        return tm

    def __lt__(self, other):
        return self.fitness() < other.fitness()

    def __str__(self):
        return str(self.genome)
    
    def __repr__(self):
        return str(self)

SAGE_OPERATIONS = [
    SetRegister(-1),
    # SetTape(-1),
    SetRegister(0),
    # SetTape(0),
    SetRegister(1),
    # SetTape(1),
    MoveLeft(1),
    MoveRight(1),
    Dereference(),
    Function(),
    Call(),
    Save(),
    Restore(),
    GetChar(),
    PutChar(),
    GetInt(),
    PutInt(),

    If(),
    IfElse(),
    WhileLoop(),

    Dereference(),
    Reference(),
    Allocate(),
    Index(),
    Where(),
    IsNonNegative(),

    Add(),
    Subtract(),
    Multiply(),
    Divide()
]

def how_sorted_is_list(l, total=100):
    # Pick a bunch of random i, j values
    # and see how many times i < j
    # and l[i] < l[j]
    count = 0
    if len(l) <= 1:
        return 1.0
    
    for _ in range(total):
        i = j = 0
        while i == j:
            i = random.randint(0, len(l) - 1)
            j = random.randint(0, len(l) - 1)
        if type(l[min(i, j)]) == type(l[max(i, j)]):
            if l[min(i, j)] <= l[max(i, j)]:
                count += 1
        else:
            count -= 1
    return count / total

def sorted_fitness_function(genome):
    # Create several lists of differing lengths, testing sizes 0, 1, ..., 10
    # and see how sorted they are.
    lists = []
    if genome.get_size() < 100:
        return 0.0

    for i in range(1, 9):
        lists.append([random.randint(0, 100) for _ in range(i)])

    fitness = 0.0
    for l in lists:
        input_list = [len(l)]
        input_list.extend(l)

        tm = None
        try:
            tm = genome.evaluate(input_list)
            fitness += how_sorted_is_list(tm.output) * 50.0
            l.sort()
            if tm.output != l:
                # print("Failed to sort", l, tm.output)
                fitness = 0.0
                break
        except:
            fitness = 0.0
            break

    return fitness / genome.get_size()

def factorial_fitness_function(genome):
    # Create several lists of differing lengths, testing sizes 0, 1, ..., 10
    # and see how sorted they are.
    fitness = 0.0
    for i in range(0, 15):
        try:
            tm = genome.evaluate([int(i)], 5000)
            if tm.output == [math.factorial(i)]:
                fitness += 1.0
            else:
                fitness = 0.0
                break
        except:
            fitness = 0.0
            break

    return fitness / genome.get_size()


POPULATION_SIZE = 100

def evolve_optimizations(path_to_vm_code, fitness_function):
    print(f'Evolving optimizations for \'{path_to_vm_code}\'...')
    genomes = [Genome.from_operations(parse(open(path_to_vm_code).read())[0], SAGE_OPERATIONS) for _ in range(POPULATION_SIZE)]
    old_genome_size = genomes[0].get_size()
    for genome in genomes:
        genome.set_fitness_function(fitness_function)
    print("Sorting genomes...")
    genomes.sort()
    genomes = genomes[::-1]
    print("Printing fitnesses...")
    print(list(map(lambda g: g.fitness(), genomes)))
    try:
        for epoch in range(100):
            print(f"Epoch {epoch}")

            genomes = genomes[:POPULATION_SIZE//10]
            del genomes[POPULATION_SIZE//10:]

            print("Fitnesses:", list(map(lambda g: g.fitness(), genomes)))
            
            print("Mutating...")
            # Mutate the genomes.
            for genome in genomes:
                if len(genomes) < POPULATION_SIZE:
                    for _ in range(10):
                        new_genome = genome.copy()
                        new_genome.mutate(0.01)
                        genomes.append(new_genome)

            # Sort the genomes by fitness.
            print("Sorting genomes...")
            genomes.sort()
            genomes = genomes[::-1]

            print('Program size:', genomes[0].get_size())
    except KeyboardInterrupt:
        pass
    finally:
        new_genome_size = genomes[0].get_size()

    return genomes[0].into_operations(), old_genome_size, new_genome_size 


if __name__ == '__main__':
    args = sys.argv[1:]
    if len(args) > 0 and args[0] == 'factorial':
        genome, old_genome_size, new_genome_size = evolve_optimizations('factorial.vm.sg', factorial_fitness_function)
        print(genome)
        print(old_genome_size, new_genome_size)
        exit(0)
    elif len(args) > 0 and args[0] == 'sort':
        # Otherwise, use the default VM code.
        genome, old_genome_size, new_genome_size = evolve_optimizations('sort.vm.sg', sorted_fitness_function)
        print(genome)
        print(old_genome_size, new_genome_size)
        exit(0)
    else:
        print('Usage: python3 sage.py [factorial|sort]')
        exit(1)