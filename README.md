# pyvalidate
Pythonic decorator for datatype validation.
Only needs to import:
```
import inspect
import sys
```
Example of Usage:

```
@validate_data(int, float, list, tuple)
def process(a, b):
    return f"Used vars: {a} y {b}"

class MyClasss:
    def __init__(self, value):
        self.value = value
        self.name = "example"

print("\n=== EXAMPLES WITH ERRORS ===")
try:
    print(process(5, "string"))
except TypeError as e:
    print(e)
try:
    obj = MyClass(42)
    print(process(obj, [1, 2, 3]))
except TypeError as e:
    print(e)
try:
    big_list = list(range(100))
    print(process(big_list, "invalid string"))
except TypeError as e:
    print(e)
try:
    big_dict = {f"key_{i}": f"value_{i}" for i in range(10)}
    print(process(big_dict, None))
except TypeError as e:
    print(e)
```
