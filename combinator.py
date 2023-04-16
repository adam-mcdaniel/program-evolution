from copy import deepcopy
from sys import setrecursionlimit
import numpy as np
from leap_ec import Individual, context
from leap_ec import ops, util
from leap_ec.decoder import IdentityDecoder

# from leap_ec.real_rep.problems import SpheroidProblem, plot_2d_problem
# from leap_ec.real_rep.ops import mutate_gaussian
# from leap_ec.real_rep.initializers import create_real_vector, create_int_vector
from leap_ec.int_rep.initializers import create_int_vector

from leap_ec.algorithm import generational_ea
from leap_ec.probe import CartesianPhenotypePlotProbe, BestSoFarProbe, FitnessPlotProbe

setrecursionlimit(5000)

class Combinator:
    RECURSION_LIMIT = 100

    def __init__(self, *args):
        self.args = list(args)
        self.depth = 0

    def __getitem__(self, index):
        return self.args[index]

    def __setitem__(self, index, value):
        self.args[index] = value

    def set_depth(self, depth):
        self.depth = depth

    def num_required_args(self):
        raise NotImplementedError

    def apply(self, args, depth=0):
        raise NotImplementedError

    def clone(self):
        return deepcopy(self)

    def __call__(self, *args):
        if self.depth > self.RECURSION_LIMIT:
            raise RecursionError("Maximum recursion depth exceeded for Combinator", self.__class__.__name__, self.args, self.depth)

        result = self.clone()

        for arg in args:
            if not isinstance(arg, Combinator):
                raise TypeError(f"Expected Combinator, got {type(arg)}")
            result.args.append(arg.clone())

        if len(result.args) < result.num_required_args():
            return result

        result.set_depth(result.depth + 1)
        for arg in result.args:
            arg.set_depth(result.depth + 1)

        if len(result.args) == result.num_required_args():
            return result.clone().apply(result.args)
        else:
            return result.clone().apply(result.args[:result.num_required_args()]).clone()(*result.args[result.num_required_args():])

    def __repr__(self):
        return f"{self.__class__.__name__}({', '.join(map(repr, self.args))})"

    def __str__(self):
        return self.__repr__()

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.args == other.args
    
    def __hash__(self):
        return hash((self.__class__, tuple(self.args)))


class Data(Combinator):
    def __init__(self, value):
        super().__init__()
        self.value = value

    def num_required_args(self):
        return 1

    def apply(self, args):
        return self

    def clone(self):
        result = super().clone()
        result.value = deepcopy(self.value)
        return result

    def __add__(self, other):
        if isinstance(other, Data):
            return Data(self.value + other.value)
        else:
            return Data(self.value + other)

    def __sub__(self, other):
        if isinstance(other, Data):
            return Data(self.value - other.value)
        else:
            return Data(self.value - other)
    
    def __mul__(self, other):
        if isinstance(other, Data):
            return Data(self.value * other.value)
        else:
            return Data(self.value * other)

    def __truediv__(self, other):
        if isinstance(other, Data):
            return Data(self.value / other.value)
        else:
            return Data(self.value / other)

    def __floordiv__(self, other):
        if isinstance(other, Data):
            return Data(self.value // other.value)
        else:
            return Data(self.value // other)

    def __mod__(self, other):
        if isinstance(other, Data):
            return Data(self.value % other.value)
        else:
            return Data(self.value % other)

    def __pow__(self, other):
        if isinstance(other, Data):
            return Data(self.value ** other.value)
        else:
            return Data(self.value ** other)

    def __lshift__(self, other):
        if isinstance(other, Data):
            return Data(self.value << other.value)
        else:
            return Data(self.value << other)

    def __rshift__(self, other):
        if isinstance(other, Data):
            return Data(self.value >> other.value)
        else:
            return Data(self.value >> other)

    def __and__(self, other):
        if isinstance(other, Data):
            return Data(self.value & other.value)
        else:
            return Data(self.value & other)

    def __or__(self, other):
        if isinstance(other, Data):
            return Data(self.value | other.value)
        else:
            return Data(self.value | other)

    def __xor__(self, other):
        if isinstance(other, Data):
            return Data(self.value ^ other.value)
        else:
            return Data(self.value ^ other)

    def __neg__(self):
        return Data(-self.value)
    
    def __pos__(self):
        return Data(+self.value)
    
    def __abs__(self):
        return Data(abs(self.value))
    
    def __invert__(self):
        return Data(~self.value)

    def __lt__(self, other):
        if isinstance(other, Data):
            return self.value < other.value
        else:
            return self.value < other
    
    def __le__(self, other):
        if isinstance(other, Data):
            return self.value <= other.value
        else:
            return self.value <= other

    def __eq__(self, other):
        if isinstance(other, Data):
            return self.value == other.value
        else:
            return self.value == other

    def __ne__(self, other):
        if isinstance(other, Data):
            return self.value != other.value
        else:
            return self.value != other

    def __gt__(self, other):
        if isinstance(other, Data):
            return self.value > other.value
        else:
            return self.value > other

    def __ge__(self, other):
        if isinstance(other, Data):
            return self.value >= other.value
        else:
            return self.value >= other

    def __repr__(self):
        return f"Data({self.value})"
    
    def __str__(self):
        return str(self.value)

    def __hash__(self):
        return hash((self.__class__.__name__, self.value))


class Lambda(Combinator):
    def __init__(self, function, num_args=1):
        super().__init__()
        self.function = function
        self.num_args = num_args

    def clone(self):
        result = super().clone()
        result.value = deepcopy(self.function)
        result.num_args = self.num_args
        return result

    def num_required_args(self):
        return self.num_args

    def apply(self, args):
        return self.function(*args)

    def __repr__(self):
        return f"Lambda({self.function.__name__})"

    def __hash__(self):
        return hash((self.__class__.__name__, self.function))





class S(Combinator):
    def num_required_args(self):
        return 3

    def apply(self, args):
        x = args[0]
        y = args[1]
        z = args[2]
        z2 = z.clone()
        return x(z)(y(z2))

class K(Combinator):
    def num_required_args(self):
        return 2

    def apply(self, args):
        return args[0]

class I(Combinator):
    def num_required_args(self):
        return 1
        
    def apply(self, args):
        return args[0]

s = S()
k = K()
i = I()


assert s(k, i, i) == i
assert s(k)(i)(k(i)(s))(i) == i
assert k(k, s, i) == k(i)









def increment(x):
    return x + 1

assert s(k, i, i)(Lambda(increment))(Data(5)) == Data(6)


class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def shift_by(self, x, y):
        return Point(self.x + x, self.y + y)

    def __repr__(self):
        return f"Point({self.x}, {self.y})"

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __hash__(self):
        return hash((self.x, self.y))
        
assert s(k, i, i)(Lambda(lambda point: Data(point.value.shift_by(1, 0))))(Data(Point(5, 6))) == Data(Point(6, 6))


import random

# We are going to evolve SKI combinator programs.
# This will be the representation of a program.
class CombinatorGene:
    def __init__(self, combinator):
        self.combinator = combinator

    def __repr__(self):
        return f"{self.combinator}"

    def clone(self):
        return CombinatorGene(self.combinator.clone())

    def random(combinator_set=[S(), K(), I()]):
        return CombinatorGene(random.choice(combinator_set))

    def mutate(self, combinator_set=[S(), K(), I()]):
        result = random.random()
        # Randomly mutate into another combinator or into an application.
        if result < 0.5:
            return CombinatorGene.random()
        else:
            return ApplicationGene()

    def __hash__(self):
        return hash(self.combinator)

class ApplicationGene:
    def __repr__(self):
        return f"Apply"

    def clone(self):
        return ApplicationGene()

    def mutate(self, combinator_set=[S(), K(), I()]):
        return CombinatorGene(random.choice(combinator_set))

    def __hash__(self):
        return hash("Apply")

class NothingGene:
    def __repr__(self):
        return f"Nothing"

    def clone(self):
        return NothingGene()

    def mutate(self, combinator_set=[S(), K(), I()]):
        return CombinatorGene(random.choice(combinator_set))

    def __hash__(self):
        return hash("Nothing")


class Genome:
    def __init__(self, genes, combinator_set=[S(), K(), I()]):
        self.genes = genes
        self.combinator_set = combinator_set

    def random(length=10, combinator_set=[S(), K(), I()]):
        result = Genome([CombinatorGene.random() for _ in range(length)], combinator_set)
        for _ in range(10):
            result.mutate()
        return result

    def encode(self):
        # Encode the genome as a list of numbers
        # Assign a number to each combinator.
        combinator_to_number = {combinator: i for i, combinator in enumerate(self.combinator_set)}

        # For each gene, encode it as a number.
        return [combinator_to_number[gene.combinator] if isinstance(gene, CombinatorGene) else len(combinator_to_number) for gene in self.genes]
        
    def decode(genes, combinator_set=[S(), K(), I()]):
        # Decode the genome from a list of numbers.
        # Assign a number to each combinator.
        combinator_to_number = {combinator: i for i, combinator in enumerate(combinator_set)}

        # For each gene, encode it as a number.
        return Genome([CombinatorGene(combinator_set[gene]) if gene < len(combinator_to_number) else ApplicationGene() for gene in genes], combinator_set)

    def fitness(self):
        # Evaluate the program.
        result = self.evaluate()
        # Is the result a Data object?
        if isinstance(result, Data):
            # Is the result a Point?
            if isinstance(result.value, Point):
                # Maximize the distance from the origin.
                return result.value.x ** 2 + result.value.y ** 2
            else:
                return size(self.as_tree())
        else:
            return -1

    def __lt__(self, other):
        return self.fitness() < other.fitness()

    def __repr__(self):
        return f"Genome({self.genes})"
    
    def from_combinators(combinator_set=[S(), K(), I()], size=50):
        return Genome([CombinatorGene.random(combinator_set) for _ in range(size)], combinator_set)

    def random_gene(self):
        return random.choice([NothingGene(), ApplicationGene(), CombinatorGene.random(self.combinator_set)])

    def clone(self):
        return Genome([gene.clone() for gene in self.genes])

    def insert_random_gene(self):
        index = random.randint(0, len(self.genes) - 1)
        self.genes.insert(index, self.random_gene())

    def remove_random_gene(self):
        if len(self.genes) < 2:
            return
        index = random.randint(0, len(self.genes) - 1)
        self.genes.pop(index)

    def mutate(self):
        if random.random() < 0.5:
            if random.random() < 0.5:
                self.insert_random_gene()
            else:
                self.remove_random_gene()
        else:
            # Randomly mutate a gene.
            index = random.randint(0, len(self.genes) - 1)
            self.genes[index] = self.genes[index].mutate(self.combinator_set)


    def crossover(self, other):
        # Randomly select a crossover point.
        index = random.randint(0, len(self.genes) - 1)
        # Create two new genomes by swapping the genes after the crossover point.
        return Genome(self.genes[:index] + other.genes[index:], self.combinator_set), Genome(other.genes[:index] + self.genes[index:], self.combinator_set)

    def evaluate(self):
        # Evaluate the program.
        stack = []
        for gene in self.genes:
            if isinstance(gene, CombinatorGene):
                stack.append(gene.combinator)
            elif isinstance(gene, ApplicationGene):
                try:
                    f = stack.pop()
                    x = stack.pop()
                    stack.append(f(*x))
                except:
                    return None
        # The result should be at the top of the stack.
        if len(stack) != 1:
            return None
        return stack.pop()
    
    def as_tree(self):
        # Generate a tree representation of the program.
        # The output is a list of lists.
        # The first element is the root node.
        # The second element is a list of the children of the root node.
        # The third element is a list of the children of the children of the root node.
        # And so on.
        stack = []
        for gene in self.genes:
            if isinstance(gene, CombinatorGene):
                stack.append([gene.combinator])
            elif isinstance(gene, ApplicationGene):
                # Pop the last two elements off the stack.
                # The second element is the left child.
                # The first element is the right child.
                # The result is the parent.
                try:
                    f = stack.pop()
                    x = stack.pop()
                    stack.append([gene, f, x])
                except:
                    return None
        return stack.pop()

def size(l):
    if isinstance(l, list):
        return 1 + sum(size(item) for item in l)
    else:
        return 0

genome = Genome([
    # Postfix notation.  k(k)(s)(i) -> i s k k
    CombinatorGene(I()),
    CombinatorGene(S()),
    CombinatorGene(K()),
    CombinatorGene(K()),
    ApplicationGene(),
    ApplicationGene(),
    ApplicationGene(),
])


# encoding = genome.encode()
# h = max(encoding)
# l = min(encoding)
# for _ in range(10):
#     genome = Genome.decode(create_int_vector([(l, h)] * 100)())
#     print(genome.as_tree())
#     print(Genome.decode(create_int_vector([(l, h)] * 100)()).evaluate())

# print([Genome.random() for _ in range(10)])
GENOME_SIZE = 10
POPULATION_SIZE = 10000
combinator_set = [S(), K(), I(), Data(Point(0, 0)), Lambda(lambda point: Data(point.value.shift_by(1, 0))), Lambda(lambda point: Data(point.value.shift_by(0, 1)))]
genomes = [Genome.random(GENOME_SIZE, combinator_set) for _ in range(POPULATION_SIZE)]
genomes.sort()
genomes = genomes[::-1]
print(list(map(lambda g: g.fitness(), genomes)))

for epoch in range(1000):
    print(f"Epoch {epoch}")

    best_genomes = genomes[:POPULATION_SIZE//10]

    print(list(map(lambda g: g.fitness(), best_genomes)))
    # Create the next generation.
    # The first 10 genomes are the best genomes from the previous generation.
    genomes = deepcopy(best_genomes) + [Genome.random(GENOME_SIZE, combinator_set) for _ in range(POPULATION_SIZE - len(best_genomes))]

    # Cross over the best genomes.
    for i in range(0, len(best_genomes), 2):
        child1, child2 = best_genomes[i].crossover(best_genomes[i + 1])
        genomes.append(child1)
        genomes.append(child2)
    
    # Mutate the genomes.
    for genome in genomes:
        genome.mutate()

    genomes.extend(best_genomes)
    # Sort the genomes by fitness.
    genomes.sort()
    genomes = genomes[::-1]

print(list(map(lambda g: g.fitness(), genomes)))