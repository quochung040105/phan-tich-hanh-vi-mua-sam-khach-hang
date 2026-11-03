"""
Bước 3.a - Giới thiệu bộ dữ liệu thô ban đầu (dùng Python)
Thống kê số lượng giá trị của các thuộc tính kiểu boolean/định danh/thứ tự
để phát hiện các giá trị không nhất quán (sai định dạng, viết hoa/thường khác nhau, ...)
"""
from common import load_before, OUT_DIR, NOMINAL_COLS, ORDINAL_COLS, BOOLEAN_COLS, log

REPORT = OUT_DIR / "01_eda_value_counts.txt"
REPORT.write_text("", encoding="utf-8")  # reset

df = load_before()

log("=" * 70, REPORT)
log(f"KÍCH THƯỚC FILE 'BEFORE': {df.shape[0]} dòng x {df.shape[1]} cột", REPORT)
log("=" * 70, REPORT)

log("\n--- 1. Tổng số giá trị thiếu (NaN) theo từng cột ---", REPORT)
log(df.isna().sum().to_string(), REPORT)

log("\n--- 2. Số dòng trùng lặp hoàn toàn (duplicate rows) ---", REPORT)
log(df.duplicated().sum(), REPORT)

log("\n--- 3. Số ID bị trùng lặp ---", REPORT)
log(df["ID"].duplicated().sum(), REPORT)
dup_ids = df[df["ID"].duplicated(keep=False) & df["ID"].notna()]
log("Chi tiết các dòng có ID trùng:", REPORT)
log(dup_ids[["ID", "Year_Birth", "Education", "Marital_Status"]].to_string(), REPORT)

log("\n--- 4. Số dòng trống hoàn toàn (toàn bộ field đều NULL) ---", REPORT)
log(df.isna().all(axis=1).sum(), REPORT)

for col in ORDINAL_COLS + NOMINAL_COLS:
    log(f"\n--- Value counts cho field '{col}' (bao gồm cả khoảng trắng thừa) ---", REPORT)
    log(df[col].value_counts(dropna=False).to_string(), REPORT)
    vc = df[col].dropna()
    log(f">> Tất cả biến thể (chuỗi gốc, chưa strip) trong '{col}': {sorted(vc.unique())}", REPORT)

log("\n--- 5. Value counts cho các field boolean (0/1) ---", REPORT)
for col in BOOLEAN_COLS:
    log(f"\n{col}:", REPORT)
    log(df[col].value_counts(dropna=False).to_string(), REPORT)

log("\n--- 6. Field Year_Birth: các giá trị không phải số (nghi vấn outlier/lỗi nhập liệu) ---", REPORT)
import pandas as pd
yb_numeric = pd.to_numeric(df["Year_Birth"], errors="coerce")
non_numeric = df.loc[yb_numeric.isna() & df["Year_Birth"].notna(), "Year_Birth"].unique()
log(f"Giá trị không parse được thành số: {list(non_numeric)}", REPORT)
log(f"Giá trị Year_Birth nhỏ nhất (nghi vấn outlier do nhập liệu sai): {sorted(yb_numeric.dropna().unique())[:5]}", REPORT)

log("\n--- 7. Field Income: thống kê nhanh ---", REPORT)
inc = pd.to_numeric(df["Income"], errors="coerce")
log(inc.describe().to_string(), REPORT)
log(f"Giá trị Income nhỏ nhất: {inc.min()} | lớn nhất: {inc.max()}", REPORT)

log("\n--- 8. Field Recency: thống kê nhanh (phát hiện giá trị 999 bất thường) ---", REPORT)
rec = pd.to_numeric(df["Recency"], errors="coerce")
log(f"Giá trị Recency lớn nhất: {rec.max()} | số dòng = 999: {(rec == 999).sum()}", REPORT)

log("\n--- 9. Field Dt_Customer: ví dụ các giá trị có khoảng trắng thừa ---", REPORT)
ws = [v for v in df["Dt_Customer"].dropna().unique() if v != v.strip()]
log(f"Số giá trị có khoảng trắng thừa: {len(ws)}; ví dụ: {ws[:5]}", REPORT)

print(f"\n>>> Đã ghi báo cáo EDA vào: {REPORT}")
