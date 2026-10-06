import numpy as np
import matplotlib.pyplot as plt
import pandas as pd


xr = np.linspace(-5,5,100)
yr = np.sin(xr)/xr
plt.plot(xr,yr)

plt.grid()
plt.xlabel('Xaxis')
plt.ylabel('Yaxis')
plt.show()

Table= pd.DataFrame()
Table['Source']=['Solar','Wind','Hydro','Hydrogen'] 
Table['Installed'] = [10,20,200,11]
Table['Increased']=[20,50,100,12]
Table['Percentage']=[2,14,25,22]
Table.head() 

print(Table['Source'][1])
print(Table['Source'][2])
print(Table['Source'][3])

Table.plot()
plt.grid()
plt.show()
