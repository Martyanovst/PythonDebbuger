import bytecode
import re
import sys
import inspect
import time
import threading

class Debugger:

    def __init__(self):
        global system_names
        self.line_pattern = re.compile(r'lineno=(\d+)')
        self.breakpoints = set()
        self.is_running = True

    def open(self, file, path):
        self.file = file
        self.compiled_code = compile(self.file, path, 'exec')
        self.bytecode = bytecode.Bytecode.from_code(self.compiled_code)

    def debug(self, wait_event,print_event):
        self.wait_event = wait_event
        self.print_event = print_event
        bc_instr = self.get_instructions()
        _globals = {'self.debug_function' : self.debug_function,  '__name__': '__main__'}
        self.wait_event.wait()
        exec(bytecode.Bytecode(bc_instr).to_code(), _globals)
        self.is_running = False

    def get_instructions(self):
        line_number = 1
        bc_instr = bytecode._InstrList()
        for instruction in self.bytecode:
            new_line_number = self.line_pattern.search(str(instruction)).group(1)
            if new_line_number != line_number:
                bc_instr.append(bytecode.Instr('LOAD_GLOBAL', 'self.debug_function'))
                bc_instr.append(bytecode.Instr('CALL_FUNCTION', 0))
                bc_instr.append(bytecode.Instr('POP_TOP'))
                line_number = new_line_number
            bc_instr.append(instruction)
        return  bc_instr

    def set_breakpoint(self, line):
        if line not in self.breakpoints:
            self.breakpoints.add(line)
        else:
            self.breakpoints.remove(line)

    def debug_function(self):
        debugger_frame = sys._getframe()
        call_stack = []
        while debugger_frame is not None:
            call_stack.append(debugger_frame)
            debugger_frame = debugger_frame.f_back

        if call_stack[1].f_lineno not in self.breakpoints:
            return
        self.wait_event.wait()
        self.wait_event.clear()
        self.watch = {}
        for frame in call_stack[1:-2]:
            names = frame.f_code.co_names
            classes = set()
            for local in filter(lambda x: x in names and x != 'self.debug_function', frame.f_locals.keys()):
                obj = frame.f_locals[local]
                if inspect.isclass(obj):
                    classes.add(obj)
                    continue
                if inspect.isfunction(obj):
                    continue
                if obj.__class__ in classes:
                    self.get_class_fields(obj,classes,local)
                elif local[:2] != '__':
                    self.watch['name: {}'.format(local)] = ' value: {}'.format(obj)

        self.print_event.set()


    def get_class_fields(self,obj,classes, local):
        stack = [(obj,local)]
        depth = 0
        while(len(stack) != 0):
            obj,local = stack.pop()
            self.watch[' ' * depth + 'name: {}  '.format(local)] =  'value: {}'.format(obj)

            if obj.__class__ in classes:
                for variable in filter(lambda x: x[:2] != '__', dir(obj)):
                    attribute = getattr(obj, variable)
                    if not callable(attribute):
                        stack.append((attribute,variable))
                depth += 1
            if depth > 3:
                depth -= 1
                continue

