from PrettyPrint import PrettyPrintTree


class Tree:
    def __init__(self, value):
        self.val = value
        self.children = []

    def add_child(self, child):
        self.children.append(child)
        return child


pt = PrettyPrintTree(lambda x: x.children, lambda x: x.val)
tree = Tree("")
child1 = tree.add_child(Tree(""))
child2 = tree.add_child(Tree("K"))
child1.add_child(Tree("I"))
child1.add_child(Tree("S"))
pt(tree)

print("\n")
pt2 = PrettyPrintTree(lambda x: x.children, lambda x: x.val)
tree2 = Tree("/\\")
I = tree2.add_child(Tree("I"))
one = tree2.add_child(Tree("/\\"))
two = one.add_child(Tree("/\\"))
three = one.add_child(Tree("/\\"))
three.add_child(Tree("S"))
three.add_child(Tree("K"))
two.add_child(Tree("S"))
four = two.add_child(Tree("/\\"))
four.add_child(Tree("K"))
four.add_child(Tree("I"))
pt2(tree2)