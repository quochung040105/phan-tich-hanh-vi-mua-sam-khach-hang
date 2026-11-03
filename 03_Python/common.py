"""
Các hằng số và hàm dùng chung cho toàn bộ pipeline Python.
Chạy các script 01..05 theo đúng thứ tự vì script sau dùng kết quả của script trước.
"""
from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "DATA"
OUT_DIR = ROOT / "outputs" / "python"
CHART_DIR = ROOT / "04_Charts" / "images"
OUT_DIR.mkdir(parents=True, exist_ok=True)
CHART_DIR.mkdir(parents=True, exist_ok=True)

ORIGINAL_CSV = DATA_DIR / "marketing_campaign.csv"          # file gốc (tab-separated)
BEFORE_CSV = DATA_DIR / "NguyenQuocHung_customer_personality.csv"  # file đã bị làm bẩn
AFTER_CLEAN_CSV = OUT_DIR / "_intermediate_after_cleaning_python.csv"  # trung gian, không phải file nộp bài
AFTER_PYTHON_CSV = DATA_DIR / "after_python.csv"             # kết quả cuối cùng (Python) - 1 trong 3 file nộp bài

# Các nhóm field theo kiểu dữ liệu / ý nghĩa
ID_COL = "ID"
NUMERIC_COLS = [
    "Year_Birth", "Income", "Kidhome", "Teenhome", "Recency",
    "MntWines", "MntFruits", "MntMeatProducts", "MntFishProducts",
    "MntSweetProducts", "MntGoldProds",
    "NumDealsPurchases", "NumWebPurchases", "NumCatalogPurchases",
    "NumStorePurchases", "NumWebVisitsMonth",
]
BOOLEAN_COLS = [
    "AcceptedCmp3", "AcceptedCmp4", "AcceptedCmp5", "AcceptedCmp1",
    "AcceptedCmp2", "Complain", "Response",
]
CONSTANT_COLS = ["Z_CostContact", "Z_Revenue"]  # luôn luôn hằng số -> ứng viên rút gọn dữ liệu
DATE_COL = "Dt_Customer"
NOMINAL_COLS = ["Marital_Status"]
ORDINAL_COLS = ["Education"]
EDUCATION_ORDER = ["Basic", "2n Cycle", "Graduation", "Master", "PhD"]

MNT_COLS = [
    "MntWines", "MntFruits", "MntMeatProducts",
    "MntFishProducts", "MntSweetProducts", "MntGoldProds",
]


def load_before(dtype_str=True):
    """Đọc file 'before' (dữ liệu đã bị làm bẩn) y nguyên dạng chuỗi để không mất dấu vết lỗi."""
    if dtype_str:
        return pd.read_csv(BEFORE_CSV, dtype=str)
    return pd.read_csv(BEFORE_CSV)


def load_original():
    return pd.read_csv(ORIGINAL_CSV, sep="\t")


def lowest_mode(series: pd.Series):
    """Mode của series; nếu có nhiều mode, chọn giá trị thấp nhất (yêu cầu của đề bài)."""
    m = series.mode(dropna=True)
    if len(m) == 0:
        return np.nan
    return m.min()


def log(msg, path=None, mode="a"):
    print(msg)
    if path is not None:
        with open(path, mode, encoding="utf-8") as f:
            f.write(str(msg) + "\n")
