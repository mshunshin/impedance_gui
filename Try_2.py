import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd

# Example data for two box plots
np.random.seed(42)
data1 = np.random.normal(loc=0, scale=1, size=100)  # Data for first box plot
data2 = np.random.normal(loc=2, scale=1.5, size=100)  # Data for second box plot

# Create a DataFrame for each set of data (if you have your own data, use that)
df1 = pd.DataFrame({'Data': data1})
df2 = pd.DataFrame({'Data': data2})

# Create subplots
fig, axes = plt.subplots(1, 2, figsize=(12, 6))  # 1 row, 2 columns

# Create the first box plot with scatter overlay
sns.boxplot(data=df1, y='Data', color='lightblue', ax=axes[0])
sns.stripplot(data=df1, y='Data', color='red', jitter=True, size=4, ax=axes[0])
axes[0].set_title('Box Plot 1')

# Create the second box plot with scatter overlay
sns.boxplot(data=df2, y='Data', color='lightgreen', ax=axes[1])
sns.stripplot(data=df2, y='Data', color='blue', jitter=True, size=4, ax=axes[1])
axes[1].set_title('Box Plot 2')

# Show the plot
plt.tight_layout()
plt.show()
