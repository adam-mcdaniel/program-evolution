import random
from copy import deepcopy
import numpy as np
from scipy.stats import entropy

class Tape:
    def __init__(self, length=1000, blank_symbol=0, head_position=0, max_steps=1000):
        self.tape = [blank_symbol] * length
        self.head_position = head_position
        self.register = self.blank_symbol = blank_symbol
        self.max_steps = max_steps
        self.steps = 0
        self.env = {}
    
    def __getitem__(self, index):
        # Check if index is out of bounds
        if index >= len(self.tape):
            # If so, fill with blank symbols
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
        self[self.head_position] = value

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
    
    def __str__(self):
        return str(self.tape)

    def __repr__(self):
        return str(self.tape)

    def __len__(self):
        return len(self.tape)

class TuringMachine:
    def __init__(self, operations):
        self.operations = operations
    
    def run(self, tape, steps=1000):
        tape.max_steps = steps
        tape.steps = 0
        try:
            for operation in self.operations:
                operation.checked_apply(tape)
        except RuntimeError:
            pass
        return tape

class Operation:
    def checked_apply(self, tape):
        tape.steps += 1
        if tape.steps > tape.max_steps:
            raise RuntimeError("Maximum number of steps exceeded")
        self.apply(tape)

    def apply(self, tape):
        pass

    def __str__(self):
        return self.__class__.__name__
    
    def __repr__(self):
        return str(self)

class SetTape(Operation):
    def __init__(self, value):
        self.value = value
    
    def apply(self, tape):
        tape.set(self.value)

    def __str__(self):
        return super().__str__() + f"({self.value})"

class SetRegister(Operation):
    def __init__(self, value):
        self.value = value
    
    def apply(self, tape):
        tape.register = self.value

    def __str__(self):
        return super().__str__() + f"({self.value})"

class Restore(Operation):
    def apply(self, tape):
        tape.register = tape.get()

class Move(Operation):
    def __init__(self, direction):
        self.direction = direction
    
    def apply(self, tape):
        tape.move_head(self.direction)

    def __str__(self):
        return super().__str__() + f"({self.direction})"

class Arithmetic(Operation):
    ADD = lambda x, y: x + y
    SUBTRACT = lambda x, y: x - y
    MULTIPLY = lambda x, y: min(x, 2**64) * min(y, 2**64)
    DIVIDE = lambda x, y: x / y
    MODULO = lambda x, y: x % y

    def __init__(self, operation):
        self.operation = operation
    
    def apply(self, tape):
        try:
            tape.register = self.operation(tape.register, tape.get())
        except ZeroDivisionError:
            tape.register = 0

    def __str__(self):
        if self.operation == Arithmetic.ADD:
            return "Add"
        elif self.operation == Arithmetic.SUBTRACT:
            return "Subtract"
        elif self.operation == Arithmetic.MULTIPLY:
            return "Multiply"
        elif self.operation == Arithmetic.DIVIDE:
            return "Divide"
        elif self.operation == Arithmetic.MODULO:
            return "Modulo"
        else:
            return super().__str__()

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
        return super().__str__() + f"({self.operations})"

class ForLoop(Operation):
    def __init__(self, operations=[]):
        self.operations = operations
    
    def apply(self, tape):
        while tape.register > 0:
            if len(self.operations) == 0:
                break
            for operation in self.operations:
                operation.checked_apply(tape)
            tape.register -= 1

    def __str__(self):
        return super().__str__() + f"({self.operations})"

class If(Operation):
    def __init__(self, operations=[]):
        self.operations = operations
    
    def apply(self, tape):
        if tape.register != 0:
            for operation in self.operations:
                operation.checked_apply(tape)

class Dereference(Operation):
    def __init__(self, operations=[]):
        self.operations = operations
    
    def apply(self, tape):
        old_head = tape.get_head_position()
        new_head = int(tape.get())
        tape.move_head(int(new_head - old_head))
        for operation in self.operations:
            operation.checked_apply(tape)
        tape.set_head_position(old_head)

    def __str__(self):
        return super().__str__() + f"({self.operations})"

class Print(Operation):
    def apply(self, tape):
        print(tape.register)

class Input(Operation):
    def apply(self, tape):
        try:
            tape.register = int(input("Input: "))
        except ValueError:
            tape.register = 0

class DecrementRegister(Operation):
    def apply(self, tape):
        tape.register = tape.register - 1

class IncrementRegister(Operation):
    def apply(self, tape):
        tape.register = tape.register + 1

class DecrementTape(Operation):
    def apply(self, tape):
        tape.set(tape.get() - 1)

class IncrementTape(Operation):
    def apply(self, tape):
        tape.set(tape.get() + 1)

class Save(Operation):
    def apply(self, tape):
        tape.set(tape.register)

class Function(Operation):
    def __init__(self, name=None, operations=[]):
        self.name = name
        self.operations = operations
    
    def apply(self, tape):
        if self.name is not None and tape.get_env(self.name) is None:
            tape.add_env(self.name, self.operations)

    def __str__(self):
        return super().__str__() + f"({self.name}, {self.operations})"

class Call(Operation):
    def __init__(self, name=None):
        self.name = name
    
    def apply(self, tape):
        if self.name is None:
            if int(tape.register) == tape.register:
                self.name = int(tape.register)
        try:
            f = tape.get_env(self.name)
            if f is not None:
                for operation in f:
                    operation.checked_apply(tape)
        except KeyError:
            pass

    def __str__(self):
        if self.name is None:
            return super().__str__() + f"(Register)"
        return super().__str__() + f"({self.name})"

tm = TuringMachine([
    Function('add', [
        Dereference([
            Restore(),
            Move('R'),
            Arithmetic(Arithmetic.ADD),
            Print()
        ]),
    ]),

    SetTape(1),
    Move('R'),
    SetRegister(2),
    Save(),
    Move('R'),
    SetTape(1),

    SetTape(100),
    Dereference([
        SetTape(10),
        Move('R'),
        SetTape(9),
    ]),

    Call('add'),
    Save(),
])

# Genome looks like a list of numbers like so:
# [1, 2, 3, [4, 5, [6, 7], [8, 9], 10], 11, 12, [[13, 14, 15], 16, [17]]]
# This is a list of operations, where the numbers are the indices of the operations.
# The lists of operations are the blocks of operations.
class Genome:
    def __init__(self, operations, genome=None):
        self.operations = operations

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

    def random(operations, length=100):
        genome, _ = gen_random_genome(length)
        return Genome(operations, genome)

    def get_operation(self, index):
        return self.operations[index]
    
    def mutate(self, mutation_rate):
        for i in range(len(self.genome)):
            if random.random() < mutation_rate:
                if type(self.genome[i]) == list:
                    self.genome[i] = list(Genome(self.operations, self.genome[i]).mutate(mutation_rate).genome)
                else:
                    self.genome[i] = random.randint(0, len(self.operations) - 1)

        if random.random() < 0.5:
            x = random.random()
            if x < 0.3333:
                self.insert_random_gene()
            elif x < 0.6666:
                self.swap_random_gene()
            else:
                self.remove_random_gene()

        return self
        
    def crossover(self, other):
        # Randomly select a crossover point.
        index = random.randint(0, min(len(self.genome) - 1, len(other.genome) - 1))
        # Create two new genomes by swapping the genes after the crossover point.
        return Genome(self.operations, self.genome[:index] + other.genome[index:]), Genome(self.operations, other.genome[:index] + self.genome[index:])

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
        return Genome(self.operations, result)

    def remove_random_gene(self):
        for i in range(len(self.genome)):
            if random.random() < 2 / len(self.genome):
                if type(self.genome[i]) == list:
                    self.genome[i] = list(Genome(self.operations, self.genome[i]).remove_random_gene().genome)
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
                operation_type = self.get_operation(operation[0])
                if type(operation_type) == WhileLoop:
                    operations.append(WhileLoop(Genome(self.operations, operation[1:]).into_operations()))
                if type(operation_type) == ForLoop:
                    operations.append(ForLoop(Genome(self.operations, operation[1:]).into_operations()))
                elif type(operation_type) == Dereference:
                    operations.append(Dereference(Genome(self.operations, operation[1:]).into_operations()))
                elif type(operation_type) == Function:
                    operations.append(Function(func_count, Genome(self.operations, operation[1:]).into_operations()))
                    func_count += 1
                else:
                    operations.append(ForLoop(Genome(self.operations, operation).into_operations()))
            else:
                if operation >= len(self.operations):
                    raise IndexError(f"Operation index {operation} is out of range")
                operations.append(self.get_operation(operation))
                
        return operations
    
    def fitness(self):
        # Evaluate the program.
        result = self.evaluate()
        tape = result.tape
        steps = result.steps
        # The fitness is the number of 1s in the tape.
        # return result.tape.count(1)
        try:
            result = entropy(np.array(list(map(lambda x: min(x, 2.0 ** 16), result.tape)))).sum()
            if np.isnan(result):
                return 0.0
        except:
            print(result)
            raise Exception("Entropy failed")
        return result * 1000 / self.get_size()
        
    def evaluate(self):
        tape = Tape()
        tm = TuringMachine(self.into_operations())
        tm.run(tape, 3000)
        return tape
    
    def __lt__(self, other):
        return self.fitness() < other.fitness()

    def __str__(self):
        return str(self.genome)
    
    def __repr__(self):
        return str(self)

operations = [
    SetRegister(-1),
    SetTape(-1),
    SetRegister(0),
    SetTape(0),
    SetRegister(1),
    SetTape(1),
    Move('R'),
    Move('L'),
    Move('R'),
    Move('L'),
    ForLoop(),
    Dereference(),
    Function(),
    Function(),
    Function(),
    Function(),
    Function(),
    Function(),
    Function(),
    Call(),
    Call(0),
    Call(1),
    Call(2),
    Call(3),
    Call(4),
    Call(5),
    Call(),
    Call(0),
    Call(1),
    Call(2),
    Call(3),
    Call(4),
    Call(5),
    Save(),
    Restore(),
    # Print(),
    # Input(),
    IncrementRegister(),
    DecrementRegister(),
    IncrementTape(),
    DecrementTape(),
    IncrementRegister(),
    DecrementRegister(),
    IncrementTape(),
    DecrementTape(),
    Arithmetic(Arithmetic.ADD),
    Arithmetic(Arithmetic.SUBTRACT),
    Arithmetic(Arithmetic.MULTIPLY),
    Arithmetic(Arithmetic.DIVIDE),
    Arithmetic(Arithmetic.MODULO),
]

def gen_random_genome(length=100, depth=0, max_depth=5):
    if depth > 7:
        return [], 0
    total = 0
    genome = []
    for i in range(1000):
        if total >= length:
            return genome, total
        
        genome.append(random.randint(0, len(operations) - 1))
        total += 1

        if total >= length:
            return genome, total

        if random.random() < 0.5:
            gene, partial = gen_random_genome(length, depth + 1)
            genome.append(gene)
            total += partial
    return genome, total


# genome = Genome.random(operations, 25)
# print(genome)
# print(genome.into_operations())
# t1 = Tape()
# tm = TuringMachine(genome.into_operations())
# tm.run(t1)
# genome.mutate(0.05)

# t2 = Tape()
# tm = TuringMachine(genome.into_operations())
# tm.run(t2)
# print(genome)
# print(genome.into_operations())
# print(t1)
# print(t2)

GENOME_SIZE = 100
POPULATION_SIZE = 500
# combinator_set = [S(), K(), I(), Data(Point(0, 0)), Lambda(lambda point: Data(point.value.shift_by(1, 0))), Lambda(lambda point: Data(point.value.shift_by(0, 1)))]
genomes = [Genome.random(operations, random.randint(GENOME_SIZE//3, GENOME_SIZE)) for _ in range(POPULATION_SIZE)]
genomes.sort()
genomes = genomes[::-1]
print(list(map(lambda g: g.fitness(), genomes)))
try:
    for epoch in range(200):
        print(f"Epoch {epoch}")

        best_genomes = genomes[:POPULATION_SIZE//10]

        print(list(map(lambda g: g.fitness(), best_genomes)))
        # Create the next generation.
        # The first 10 genomes are the best genomes from the previous generation.
        genomes = deepcopy(best_genomes) + [Genome.random(operations, random.randint(GENOME_SIZE//3, GENOME_SIZE)) for _ in range(POPULATION_SIZE - len(best_genomes))]

        # Cross over the best genomes.
        for i in range(0, len(best_genomes), 2):
            child1, child2 = best_genomes[i].crossover(best_genomes[i + 1])
            genomes.append(child1)
            genomes.append(child2)

        # Cross over the best genomes.
        for i in range(0, len(best_genomes), 2):
            child = best_genomes[i].crossover_splits(best_genomes[i + 1])
            genomes.append(child)
        
        # Mutate the genomes.
        for genome in genomes:
            if random.random() < 0.5:
                new_genome = deepcopy(genome)
                new_genome.mutate(random.random() * 0.5)
                genomes.append(new_genome)

        genomes.extend(best_genomes)
        # Sort the genomes by fitness.
        genomes.sort()
        genomes = genomes[::-1]

        # print(list(map(lambda g: g.fitness(), genomes)))
        print(genomes[0].into_operations())
        print(genomes[0].evaluate())
except KeyboardInterrupt:
    genomes = best_genomes

# tm = TuringMachine(genome.into_operations())
# tape = Tape()
# tm.run(tape)
# print(tm.operations, tape)
# print(tm.operations, '\n =>', sum(tape.tape))