def get_next_method(obj, method):
    method_string = method.__name__
    print(method)
    print(obj)
    print(obj.__class__)
    print(isinstance(super(obj.__class__, obj), object))
    next_method = super(obj.__class__, obj).__dict__[method.__name__]

class A():
    def f(self):
        print("Hello")

class B(A):
    def f(self):
        print("Goodbye")
    def wat(self):
        print(super().__class__)

b = B()
b.f()
b.wat()
print(super(B,b).__class__)
get_next_method(b, b.f)()
