from sage import *
import graphviz as gv
import pydot
import sage
from random import randint
def hsv_to_rgb(h, s, v):
    # This is taken from:
    # https://stackoverflow.com/questions/24852345/hsv-to-rgb-color-conversion
    if s == 0.0: return (v, v, v)
    i = int(h*6.) # XXX assume int() truncates!
    f = (h*6.)-i; p,q,t = v*(1.-s), v*(1.-s*f), v*(1.-s*(1.-f)); i%=6
    if i == 0: return (v, t, p)
    if i == 1: return (q, v, p)
    if i == 2: return (p, v, t)
    if i == 3: return (p, q, v)
    if i == 4: return (t, p, v)
    if i == 5: return (v, p, q)

class GraphNode:
    def __init__(self, operation, label=None, color=None, parents=None):
        self.label = label
        if label is None and type(operation) != list:
            self.label = str(operation)
        self.color = color
        self.cluster = None
        self.id = randint(2, 100000000000000) * randint(2, 100000000000000) * randint(2, 100000000000000)
        self.operation = operation
        
        self.next = None
        self.prev = None
        
        self.children = []
        self.parents = []
        self._graph = None
        self.is_root = True

        if parents:
            if type(parents) == list:
                for parent in parents:
                    self.add_parent(parent)
            else:
                self.add_parent(parents)

        match type(operation):
            case sage.WhileLoop:
                self.label = 'While'
                for op in operation.operations:
                    self.add_child(GraphNode(op, parents=self))
                # if self.children:
                #     self.id = self.children[0].id
            case sage.If:
                self.label = 'If'
                for op in operation.then_operations:
                    self.children.append(GraphNode(op, parents=self))
                # if self.children:
                #     self.id = self.children[0].id
            case sage.IfElse:
                self.label = 'IfElse'
                if operation.then_operations:
                    self.add_child(GraphNode(operation.then_operations, 'If', color='green', parents=self))
                if operation.else_operations:
                    self.add_child(GraphNode(operation.else_operations, 'Else', color='red', parents=self))

            case sage.Function:
                self.label = 'Function'
                for op in operation.operations:
                    self.add_child(GraphNode(op, parents=self))
            case _:
                if type(operation) == list:
                    for op in operation:
                        self.add_child(GraphNode(op, parents=self))
                    self.id = self.children[0].id

                else:
                    self.label = str(operation)
                    self.operation = operation

        if type(operation) != sage.IfElse:
            for prev, next in zip(self.children, self.children[1:]):
                prev.next = next
                next.prev = prev

    def add_child(self, child):
        if type(child) == list:
            if len(child) == 1:
                child = child[0]
            elif len(child) == 0:
                return

        child.is_root = False
        if child in self.children:
            return
        self.children.append(child)
        child.add_parent(self)
    
    def add_parent(self, parent):
        self.is_root = False
        if parent in self.parents:
            return

        self.parents.append(parent)
        parent.add_child(self)
    
    def graph(self):
        if self.is_root:
            self._graph = gv.Digraph(format='svg')
            # self._graph.attr(compound='true')
            self._graph.attr('node', shape='ellipse')
            self._graph.attr('node', style='filled')
            self._graph.attr(rank='same')
            self._graph.node('node_-1', label='ENTRY POINT', shape='diamond', color='yellow')
            self._graph.edge('node_-1', f'node_{self.id}', lhead=f'cluster_{self.id}')

        elif self.graph is None and self.parents:
            self._graph = self.parents[0]._graph
        # elif self.next:
        #     if self.next.cluster:
        #         self._graph.edge(f'node_{self.id}', f'node_{self.next.id}', lhead=f'cluster_{self.next.cluster}')
        #     else:
        #         self._graph.edge(f'node_{self.id}', f'node_{self.next.id}')

        match type(self.operation):
            case sage.WhileLoop:
                with self._graph.subgraph(name=f'cluster_{self.id}') as c:
                    c.attr(label=f'')
                    c.attr(color='magenta')
                    c.attr(style='filled')
                    c.node(f'node_{self.id}', label='While', color='yellow', shape='diamond')
                    for child in self.children:
                        child._graph = c
                        child.cluster = f'cluster_{self.id}'
                        child.graph()
                    if self.children:
                        c.edge(f'node_{self.id}', f'node_{self.children[0].id}', ltail=f'cluster_{self.id}', constraint='false')
                    else:
                        c.edge(f'node_{self.id}', f'node_{self.next.id}', ltail=f'cluster_{self.id}', constraint='false')
            case sage.If:
                with self._graph.subgraph(name=f'cluster_{self.id}') as c:
                    c.attr(label=f'')
                    c.attr(color='pink')
                    c.attr(style='filled')
                    c.node(f'node_{self.id}', label='If', color='yellow', shape='diamond')
                    for child in self.children:
                        child._graph = c
                        child.cluster = f'cluster_{self.id}'
                        child.graph()
                    if self.children:
                        c.edge(f'node_{self.id}', f'node_{self.children[0].id}', ltail=f'cluster_{self.id}', constraint='false')
                    else:
                        c.edge(f'node_{self.id}', f'node_{self.next.id}', ltail=f'cluster_{self.id}', constraint='false')
            
            case sage.IfElse:
                with self._graph.subgraph(name=f'cluster_{self.id}') as c:
                    c.attr(label=f'')
                    c.attr(color='blue')
                    c.attr(style='filled')
                    c.node(f'node_{self.id}', label=self.label, color='yellow', shape='diamond')
                    for child in self.children:
                        child._graph = c
                        child.cluster = f'cluster_{self.id}'
                        child.graph()
                        c.edge(f'node_{self.id}', f'node_{child.id}', ltail=f'cluster_{self.id}', constraint='false')

            case sage.Function:
                with self._graph.subgraph(name=f'cluster_{self.id}') as c:
                    c.attr(label=f'')
                    c.attr(color='lime')
                    c.attr(style='filled')
                    c.node(f'node_{self.id}', label="Function", color='yellow', shape='diamond')
                    c.node(f'node_{self.id+1}', label="Return", color='yellow', shape='diamond')
                    if self.children:
                        c.edge(f'node_{self.id}', f'node_{self.children[0].id}', ltail=f'cluster_{self.id}', constraint='false')
                        for child in self.children:
                            child._graph = c
                            child.cluster = f'cluster_{self.id}'
                            child.graph()
                        c.node(f'node_{self.id+1}', label="RETURN", color='yellow', shape='diamond')
                        c.edge(f'node_{self.children[-1].id}', f'node_{self.id+1}', ltail=f'cluster_{self.id}', constraint='false')
                    # if self.prev and self.next:
                    #     self._graph.edge(f'node_{self.prev.id}', f'node_{self.next.id}')
            case _:
                if type(self.operation) == list:
                    with self._graph.subgraph(name=f'cluster_{self.id}') as c:
                        r, g, b = hsv_to_rgb(random.randint(0, 360), 0.8, 0.8)
                        r = int(r * 255)
                        g = int(g * 255)
                        b = int(b * 255)
                        c.attr(color=f'#%02x%02x%02x' % (random.randint(0, 0xff), random.randint(0, 0xff), random.randint(0, 0xff)))
                        c.attr(style='filled')
                        if self.label:
                            c.attr(label=self.label)
                        for child in self.children:
                            child._graph = c
                            child.cluster = f'cluster_{self.id}'
                            child.graph()
                else:
                    self._graph.node(f'node_{self.id}', label=self.label, color=self.color)
                    for child in self.children:
                        child._graph = self._graph
                        child.graph()

        if self.next:
            if type(self.operation) == IfElse:
                if len(self.children) == 2:
                    self._graph.edge(f'node_{self.children[0].children[-1].id}', f'node_{self.next.id}', constraint='false')
                    self._graph.edge(f'node_{self.children[1].children[-1].id}', f'node_{self.next.id}', constraint='false')
                elif len(self.children) == 1:
                    self._graph.edge(f'node_{self.children[0].children[-1].id}', f'node_{self.next.id}', constraint='false')
                else:
                    self._graph.edge(f'node_{self.id}', f'node_{self.next.id}', constraint='false')
            elif type(self.operation) in [WhileLoop, If, list]:
                if len(self.children) >= 1:
                    self._graph.edge(f'node_{self.children[-1].id}', f'node_{self.next.id}', constraint='false')
                elif self.prev and self.next and type(self.operation) == list:
                    self._graph.edge(f'node_{self.prev.id}', f'node_{self.next.id}', constraint='false')
            else:
                # if self.cluster and self.next.cluster:
                #     self._graph.edge(f'node_{self.id}', f'node_{self.next.id}', ltail=self.next.cluster, lhead=self.next.cluster)
                # elif self.cluster:
                #     self._graph.edge(f'node_{self.id}', f'node_{self.next.id}', ltail=self.next.cluster)
                # elif self.next.cluster:
                #     self._graph.edge(f'node_{self.id}', f'node_{self.next.id}', lhead=self.cluster)
                # else:
                self._graph.edge(f'node_{self.id}', f'node_{self.next.id}')

        return self._graph

# class Graph:
#     def __init__(self, ops: list[Operation]):
#         # Create a GraphNode for the program.
#         self.root = GraphNode('Program')

# class Graph:
#     def __init__(self, ops: list[Operation]):
#         self.operations = ops
#         g = gv.Digraph(format='png')
#         g.attr(compound='true')
#         g.attr('node', shape='box')
#         self.fun_count = 0
#         self.result, _ = self.graph(ops, g)

#     def graph(self, ops, graph, i=0, j=0):
#         j_start = j
#         for op in ops:
#             match type(op):
#                 case sage.WhileLoop:
#                     with graph.subgraph(name=f'cluster_{i}_{j}') as c:
#                         c.attr(label=f'While')
#                         c.attr(color='blue')
#                         c.attr(style='filled')
#                         _, last = self.graph(op.operations, c, i+1, j)
#                         j = last[1]
#                 case sage.If:
#                     with g.subgraph(name=f'cluster_{i}_{j}') as c:
#                         c.attr(label=f'If')
#                         c.attr(color='yellow')
#                         c.attr(style='filled')
#                         _, last = self.graph(op.operations, c, i+1, j)
#                         j = last[1]
#                 case sage.IfElse:
                    
#                     with graph.subgraph(name=f'cluster_{i}_{j}') as ifelse_c:
#                         ifelse_c.attr(label=f'IfElse')
#                         ifelse_c.attr(color='yellow')
#                         ifelse_c.attr(style='filled')
#                         graph.node(f'node_{i}_{j}', label='IfElse')
#                         graph.edge(f'node_{i}_{j}', f'node_{i+1}_{0}', lhead=f'cluster_{i}_{j}_then')
#                         # graph.edge(f'node_{i}_{j}', f'node_{i+1}_{len(op.then_operations) + 1}', lhead=f'cluster_{i}_{j}_else')

#                         with ifelse_c.subgraph(name=f'cluster_{i}_{j}_then') as c:
#                             c.attr(label=f'If')
#                             c.attr(color='green')
#                             c.attr(style='filled')
#                             _, last_then = self.graph(op.then_operations, c, i+1, j)
                        
#                         with ifelse_c.subgraph(name=f'cluster_{i}_{j}_else') as c:
#                             c.attr(label=f'Else')
#                             c.attr(color='red')
#                             c.attr(style='filled')
#                             _, last_else = self.graph(op.else_operations, c, i+1, len(op.then_operations) + 1, j)
#                     # graph.edge(f'node_{last_then[0]+}_{last_then[1]}', f'node_{i}_{j}')
#                     # graph.edge(f'node_{last_then[0]}_{last_then[1]-1}', f'node_{i}_{j + 1}', ltail=f'cluster_{i}_{j}_then')
#                     # graph.edge(f'node_{last_else[0]}_{last_else[1]-1}', f'node_{i}_{j + 1}', ltail=f'cluster_{i}_{j}_else')
#                         # i += 1
#                     j = last_else[1]
#                     # graph.edge(f'cluster_{i}_{j}_then:{last_then[0]}', f'cluster_{i}_{j}_else:{last_else[0]}')
#                 case sage.Function:
#                     with graph.subgraph(name=f'cluster_{i}_{j}') as c:
#                         c.attr(label=f'Function #{self.fun_count}')
#                         self.fun_count += 1
#                         c.attr(color='magenta')
#                         c.attr(style='filled')
#                         _, last = self.graph(op.operations, c, i+1)
#                         j = last[1]
#                 case _:
#                     graph.node(f'node_{i}_{j}', label=str(op))
#                     if (j - j_start) < len(ops) - 1:
#                         graph.edge(f'node_{i}_{j}', f'node_{i}_{j+1}')
#             j += 1
#         return graph, (i, j)
    

# program = [Function(0, [MoveRight(3), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), MoveLeft(3), MoveRight(3), Save(), MoveLeft(3), MoveRight(2), Restore(), MoveLeft(2), MoveRight(3), Dereference(), Save(), Reference(), MoveLeft(3), Restore(), MoveRight(2), Save(), MoveLeft(2), MoveRight(2), Dereference(), Restore(), Reference(), MoveLeft(2), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), Reference(), Save(), Dereference(), Restore(), Reference(), MoveRight(4), Save(), MoveLeft(4), Dereference(), MoveLeft(1), Where(), Reference(), Save(), MoveRight(4), Restore(), MoveLeft(4), IfElse([MoveRight(2), Dereference(), Restore(), Reference(), MoveLeft(2), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), MoveRight(2), Dereference(), Restore(), Reference(), MoveLeft(2), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), SetRegister(1), Dereference(), Save(), Reference(), Dereference(), MoveLeft(1), Restore(), MoveRight(1), Reference(), Dereference(), Subtract(), Reference(), Dereference(), MoveLeft(1), Save(), MoveRight(1), Reference(), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), SetRegister(0), MoveRight(4), Save(), MoveLeft(4), MoveRight(4), Restore(), MoveLeft(4), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), Dereference(), Restore(), Reference(), MoveRight(4), Save(), MoveLeft(4), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), MoveRight(4), Restore(), MoveLeft(4), Call(), Dereference(), MoveLeft(1), Restore(), MoveRight(1), Reference(), Dereference(), Multiply(), Reference(), Dereference(), MoveLeft(1), Save(), MoveRight(1), Reference(), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save()], [Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), SetRegister(1), Dereference(), Save(), Reference()]), Dereference(), Restore(), Reference(), MoveRight(2), Dereference(), Save(), Reference(), MoveLeft(2), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), MoveRight(3), Dereference(), Restore(), Reference(), MoveLeft(3), MoveRight(2), Save(), MoveLeft(2), MoveRight(3), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), MoveLeft(3), MoveRight(3), Save(), MoveLeft(3)]), Allocate(), MoveRight(3), Save(), Add(), MoveLeft(1), Dereference(), Save(), GetInt(), Dereference(), Save(), Subtract(), MoveRight(1), Dereference(), Call(), Dereference(), Restore(), PutInt()]
program = [Function(0, [MoveRight(3), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), MoveLeft(3), MoveRight(3), Restore(), MoveLeft(3), MoveRight(2), Restore(), MoveLeft(2), MoveRight(3), Dereference(), Save(), Reference(), MoveLeft(3), Restore(), MoveRight(2), Save(), MoveLeft(2), MoveRight(2), Dereference(), Restore(), Reference(), MoveLeft(2), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), Dereference(), Restore(), Allocate(), Save(), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), SetRegister(0), Dereference(), Save(), Reference(), MoveRight(2), Dereference(), MoveRight(2), Restore(), MoveLeft(2), Reference(), MoveLeft(2), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), MoveRight(2), Dereference(), Restore(), IfElse([], []), Reference(), MoveLeft(2), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), Dereference(), MoveLeft(1), Restore(), MoveRight(1), Reference(), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), Restore(), Reference(), Dereference(), MoveLeft(1), Save(), MoveRight(1), Reference(), Dereference(), MoveLeft(1), Restore(), MoveRight(1), Reference(), Dereference(), MoveRight(1), Subtract(), MoveLeft(1), Reference(), Dereference(), MoveLeft(1), Save(), MoveRight(1), Reference(), Dereference(), MoveLeft(1), SetRegister(-1), Add(), Save(), MoveRight(1), Reference(), Dereference(), MoveLeft(1), Restore(), IsNonNegative(), Save(), MoveRight(1), Reference(), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), Dereference(), Restore(), Reference(), MoveRight(4), Save(), MoveLeft(4), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), MoveRight(4), Restore(), MoveLeft(4), WhileLoop([Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), GetInt(), Dereference(), Save(), Reference(), MoveRight(2), Dereference(), MoveRight(2), Restore(), MoveLeft(2), Reference(), MoveLeft(2), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), MoveRight(2), Dereference(), MoveRight(1), Restore(), MoveLeft(1), Reference(), MoveLeft(2), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), Dereference(), Restore(), Reference(), MoveRight(4), Save(), MoveLeft(4), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), Dereference(), Restore(), Reference(), MoveRight(5), Save(), MoveLeft(5), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), SetRegister(1), MoveRight(6), Save(), MoveLeft(6), MoveRight(5), Restore(), MoveLeft(5), MoveRight(6), Multiply(), MoveLeft(6), MoveRight(5), Save(), MoveLeft(5), MoveRight(4), Restore(), MoveLeft(4), MoveRight(5), Index(), MoveLeft(5), MoveRight(6), Save(), MoveLeft(6), MoveRight(6), Restore(), MoveLeft(6), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), Dereference(), Restore(), Reference(), MoveRight(4), Save(), MoveLeft(4), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), Dereference(), Restore(), Reference(), MoveRight(4), Dereference(), Save(), Reference(), MoveLeft(4), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), MoveRight(2), Restore(), MoveLeft(2), MoveRight(4), Save(), MoveLeft(4), SetRegister(2), MoveRight(5), Save(), MoveLeft(5), MoveRight(4), Restore(), MoveLeft(4), MoveRight(5), Index(), MoveLeft(5), MoveRight(6), Save(), MoveLeft(6), MoveRight(6), Restore(), MoveLeft(6), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), SetRegister(1), Dereference(), Save(), Reference(), MoveRight(2), Dereference(), MoveRight(3), Restore(), MoveLeft(3), Reference(), MoveLeft(2), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), Dereference(), Restore(), Reference(), MoveRight(4), Save(), MoveLeft(4), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), MoveRight(4), Dereference(), Restore(), Reference(), MoveLeft(4), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), SetRegister(1), Dereference(), Save(), Reference(), Dereference(), MoveLeft(1), Restore(), MoveRight(1), Reference(), Dereference(), Add(), Reference(), Dereference(), MoveLeft(1), Save(), MoveRight(1), Reference(), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), MoveRight(2), Dereference(), MoveRight(3), Restore(), MoveLeft(3), Reference(), MoveLeft(2), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), Dereference(), Restore(), Reference(), MoveRight(4), Save(), MoveLeft(4), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), Dereference(), Restore(), Reference(), MoveRight(4), Dereference(), Save(), Reference(), MoveLeft(4), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), MoveRight(2), Dereference(), MoveRight(2), Restore(), MoveLeft(2), Reference(), MoveLeft(2), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), MoveRight(2), Dereference(), Restore(), Reference(), MoveLeft(2), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), Dereference(), MoveLeft(1), Restore(), MoveRight(1), Reference(), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), Restore(), Reference(), Dereference(), MoveLeft(1), Save(), MoveRight(1), Reference(), Dereference(), MoveLeft(1), Restore(), MoveRight(1), Reference(), Dereference(), MoveRight(1), Subtract(), MoveLeft(1), Reference(), Dereference(), MoveLeft(1), Save(), MoveRight(1), Reference(), Dereference(), MoveLeft(1), SetRegister(-1), Add(), Save(), MoveRight(1), Reference(), Dereference(), MoveLeft(1), Restore(), IsNonNegative(), Save(), MoveRight(1), Reference(), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), Dereference(), Restore(), Reference(), MoveRight(4), Save(), MoveLeft(4), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), MoveRight(4), Restore(), MoveLeft(4)]), MoveRight(2), Dereference(), MoveRight(1), Restore(), MoveLeft(1), Reference(), MoveLeft(2), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), Dereference(), Restore(), Reference(), Dereference(), MoveLeft(1), Save(), MoveRight(1), Reference(), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), Dereference(), Restore(), Reference(), Dereference(), MoveLeft(1), Save(), MoveRight(1), Reference(), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), Dereference(), Restore(), Reference(), MoveRight(2), Dereference(), Save(), Reference(), MoveLeft(2), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), MoveRight(3), Dereference(), Restore(), Reference(), MoveLeft(3), MoveRight(2), Save(), MoveLeft(2), MoveRight(3), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), MoveLeft(3), MoveRight(3), Save(), MoveLeft(3)]), Function(1, [MoveRight(3), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), MoveLeft(3), MoveRight(3), Save(), MoveLeft(3), MoveRight(2), Restore(), MoveLeft(2), MoveRight(3), Dereference(), Save(), Reference(), MoveLeft(3), Restore(), MoveRight(2), Save(), MoveLeft(2), MoveRight(2), Dereference(), MoveLeft(1), Restore(), MoveRight(1), Reference(), MoveLeft(2), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), MoveRight(2), Dereference(), Restore(), Reference(), MoveLeft(2), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), Dereference(), MoveLeft(1), Restore(), MoveRight(1), Reference(), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), Restore(), Reference(), Dereference(), MoveLeft(1), Save(), MoveRight(1), Reference(), Dereference(), MoveLeft(1), Restore(), MoveRight(1), Reference(), Dereference(), MoveRight(1), Subtract(), MoveLeft(1), Reference(), Dereference(), MoveLeft(1), Save(), MoveRight(1), Reference(), Dereference(), MoveLeft(1), SetRegister(-1), Add(), Save(), MoveRight(1), Reference(), Dereference(), MoveLeft(1), Restore(), IsNonNegative(), Save(), MoveRight(1), Reference(), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), Dereference(), Restore(), Reference(), MoveRight(4), Save(), MoveLeft(4), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), MoveRight(4), Restore(), MoveLeft(4), IfElse([MoveRight(2), Dereference(), MoveLeft(2), Restore(), MoveRight(2), Reference(), MoveLeft(2), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), MoveRight(2), Dereference(), MoveLeft(1), Restore(), MoveRight(1), Reference(), MoveLeft(2), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), MoveRight(2), Dereference(), Restore(), Reference(), MoveLeft(2), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), SetRegister(2), MoveRight(4), Save(), MoveLeft(4), MoveRight(4), Restore(), MoveLeft(4), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), Dereference(), Restore(), Reference(), MoveRight(4), Save(), MoveLeft(4), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), MoveRight(4), Restore(), MoveLeft(4), Call(), MoveRight(2), Dereference(), MoveLeft(2), Restore(), MoveRight(2), Reference(), MoveLeft(2), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), MoveRight(2), Dereference(), MoveLeft(1), Restore(), MoveRight(1), Reference(), MoveLeft(2), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), MoveRight(2), Dereference(), MoveRight(1), Restore(), MoveLeft(1), Reference(), MoveLeft(2), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), SetRegister(1), Dereference(), Save(), Reference(), Dereference(), MoveLeft(1), Restore(), MoveRight(1), Reference(), Dereference(), Subtract(), Reference(), Dereference(), MoveLeft(1), Save(), MoveRight(1), Reference(), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), SetRegister(1), MoveRight(4), Save(), MoveLeft(4), MoveRight(4), Restore(), MoveLeft(4), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), Dereference(), Restore(), Reference(), MoveRight(4), Save(), MoveLeft(4), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), MoveRight(4), Restore(), MoveLeft(4), Call(), MoveRight(2), Dereference(), MoveLeft(2), Restore(), MoveRight(2), Reference(), MoveLeft(2), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), MoveRight(2), Dereference(), MoveRight(1), Restore(), MoveLeft(1), Reference(), MoveLeft(2), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), SetRegister(1), Dereference(), Save(), Reference(), Dereference(), MoveLeft(1), Restore(), MoveRight(1), Reference(), Dereference(), Add(), Reference(), Dereference(), MoveLeft(1), Save(), MoveRight(1), Reference(), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), MoveRight(2), Dereference(), Restore(), Reference(), MoveLeft(2), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), SetRegister(1), MoveRight(4), Save(), MoveLeft(4), MoveRight(4), Restore(), MoveLeft(4), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), Dereference(), Restore(), Reference(), MoveRight(4), Save(), MoveLeft(4), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), MoveRight(4), Restore(), MoveLeft(4), Call(), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save()], []), Dereference(), MoveLeft(3), Where(), MoveRight(3), Reference(), Save(), MoveRight(3), Dereference(), Restore(), Reference(), MoveLeft(3), MoveRight(2), Save(), MoveLeft(2), MoveRight(3), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), MoveLeft(3), MoveRight(3), Save(), MoveLeft(3)]), Function(2, [MoveRight(3), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), MoveLeft(3), MoveRight(3), Save(), MoveLeft(3), MoveRight(2), Restore(), MoveLeft(2), MoveRight(3), Dereference(), Save(), Reference(), MoveLeft(3), Restore(), MoveRight(2), Save(), MoveLeft(2), MoveRight(2), Dereference(), Restore(), Reference(), MoveLeft(2), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), MoveRight(2), Dereference(), MoveLeft(2), Restore(), MoveRight(2), Reference(), MoveLeft(2), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), Dereference(), Restore(), Reference(), MoveRight(4), Save(), MoveLeft(4), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), Dereference(), Restore(), Reference(), MoveRight(5), Save(), MoveLeft(5), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), SetRegister(1), MoveRight(6), Save(), MoveLeft(6), MoveRight(5), Restore(), MoveLeft(5), MoveRight(6), Multiply(), MoveLeft(6), MoveRight(5), Save(), MoveLeft(5), MoveRight(4), Restore(), MoveLeft(4), MoveRight(5), Index(), MoveLeft(5), MoveRight(6), Save(), MoveLeft(6), MoveRight(6), Dereference(), Restore(), Reference(), MoveLeft(6), Dereference(), MoveRight(1), Save(), Subtract(), SetRegister(0), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), MoveRight(2), Dereference(), MoveLeft(1), Restore(), MoveRight(1), Reference(), MoveLeft(2), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), SetRegister(1), Dereference(), Save(), Reference(), Dereference(), MoveLeft(1), Restore(), MoveRight(1), Reference(), Dereference(), Subtract(), Reference(), Dereference(), MoveLeft(1), Save(), MoveRight(1), Reference(), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), MoveRight(2), Dereference(), MoveLeft(1), Restore(), MoveRight(1), Reference(), MoveLeft(2), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), MoveRight(2), Dereference(), MoveRight(3), Restore(), MoveLeft(3), Reference(), MoveLeft(2), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), MoveRight(2), Dereference(), Restore(), Reference(), MoveLeft(2), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), Dereference(), MoveLeft(1), Restore(), MoveRight(1), Reference(), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), Restore(), Reference(), Dereference(), MoveLeft(1), Save(), MoveRight(1), Reference(), Dereference(), MoveLeft(1), Restore(), MoveRight(1), Reference(), Dereference(), MoveRight(1), Subtract(), MoveLeft(1), Reference(), Dereference(), MoveLeft(1), Save(), MoveRight(1), Reference(), Dereference(), MoveLeft(1), SetRegister(-1), Add(), Save(), MoveRight(1), Reference(), Dereference(), MoveLeft(1), Restore(), IsNonNegative(), Save(), MoveRight(1), Reference(), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), Dereference(), Restore(), Reference(), MoveRight(4), Save(), MoveLeft(4), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), MoveRight(4), Restore(), MoveLeft(4), WhileLoop([MoveRight(2), Dereference(), MoveRight(3), Restore(), MoveLeft(3), Reference(), MoveLeft(2), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), MoveRight(2), Dereference(), MoveLeft(2), Restore(), MoveRight(2), Reference(), MoveLeft(2), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), Dereference(), Restore(), Reference(), MoveRight(4), Save(), MoveLeft(4), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), Dereference(), Restore(), Reference(), MoveRight(5), Save(), MoveLeft(5), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), SetRegister(1), MoveRight(6), Save(), MoveLeft(6), MoveRight(5), Restore(), MoveLeft(5), MoveRight(6), Multiply(), MoveLeft(6), MoveRight(5), Save(), MoveLeft(5), MoveRight(4), Restore(), MoveLeft(4), MoveRight(5), Index(), MoveLeft(5), MoveRight(6), Save(), MoveLeft(6), MoveRight(6), Dereference(), Restore(), Reference(), MoveLeft(6), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), MoveRight(2), Dereference(), MoveRight(1), Restore(), MoveLeft(1), Reference(), MoveLeft(2), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), Dereference(), MoveLeft(1), Restore(), MoveRight(1), Reference(), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), Restore(), Reference(), Dereference(), MoveLeft(1), Save(), MoveRight(1), Reference(), Dereference(), MoveLeft(1), Restore(), MoveRight(1), Reference(), Dereference(), MoveRight(1), Subtract(), MoveLeft(1), Reference(), Dereference(), MoveLeft(1), Save(), MoveRight(1), Reference(), Dereference(), MoveLeft(1), Restore(), IsNonNegative(), Save(), MoveRight(1), Reference(), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), Dereference(), Restore(), Reference(), MoveRight(4), Save(), MoveLeft(4), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), MoveRight(4), Restore(), MoveLeft(4), IfElse([MoveRight(2), Restore(), MoveLeft(2), MoveRight(4), Save(), MoveLeft(4), SetRegister(2), MoveRight(5), Save(), MoveLeft(5), MoveRight(4), Restore(), MoveLeft(4), MoveRight(5), Index(), MoveLeft(5), MoveRight(6), Save(), MoveLeft(6), MoveRight(6), Restore(), MoveLeft(6), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), SetRegister(1), Dereference(), Save(), Reference(), MoveRight(2), Dereference(), MoveRight(4), Restore(), MoveLeft(4), Reference(), MoveLeft(2), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), Dereference(), Restore(), Reference(), MoveRight(4), Save(), MoveLeft(4), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), MoveRight(4), Dereference(), Restore(), Reference(), MoveLeft(4), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), SetRegister(1), Dereference(), Save(), Reference(), Dereference(), MoveLeft(1), Restore(), MoveRight(1), Reference(), Dereference(), Add(), Reference(), Dereference(), MoveLeft(1), Save(), MoveRight(1), Reference(), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), MoveRight(2), Dereference(), MoveRight(4), Restore(), MoveLeft(4), Reference(), MoveLeft(2), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), Dereference(), Restore(), Reference(), MoveRight(4), Save(), MoveLeft(4), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), Dereference(), Restore(), Reference(), MoveRight(4), Dereference(), Save(), Reference(), MoveLeft(4), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), MoveRight(2), Dereference(), MoveRight(3), Restore(), MoveLeft(3), Reference(), MoveLeft(2), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), MoveRight(2), Dereference(), MoveLeft(2), Restore(), MoveRight(2), Reference(), MoveLeft(2), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), Dereference(), Restore(), Reference(), MoveRight(4), Save(), MoveLeft(4), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), Dereference(), Restore(), Reference(), MoveRight(5), Save(), MoveLeft(5), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), SetRegister(1), MoveRight(6), Save(), MoveLeft(6), MoveRight(5), Restore(), MoveLeft(5), MoveRight(6), Multiply(), MoveLeft(6), MoveRight(5), Save(), MoveLeft(5), MoveRight(4), Restore(), MoveLeft(4), MoveRight(5), Index(), MoveLeft(5), MoveRight(6), Save(), MoveLeft(6), MoveRight(6), Restore(), MoveLeft(6), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), MoveRight(2), Dereference(), MoveRight(2), Restore(), MoveLeft(2), Reference(), MoveLeft(2), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), MoveRight(2), Dereference(), MoveLeft(2), Restore(), MoveRight(2), Reference(), MoveLeft(2), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), Dereference(), Restore(), Reference(), MoveRight(4), Save(), MoveLeft(4), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), Dereference(), Restore(), Reference(), MoveRight(5), Save(), MoveLeft(5), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), SetRegister(1), MoveRight(6), Save(), MoveLeft(6), MoveRight(5), Restore(), MoveLeft(5), MoveRight(6), Multiply(), MoveLeft(6), MoveRight(5), Save(), MoveLeft(5), MoveRight(4), Restore(), MoveLeft(4), MoveRight(5), Index(), MoveLeft(5), MoveRight(6), Save(), MoveLeft(6), MoveRight(6), Restore(), MoveLeft(6), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), SetRegister(3), MoveRight(4), Save(), MoveLeft(4), MoveRight(4), Restore(), MoveLeft(4), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), Dereference(), Restore(), Reference(), MoveRight(4), Save(), MoveLeft(4), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), MoveRight(4), Restore(), MoveLeft(4), Call()], []), MoveRight(2), Restore(), MoveLeft(2), MoveRight(4), Save(), MoveLeft(4), SetRegister(3), MoveRight(5), Save(), MoveLeft(5), MoveRight(4), Restore(), MoveLeft(4), MoveRight(5), Index(), MoveLeft(5), MoveRight(6), Save(), MoveLeft(6), MoveRight(6), Restore(), MoveLeft(6), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), SetRegister(1), Dereference(), Save(), Reference(), MoveRight(2), Dereference(), MoveRight(4), Restore(), MoveLeft(4), Reference(), MoveLeft(2), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), Dereference(), Restore(), Reference(), MoveRight(4), Save(), MoveLeft(4), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), MoveRight(4), Dereference(), Restore(), Reference(), MoveLeft(4), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), SetRegister(1), Dereference(), Save(), Reference(), Dereference(), MoveLeft(1), Restore(), MoveRight(1), Reference(), Dereference(), Add(), Reference(), Dereference(), MoveLeft(1), Save(), MoveRight(1), Reference(), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), MoveRight(2), Dereference(), MoveRight(4), Restore(), MoveLeft(4), Reference(), MoveLeft(2), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), Dereference(), Restore(), Reference(), MoveRight(4), Save(), MoveLeft(4), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), Dereference(), Restore(), Reference(), MoveRight(4), Dereference(), Save(), Reference(), MoveLeft(4), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), MoveRight(2), Dereference(), MoveRight(3), Restore(), MoveLeft(3), Reference(), MoveLeft(2), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), MoveRight(2), Dereference(), Restore(), Reference(), MoveLeft(2), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), Dereference(), MoveLeft(1), Restore(), MoveRight(1), Reference(), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), Restore(), Reference(), Dereference(), MoveLeft(1), Save(), MoveRight(1), Reference(), Dereference(), MoveLeft(1), Restore(), MoveRight(1), Reference(), Dereference(), MoveRight(1), Subtract(), MoveLeft(1), Reference(), Dereference(), MoveLeft(1), Save(), MoveRight(1), Reference(), Dereference(), MoveLeft(1), SetRegister(-1), Add(), Save(), MoveRight(1), Reference(), Dereference(), MoveLeft(1), Restore(), IsNonNegative(), Save(), MoveRight(1), Reference(), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), Dereference(), Restore(), Reference(), MoveRight(4), Save(), MoveLeft(4), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), MoveRight(4), Restore(), MoveLeft(4)]), MoveRight(2), Dereference(), MoveRight(2), Restore(), MoveLeft(2), Reference(), MoveLeft(2), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), SetRegister(1), Dereference(), Save(), Reference(), Dereference(), MoveLeft(1), Restore(), MoveRight(1), Reference(), Dereference(), Add(), Reference(), Dereference(), MoveLeft(1), Save(), MoveRight(1), Reference(), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), MoveRight(2), Dereference(), MoveLeft(2), Restore(), MoveRight(2), Reference(), MoveLeft(2), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), Dereference(), Restore(), Reference(), MoveRight(4), Save(), MoveLeft(4), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), Dereference(), Restore(), Reference(), MoveRight(5), Save(), MoveLeft(5), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), SetRegister(1), MoveRight(6), Save(), MoveLeft(6), MoveRight(5), Restore(), MoveLeft(5), MoveRight(6), Multiply(), MoveLeft(6), MoveRight(5), Save(), MoveLeft(5), MoveRight(4), Restore(), MoveLeft(4), MoveRight(5), Index(), MoveLeft(5), MoveRight(6), Save(), MoveLeft(6), MoveRight(6), Restore(), MoveLeft(6), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), MoveRight(2), Dereference(), Restore(), Reference(), MoveLeft(2), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), MoveRight(2), Dereference(), MoveLeft(2), Restore(), MoveRight(2), Reference(), MoveLeft(2), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), Dereference(), Restore(), Reference(), MoveRight(4), Save(), MoveLeft(4), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), Dereference(), Restore(), Reference(), MoveRight(5), Save(), MoveLeft(5), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), SetRegister(1), MoveRight(6), Save(), MoveLeft(6), MoveRight(5), Restore(), MoveLeft(5), MoveRight(6), Multiply(), MoveLeft(6), MoveRight(5), Save(), MoveLeft(5), MoveRight(4), Restore(), MoveLeft(4), MoveRight(5), Index(), MoveLeft(5), MoveRight(6), Save(), MoveLeft(6), MoveRight(6), Restore(), MoveLeft(6), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), SetRegister(3), MoveRight(4), Save(), MoveLeft(4), MoveRight(4), Restore(), MoveLeft(4), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), Dereference(), Restore(), Reference(), MoveRight(4), Save(), MoveLeft(4), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), MoveRight(4), Restore(), MoveLeft(4), Call(), MoveRight(2), Dereference(), MoveRight(2), Restore(), MoveLeft(2), Reference(), MoveLeft(2), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), SetRegister(1), Dereference(), Save(), Reference(), Dereference(), MoveLeft(1), Restore(), MoveRight(1), Reference(), Dereference(), Add(), Reference(), Dereference(), MoveLeft(1), Save(), MoveRight(1), Reference(), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), Dereference(), Restore(), Reference(), Dereference(), MoveLeft(1), Save(), MoveRight(1), Reference(), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), Dereference(), Restore(), Reference(), Dereference(), MoveLeft(1), Save(), MoveRight(1), Reference(), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), Dereference(), Restore(), Reference(), Dereference(), MoveLeft(1), Save(), MoveRight(1), Reference(), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), Dereference(), Restore(), Reference(), MoveRight(2), Dereference(), MoveLeft(2), Save(), MoveRight(2), Reference(), MoveLeft(2), Dereference(), MoveLeft(3), Where(), MoveRight(3), Reference(), Save(), MoveRight(3), Dereference(), Restore(), Reference(), MoveLeft(3), MoveRight(2), Save(), MoveLeft(2), MoveRight(3), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), MoveLeft(3), MoveRight(3), Save(), MoveLeft(3)]), Function(3, [MoveRight(3), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), MoveLeft(3), MoveRight(3), Save(), MoveLeft(3), MoveRight(2), Restore(), MoveLeft(2), MoveRight(3), Dereference(), Save(), Reference(), MoveLeft(3), Restore(), MoveRight(2), Save(), MoveLeft(2), MoveRight(2), Dereference(), MoveLeft(1), Restore(), MoveRight(1), Reference(), MoveLeft(2), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), Dereference(), Restore(), Reference(), MoveRight(4), Save(), MoveLeft(4), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), MoveRight(4), Dereference(), Restore(), Reference(), MoveLeft(4), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), MoveRight(2), Dereference(), Restore(), Reference(), MoveLeft(2), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), Dereference(), Restore(), Reference(), MoveRight(4), Save(), MoveLeft(4), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), MoveRight(4), Dereference(), Restore(), Reference(), MoveLeft(4), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), MoveRight(2), Dereference(), MoveLeft(1), Restore(), MoveRight(1), Reference(), MoveLeft(2), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), Dereference(), Restore(), Reference(), MoveRight(4), Save(), MoveLeft(4), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), Dereference(), Restore(), Reference(), MoveRight(4), Dereference(), Save(), Reference(), MoveLeft(4), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), MoveRight(2), Dereference(), MoveRight(1), Restore(), MoveLeft(1), Reference(), MoveLeft(2), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), MoveRight(2), Dereference(), Restore(), Reference(), MoveLeft(2), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), Dereference(), Restore(), Reference(), MoveRight(4), Save(), MoveLeft(4), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), Dereference(), Restore(), Reference(), MoveRight(4), Dereference(), Save(), Reference(), MoveLeft(4), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), Dereference(), MoveLeft(2), Where(), MoveRight(2), Reference(), Save(), MoveRight(3), Dereference(), Restore(), Reference(), MoveLeft(3), MoveRight(2), Save(), MoveLeft(2), MoveRight(3), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), MoveLeft(3), MoveRight(3), Save(), MoveLeft(3)]), MoveRight(9), Where(), MoveLeft(9), MoveRight(3), Save(), MoveLeft(3), MoveRight(3), Dereference(), MoveRight(2048), Where(), Reference(), MoveLeft(3), Save(), Restore(), MoveRight(2), Save(), MoveLeft(2), Dereference(), MoveRight(1), Where(), Reference(), Save(), GetInt(), Dereference(), Save(), Reference(), MoveRight(2), Dereference(), MoveRight(1), Restore(), Reference(), MoveLeft(2), Dereference(), MoveRight(1), Save(), Reference(), Dereference(), MoveRight(1), Where(), Reference(), Reference(), Save(), MoveRight(4), Where(), MoveRight(1), Save(), SetRegister(0), Dereference(), MoveRight(1), Reference(), Save(), MoveRight(1), Restore(), Reference(), MoveRight(4), MoveLeft(4), Dereference(), Where(), MoveRight(1), Reference(), Save(), MoveRight(4), Restore(), MoveLeft(4), Call(), Dereference(), MoveRight(1), Where(), Reference(), Save(), SetRegister(0), Dereference(), Save(), Function(None, []), MoveRight(1), Reference(), Dereference(), MoveRight(1), Index(), Where(), Reference(), Save(), Dereference(), MoveRight(1), Where(), Reference(), Save(), SetRegister(0), Dereference(), Save(), Reference(), MoveRight(2), Divide(), MoveLeft(1), Reference(), PutChar(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), SetRegister(1), Dereference(), Save(), Reference(), Dereference(), MoveLeft(1), Restore(), MoveRight(1), Reference(), Dereference(), Subtract(), Reference(), Dereference(), MoveLeft(1), Save(), Reference(), Dereference(), MoveLeft(1), Where(), Reference(), Save(), MoveRight(4), MoveRight(4), MoveRight(4), Divide(), Subtract(), Dereference(), Dereference(), MoveRight(1), GetInt(), Where(), Reference(), Save(), Dereference(), Restore(), Reference(), MoveRight(4), Save(), MoveLeft(4), Dereference(), MoveLeft(1), Where(), Reference(), Save(), MoveRight(4), Restore(), MoveLeft(4), Call(), GetChar(), WhileLoop([]), Reference(), MoveLeft(2), MoveLeft(1), Restore(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), Reference(), Save(), MoveRight(2), Dereference(), MoveLeft(1), Reference(), MoveLeft(2), Dereference(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), IfElse([], []), Restore(), IfElse([], []), Dereference(), MoveLeft(1), Reference(), SetRegister(0), If([]), Divide(), Subtract(), Reference(), If([SetRegister(0)]), Reference(), Dereference(), MoveRight(1), MoveLeft(1), Reference(), Function(None, []), MoveLeft(1), MoveRight(1), Function(None, []), MoveLeft(1), Add(), SetRegister(1), Reference(), Dereference(), Function(None, []), Reference(), Dereference(), MoveLeft(1), Where(), Reference(), Save(), Dereference(), SetRegister(-1), SetRegister(1), Reference(), MoveRight(4), Save(), MoveLeft(4), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), MoveRight(4), MoveLeft(4), WhileLoop([MoveRight(2), Dereference(), MoveRight(3), Restore(), MoveLeft(3), Reference(), MoveLeft(2), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), MoveRight(2), Dereference(), MoveRight(2), Restore(), MoveLeft(2), Reference(), MoveLeft(2), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), Dereference(), Restore(), Reference(), MoveRight(4), Save(), MoveLeft(4), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), Dereference(), Restore(), Reference(), MoveRight(5), Save(), MoveLeft(5), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), SetRegister(1), MoveRight(6), Save(), MoveLeft(6), MoveRight(5), Restore(), MoveLeft(5), MoveRight(6), Multiply(), MoveLeft(6), MoveRight(5), Save(), MoveLeft(5), MoveRight(4), Restore(), MoveLeft(4), MoveRight(5), Index(), MoveLeft(5), MoveRight(6), Save(), MoveLeft(6), MoveRight(6), Dereference(), Restore(), Reference(), MoveLeft(6), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), Dereference(), Restore(), Reference(), PutInt(), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), MoveRight(2), Restore(), MoveLeft(2), MoveRight(4), Save(), MoveLeft(4), SetRegister(3), MoveRight(5), Save(), MoveLeft(5), MoveRight(4), Restore(), MoveLeft(4), MoveRight(5), Index(), MoveLeft(5), MoveRight(6), Save(), MoveLeft(6), MoveRight(6), Restore(), MoveLeft(6), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), SetRegister(1), Dereference(), Save(), Reference(), MoveRight(2), Dereference(), MoveRight(4), Restore(), MoveLeft(4), Reference(), MoveLeft(2), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), Dereference(), Restore(), Reference(), MoveRight(4), Save(), MoveLeft(4), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), MoveRight(4), Dereference(), Restore(), Reference(), MoveLeft(4), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), SetRegister(1), Dereference(), Save(), Reference(), Dereference(), MoveLeft(1), Restore(), MoveRight(1), Reference(), Dereference(), Add(), Reference(), Dereference(), MoveLeft(1), Save(), MoveRight(1), Reference(), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), MoveRight(2), Dereference(), MoveRight(4), Restore(), MoveLeft(4), Reference(), MoveLeft(2), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), Dereference(), Restore(), Reference(), MoveRight(4), Save(), MoveLeft(4), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), Dereference(), Restore(), Reference(), MoveRight(4), Dereference(), Save(), Reference(), MoveLeft(4), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), MoveRight(2), Dereference(), MoveRight(3), Restore(), MoveLeft(3), Reference(), MoveLeft(2), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), MoveRight(2), Dereference(), MoveRight(1), Restore(), MoveLeft(1), Reference(), MoveLeft(2), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), MoveRight(1), Where(), MoveLeft(1), Reference(), Save(), Dereference(), MoveLeft(1), Restore(), MoveRight(1), Reference(), Dereference(), MoveRight(1), Save(), MoveLeft(1), Reference(), Dereference(), Restore(), Reference(), Dereference(), MoveLeft(1), Save(), MoveRight(1), Reference(), Dereference(), MoveLeft(1), Restore(), MoveRight(1), Reference(), Dereference(), MoveRight(1), Subtract(), MoveLeft(1), Reference(), Dereference(), MoveLeft(1), Save(), MoveRight(1), Reference(), Dereference(), MoveLeft(1), SetRegister(-1), Add(), Save(), MoveRight(1), Reference(), Dereference(), MoveLeft(1), Restore(), IsNonNegative(), Save(), MoveRight(1), Reference(), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), Dereference(), Restore(), Reference(), MoveRight(4), Save(), MoveLeft(4), Dereference(), MoveLeft(1), Where(), MoveRight(1), Reference(), Save(), MoveRight(4), Restore(), MoveLeft(4)]), Where(), Subtract(), Save(), Restore(), MoveLeft(1), MoveRight(1), Reference(), Save(), Multiply(), MoveLeft(1), Where(), Reference(), If([]), Divide(), Dereference(), GetInt(), SetRegister(1)]
g = GraphNode(program)
g.graph().render('graph')
# g = Graph(program)
# g.result.render('graph')