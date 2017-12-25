import dis
import bytecode

import FunctionTest

code = compile(open('F:\Debbuger#\FunctionTest.py', 'r').read(),'F:\Debbuger#\FunctionTest.py','exec')
# dis.dis(code)
print()
# dis.dis(FunctionTest)
for i in bytecode.Bytecode.from_code(code):
    print(i)
# for i in dis.Bytecode(code):
#     print((i.opname,i.argval,i.starts_line))
