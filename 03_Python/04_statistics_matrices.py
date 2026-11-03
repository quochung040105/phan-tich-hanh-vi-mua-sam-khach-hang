"""
Bước 3.f - Thống kê mô tả sau tiền xử lý + Ma trận tương quan/khác biệt cho 3 record tuỳ chọn
Input : DATA/after_python.csv
Output: outputs/python/04_field_statistics.csv
        outputs/python/04_correlation_matrix_3records.csv
        outputs/python/04_difference_matrix_3records.csv
"""
import numpy as np
import pandas as pd
from scipy.spatial.distance import pdist, squareform

from common import AFTER_PYTHON_CSV, OUT_DIR, NUMERIC_COLS, log

LOGFILE = OUT_DIR / "04_statistics_log.txt"
LOGFILE.write_text("", encoding="utf-8")

df = pd.read_csv(AFTER_PYTHON_CSV)
log(f"Kích thước dữ liệu sau tiền xử lý: {df.shape}", LOGFILE)

# ---------------------------------------------------------------------------
# Thống kê mô tả cho từng field, tuỳ theo kiểu dữ liệu
# ---------------------------------------------------------------------------
numeric_like = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c]) and c != "ID"]
categorical_like = [c for c in df.columns if not pd.api.types.is_numeric_dtype(df[c])]

rows = []
for col in numeric_like:
    s = df[col]
    mode_val = s.mode(dropna=True)
    rows.append({
        "field": col, "kieu": "numeric",
        "mean": round(s.mean(), 3), "mode": mode_val.iloc[0] if len(mode_val) else np.nan,
        "median": s.median(), "std": round(s.std(), 3),
        "min": s.min(), "q25": s.quantile(0.25), "q50": s.quantile(0.50),
        "q75": s.quantile(0.75), "max": s.max(),
    })

for col in categorical_like:
    s = df[col]
    mode_val = s.mode(dropna=True)
    rows.append({
        "field": col, "kieu": "categorical",
        "mean": np.nan, "mode": mode_val.iloc[0] if len(mode_val) else np.nan,
        "median": np.nan, "std": np.nan,
        "min": np.nan, "q25": np.nan, "q50": np.nan, "q75": np.nan, "max": np.nan,
    })

stats_df = pd.DataFrame(rows)
stats_df.to_csv(OUT_DIR / "04_field_statistics.csv", index=False)
log("\n--- BẢNG THỐNG KÊ MÔ TẢ THEO TỪNG FIELD ---", LOGFILE)
log(stats_df.to_string(index=False), LOGFILE)

# ---------------------------------------------------------------------------
# Ma trận tương quan (correlation) & ma trận khác biệt (difference/distance) cho 3 record tuỳ chọn
# ---------------------------------------------------------------------------
log("\n" + "=" * 70, LOGFILE)
log("MA TRẬN TƯƠNG QUAN & MA TRẬN KHÁC BIỆT CHO 3 RECORD TUỲ CHỌN", LOGFILE)
log("=" * 70, LOGFILE)

chosen_ids = df["ID"].dropna().iloc[[0, 10, 20]].tolist()
log(f"3 record được chọn (theo ID): {chosen_ids}", LOGFILE)

subset = df.set_index("ID").loc[chosen_ids, numeric_like]
log("\nDữ liệu số của 3 record được chọn:", LOGFILE)
log(subset.to_string(), LOGFILE)

# Ma trận tương quan: tương quan Pearson giữa các VECTOR thuộc tính của từng cặp record
corr_matrix = subset.T.corr(method="pearson")
corr_matrix.to_csv(OUT_DIR / "04_correlation_matrix_3records.csv")
log("\n--- Ma trận tương quan (Pearson) giữa 3 record (tính trên vector các thuộc tính số) ---", LOGFILE)
log(corr_matrix.round(4).to_string(), LOGFILE)

# Ma trận khác biệt: khoảng cách Euclidean (đã chuẩn hoá z-score trước khi tính, tránh field có
# đơn vị/độ lớn khác nhau lấn át) giữa từng cặp record
subset_z = (subset - subset.mean()) / subset.std(ddof=0).replace(0, 1)
dist = squareform(pdist(subset_z.to_numpy(), metric="euclidean"))
diff_matrix = pd.DataFrame(dist, index=chosen_ids, columns=chosen_ids)
diff_matrix.to_csv(OUT_DIR / "04_difference_matrix_3records.csv")
log("\n--- Ma trận khác biệt (Euclidean distance, sau khi chuẩn hoá z-score) giữa 3 record ---", LOGFILE)
log(diff_matrix.round(4).to_string(), LOGFILE)

print(f"\n>>> Log & kết quả: {LOGFILE}")
