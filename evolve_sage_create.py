from evolve_sage_optimize import *
from scipy.stats import entropy

tm = SageVirtualMachine([
    Function('add', [
        Dereference([
            Restore(),
            Move('R'),
            Add(),
            PutInt()
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
        try:
            result = self.evaluate()
            tape = result.tape
            steps = result.steps
            # The fitness is the number of 1s in the tape.
            # return result.tape.count(1) * 1000 - self.get_size() * 10
            try:
                result = entropy(np.array(list(map(lambda x: min(x, 2.0 ** 16), result.tape)))).sum()
                if np.isnan(result):
                    return 0.0
            except:
                print(result)
                raise Exception("Entropy failed")
            return result / self.get_size()
        except Exception as e:
            return -1.0
        
    def evaluate(self):
        tape = Tape(100)
        tm = SageVirtualMachine(self.into_operations())
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
    ForLoop(),
    ForLoop(),
    Dereference(),
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
    Add(),
    Subtract(),
    Multiply(),
    Divide(),
    Remainder(),
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
POPULATION_SIZE = 300
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

ops = genomes[0].into_operations()
with open('entropy.py', 'w') as f:
    f.write(f'''from sage import *
import random

program = {ops}

number = input('Enter a number: ')

tm = SageVirtualMachine(program, [])
tape = Tape(1000)
tm.run(tape, 100000)
print(tape.tape)
''')
exit(0)