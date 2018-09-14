class ListHaver():
    lst = []

class ListHaverA(ListHaver):
    lst.extend["hello"]

class ListHaverB(ListHaver):
    lst.extend["world"]

A = ListHaverA()
B = ListHaverB()
print(A.lst is B.lst)
