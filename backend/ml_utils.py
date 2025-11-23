# ml_utils.py
import numpy as np
import pandas as pd
from math import sqrt

def moving_average(sales_list, window=7):
    """Simple moving average: average of the last `window` days. sales_list is list or 1D array."""
    if len(sales_list) == 0:
        return 0.0
    series = pd.Series(sales_list)
    return float(series.tail(window).mean())

def sales_average(sales_list):
    """Simple average across provided period."""
    if len(sales_list) == 0:
        return 0.0
    return float(np.mean(sales_list))

def safety_stock(std_dev_of_demand, lead_time_days, z=1.65):
    """
    z = 1.65 -> ~95% service level (brief).
    safety_stock = z * std_dev_of_demand * sqrt(lead_time_days)
    """
    return float(z * std_dev_of_demand * sqrt(max(1, lead_time_days)))

def compute_recommended_stock(sales_history_list, lead_time_days=7, service_z=1.65, window=7):
    """
    Returns recommended_stock = moving_average + safety_stock
    - moving_average: expected demand during lead_time = daily_avg * lead_time_days
    """
    ma = moving_average(sales_history_list, window=window)
    daily_avg = ma
    std = float(pd.Series(sales_history_list).std(ddof=0)) if len(sales_history_list) > 1 else 0.0
    ss = safety_stock(std, lead_time_days, z=service_z)
    recommended = daily_avg * lead_time_days + ss
    return max(0, int(round(recommended)))

# optional EOQ (very basic fallback)
def eoq(demand_per_year, setup_cost, holding_cost_per_unit):
    # EOQ = sqrt( (2 * D * S) / H )
    return int(round(((2 * demand_per_year * setup_cost) / holding_cost_per_unit) ** 0.5))
