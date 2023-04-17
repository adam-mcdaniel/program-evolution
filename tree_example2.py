from treelib import Node, Tree

tree = Tree()
tree.create_node("", "zero")  # root node
tree.create_node("", "one", parent="zero")
tree.create_node("K", "K", parent="zero")


tree.create_node("I", "I", parent="one")
tree.create_node("S", "S", parent="one")


tree.show()

tree2 = Tree()
tree2.create_node("", "zero")  # root node
tree2.create_node("I", "I0", parent="zero")
tree2.create_node("", "one", parent="zero")

tree2.create_node("", "two", parent="one")
tree2.create_node("K", "K0", parent="two")
tree2.create_node("S", "S0", parent="two")

tree2.create_node("", "three", parent="one")
tree2.create_node("", "four", parent="three")
tree2.create_node("S", "S1", parent="three")

tree2.create_node("K", "K1", parent="four")
tree2.create_node("I", "i1", parent="four")

tree2.show()