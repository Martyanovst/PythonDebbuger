import bytecode
import re
import sys
import inspect


class Debugger:

    def __init__(self):
        self.line_pattern = re.compile(r'lineno=(\d+)')
        self.call_function_pattern = re.compile(r'CALL_FUNCTION arg=(\d+?) ')
        self.make_function_pattern = re.compile(r'MAKE_FUNCTION')
        self.load_name_pattern = re.compile(r'LOAD_NAME arg=\'(.+?)\' ')
        self.compiled_object_pattern = re.compile(r'LOAD_CONST arg=(<code object (.+?) at .+?>)')
        self.breakpoints = set()
        self.is_running = True
        self.step_into = False
        self.watch = {}
        self.last_line = 1
        self.call_stack = []
        self.debug_functions_names = {'self.debug_function', 'self.debug_func', 'debug', 'open', 'run'}

    def open(self, file, path, wait_event, print_event):
        self.__wait_event = wait_event
        self.__print_event = print_event
        self.file = file
        compiled_code = compile(self.file, path, 'exec')
        self.debug(compiled_code)

    def debug(self, byte_code):
        bc_instr = self.inject_instructions_to_bytecode(byte_code)
        _globals = {'self.debug_function': self.debug_function,
                    '__name__': '__main__',
                    'Debugger.get_instruction': Debugger.inject_instructions_to_bytecode}
        self.__wait_event.wait()
        exec(bc_instr, _globals)
        self.is_running = False
        self.__wait_event.wait()
        self.__wait_event.clear()
        self.watch = {}


    @staticmethod
    def inject_instructions_to_bytecode(byte_co):
        byte_code = bytecode.Bytecode.from_code(byte_co)
        line_number = 1
        bc_instr = bytecode._InstrList()
        for i in range(len(byte_code)):
            instruction = byte_code[i]
            if instruction.__class__ is bytecode.Label:
                bc_instr.append(instruction)
                continue
            new_line_number = instruction.lineno
            if instruction.name == 'LOAD_CONST' and inspect.iscode(instruction.arg):
                bc_instr.append(bytecode.Instr('LOAD_GLOBAL', 'Debugger.get_instruction'))
                bc_instr.append(instruction)
                bc_instr.append(bytecode.Instr('CALL_FUNCTION', 1))
                line_number = new_line_number
            elif new_line_number != line_number:
                bc_instr.append(instruction)
                bc_instr.append(bytecode.Instr('LOAD_GLOBAL', 'self.debug_function', lineno=new_line_number))
                bc_instr.append(bytecode.Instr('CALL_FUNCTION', 0, lineno=new_line_number))
                bc_instr.append(bytecode.Instr('POP_TOP', lineno=new_line_number))
                line_number = new_line_number
            else:
                bc_instr.append(instruction)
        print()
        for i in bc_instr:
            print(i)
        code = bytecode.Bytecode(bc_instr)
        code.name = byte_co.co_name
        code.argcount = byte_co.co_argcount
        code.argnames = byte_code.argnames
        code.filename = byte_code.filename
        code.flags = byte_code.flags
        code.first_lineno = byte_code.first_lineno
        code.cellvars = byte_code.cellvars
        code.freevars = byte_code.freevars
        return code.to_code()

    def set_breakpoint(self, line):
        if line not in self.breakpoints:
            self.breakpoints.add(line)
        else:
            self.breakpoints.remove(line)

    @staticmethod
    def get_stack_frame():
        debugger_frame = sys._getframe()
        call_stack = []
        while debugger_frame is not None:
            call_stack.append(debugger_frame)
            debugger_frame = debugger_frame.f_back
        return call_stack[2:-2]

    def filter_locals(self, names, frame):
        return filter(lambda x: x in names and x not in self.debug_functions_names, frame.f_locals.keys())

    def debug_function(self):
        call_stack = Debugger.get_stack_frame()
        self.__wait_event.wait()
        self.__wait_event.clear()
        if call_stack[0].f_lineno not in self.breakpoints and not self.step_into:
            return
        self.last_line = call_stack[0].f_lineno
        self.call_stack = []
        for frame in filter(lambda frame: frame.f_code.co_name not in self.debug_functions_names, call_stack):
            names = frame.f_locals.keys()
            func_name = frame.f_code.co_name
            self.call_stack.append(func_name)
            self.watch[func_name] = []
            classes = set()
            for local in self.filter_locals(names, frame):
                obj = frame.f_locals[local]
                if inspect.isclass(obj):
                    classes.add(obj)
                    continue
                if inspect.isfunction(obj) or inspect.ismethod(obj):
                    continue
                if obj.__class__ in classes:
                    self.get_class_fields(obj, classes, local, func_name)
                elif local[:2] != '__':
                    self.watch[func_name].append('name: {}  value: {}'.format(local, obj))
        self.step_into = False
        self.__print_event.set()

    def get_class_fields(self, obj, classes, local, func_name):
        stack = [(obj, local)]
        depth = 0
        while len(stack) != 0:
            obj, local = stack.pop()
            value = obj.__class__.__name__ if obj.__class__ in classes else obj
            self.watch[func_name].append('\t' * depth + 'name: {}  value: {}'.format(local, value))
            if obj.__class__ in classes:
                for variable in filter(lambda x: x[:2] != '__', dir(obj)):
                    attribute = getattr(obj, variable)
                    if not callable(attribute):
                        stack.append((attribute, variable))
                depth += 1
            if depth > 3:
                depth -= 1
                continue


if __name__ == '__main__':
    debugger = Debugger()
    file = open("F:\Debbuger#\FunctionTest.py", 'r').read()
    debugger.set_breakpoint(4)
    debugger.open(file, "F:\Debbuger#\FunctionTest.py", None, None)
