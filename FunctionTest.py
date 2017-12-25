def Foo():
    for i in range(10):
       yield i

for i in Foo():
    print(i)