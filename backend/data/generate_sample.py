# generate_sample.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
products = [101,102,103,104,105,106]
rows=[]
start = datetime.today() - timedelta(days=29)
for d in range(30):
    date = (start + timedelta(days=d)).strftime("%Y-%m-%d")
    for pid in products:
        # random small daily sales pattern
        qty = max(0, int(np.random.poisson(lam=3 + (pid%3))))
        rows.append({"date": date, "product_id": pid, "quantity_sold": qty})
df = pd.DataFrame(rows)
df.to_csv("sample_sales.csv", index=False)
print("sample_sales.csv created with", len(df), "rows")
