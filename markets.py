
# coding: utf-8

# In[2]:

import pandas as pd


# In[36]:

df = pd.read_csv('output.csv')


# In[37]:

df


# In[88]:

markets = df['markets']


# In[53]:

print markets


# In[81]:

markets = [s for s in markets if s != '']


# In[82]:

markets = [s for s in markets if s != '""']


# In[85]:

market_str = ','.join(markets)


# In[87]:

with open('markets.csv', 'w') as outfile:
    outfile.write(market_str)


# In[89]:

with open('markets.csv', 'r') as infile:
    markets = infile.read()


# In[91]:

markets.split(',')

