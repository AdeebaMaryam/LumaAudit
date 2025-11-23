# backend/main.py
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io, json
from pathlib import Path
from typing import Dict, Any

# local imports (ensure backend is run as a package or adjust import)
from .ml_utils import compute_recommended_stock, sales_average, moving_average
from . import blockchain

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = Path(__file__).parent / "data"
SALES_CSV = DATA_DIR / "sample_sales.csv"

# Helper: read sales into DataFrame (return empty df with columns if file missing)
def load_sales_df() -> pd.DataFrame:
    if not SALES_CSV.exists():
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        # create empty file with headers
        pd.DataFrame(columns=["date", "product_id", "quantity_sold"]).to_csv(SALES_CSV, index=False)
    return pd.read_csv(SALES_CSV, parse_dates=["date"])

@app.post("/ingest_sales")
async def ingest_sales(file: UploadFile = File(...)):
    """Upload CSV with columns: date,product_id,quantity_sold"""
    content = await file.read()
    df_new = pd.read_csv(io.StringIO(content.decode()))
    df_old = load_sales_df()
    df = pd.concat([df_old, df_new], ignore_index=True)
    df.to_csv(SALES_CSV, index=False)
    return {"status": "ok", "rows_total": int(len(df))}

@app.get("/calculate_stock")
def calculate_stock(lead_time_days: int = 7, window: int = 7):
    df = load_sales_df()
    products: Dict[int, Dict[str, Any]] = {}
    # if df is empty, return empty dict
    if df.empty:
        return {"products": {}}

    for pid, g in df.groupby("product_id"):
        sales_list = g.sort_values("date")["quantity_sold"].astype(float).tolist()
        # compute recommended (may be float) -> convert to int
        recommended_raw = compute_recommended_stock(sales_list, lead_time_days=lead_time_days, window=window)
        recommended = int(round(recommended_raw))
        # compute last sales average as Python float
        last_avg_series = pd.Series(sales_list).tail(window)
        last_sales_avg = float(last_avg_series.mean()) if len(last_avg_series) > 0 else 0.0
        products[int(pid)] = {"recommended_qty": recommended, "last_sales_avg": last_sales_avg}
    return {"products": products}

@app.get("/restock_priority")
def restock_priority():
    """
    Priority score = (recommended - current_on_chain) / recommended
    If on_chain is 0 and recommended >0 -> high priority.
    We'll fetch contract quantity for current_on_chain.
    """
    df = load_sales_df()
    if df.empty:
        return {"priority": []}

    # calculate recommended for each product (as int)
    recs: Dict[int, int] = {}
    for pid, g in df.groupby("product_id"):
        sales_list = g.sort_values("date")["quantity_sold"].astype(float).tolist()
        rec_raw = compute_recommended_stock(sales_list)
        recs[int(pid)] = int(round(rec_raw))

    # get on-chain quantities (ensure int)
    chain: Dict[int, int] = {}
    for pid in recs.keys():
        try:
            p = blockchain.contract.functions.products(pid).call()
            chain_qty = int(p[1])  # struct: (productId, quantity, lastUpdated, discountApplied)
        except Exception:
            chain_qty = 0
        chain[pid] = chain_qty

    # compute simple score and sort
    scored = []
    for pid, rec in recs.items():
        current = int(chain.get(pid, 0))
        need = max(0, int(rec) - current)
        score = float(need) / float(rec) if rec > 0 else 0.0
        scored.append({
            "product_id": int(pid),
            "recommended": int(rec),
            "current": int(current),
            "need": int(need),
            "score": float(round(score, 4))
        })
    scored_sorted = sorted(scored, key=lambda x: x["score"], reverse=True)
    return {"priority": scored_sorted}

@app.post("/apply_discount")
def apply_discount(product_id: int, discount_percent: int = 20):
    """
    Applies discount flag on-chain and returns receipt.
    Backend is responsible for discount percent (frontend or DB).
    """
    # call on-chain
    receipt = blockchain.apply_discount_on_chain(product_id)
    # receipt is usually a AttributeDict; convert to dict safely
    try:
        receipt_dict = dict(receipt)
    except Exception:
        # fallback: try to JSON serialise the object
        receipt_dict = json.loads(json.dumps(receipt, default=str))
    return {"status": "discount_applied_on_chain", "product_id": int(product_id), "receipt": receipt_dict}

@app.post("/restock_and_update_chain")
def restock_and_update_chain(product_id: int, new_qty: int):
    """
    Use this to set/update product quantity on-chain after you physically restock.
    """
    receipt = blockchain.add_or_update_product(product_id, new_qty)
    try:
        receipt_dict = dict(receipt)
    except Exception:
        receipt_dict = json.loads(json.dumps(receipt, default=str))
    return {"status": "on_chain_updated", "product_id": int(product_id), "receipt": receipt_dict}
