from datetime import timedelta

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

FORECAST_DAYS = 10
MERCHANT_TYPE_CODE = 5732
PURCHASE_ACTIVITY = 'PurchaseActivity'

# Read data
df = pd.read_csv("combined_transactions.csv")
# Filter for proper merchant_type_code
df = df[(df['merchant_type_code']==MERCHANT_TYPE_CODE) & (df['transaction_type']==PURCHASE_ACTIVITY)]
df['date'] = pd.to_datetime(df['datetime']).dt.date

first_date = df['date'].min()
last_date = df['date'].max()
day_span = (last_date - first_date).days

# Aggregate by date
df = df['amount_cents'].groupby(df['date']).sum()

# Add 0 Purchase days
for x in range(day_span):
    day = first_date + timedelta(days=x)
    if day not in df:
        df[day] = 0

df = df.to_frame()
df = df.sort_values('date')
x = np.array(range(day_span + 1)).reshape((-1,1))
y = df.values.flatten()
model = LinearRegression(positive=True).fit(x, y)
next_ten_days = np.array([[day_span + i + 1] for i in range(FORECAST_DAYS)]).reshape((-1,1))
prediction = model.predict(next_ten_days)
print(prediction)
