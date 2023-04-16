

class Tape:
    def __init__(self, length=1000, blank_symbol=0, head_position=0):
        self.tape = [blank_symbol] * length
        self.head_position = head_position
        self.register = self.blank_symbol = blank_symbol
    
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
            raise TypeError("Direction must be a string ('l' or 'r') or signed integer (number of steps)")
    
    def set_head_position(self, position):
        self.head_position = position

    def get_head_position(self):
        return self.head_position
    
    def __str__(self):
        return str(self.tape)

    def __repr__(self):
        return str(self.tape)

    def __len__(self):
        return len(self.tape)

class TuringMachine:
    def __init__(self, operations):
        self.operations = operations
    
    def run(self, tape):
        for operation in self.operations:
            operation.apply(tape)

class Operation:
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

class Arithmetic(Operation):
    def __init__(self, operation):
        self.operation = operation
    
    def apply(self, tape):
        self.operation(tape.register, tape.get())

    def __str__(self):
        return super().__str__() + f"({self.operation.__name__})"

class Loop(Operation):
    def __init__(self, operations):
        self.operations = operations
    
    def apply(self, tape):
        while tape.register != 0:
            for operation in self.operations:
                operation.apply(tape)

class If(Operation):
    def __init__(self, operations):
        self.operations = operations
    
    def apply(self, tape):
        if tape.register != 0:
            for operation in self.operations:
                operation.apply(tape)

class Dereference(Operation):
    def __init__(self, operations):
        self.operations = operations
    
    def apply(self, tape):
        old_head = tape.get_head_position()
        new_head = tape.get()
        tape.move_head(new_head - old_head)
        for operation in self.operations:
            operation.apply(tape)
        tape.set_head_position(old_head)

class Print(Operation):
    def apply(self, tape):
        print(tape.register)

class Input(Operation):
    def apply(self, tape):
        tape.register = int(input("Input: "))

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

tm = TuringMachine([
    SetTape(1),
    Move('R'),
    SetRegister(2),
    Save(),
    Move('R'),
    SetTape(1),

    SetRegister(10),
    SetTape(100),
    Loop([
        Dereference([
            Save()
        ]),
        DecrementRegister(),
        IncrementTape(),
    ]),
    SetTape(0),
])

tape = Tape()
print(tape, tm.operations)
tm.run(tape)
print(tape, tm.operations)