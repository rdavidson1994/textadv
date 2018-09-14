import numpy as np
x = np.arange(5)
z = (slice(None), *[None]*len(x))
print(z)
y = x[(slice(None), *[None]*len(x))]
print(y)