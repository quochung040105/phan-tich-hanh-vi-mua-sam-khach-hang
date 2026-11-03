"""
Bước 3.c, 3.d, 3.e (dùng Python)
  c) Tích hợp dữ liệu (Data Integration) - ghi chú vì bộ dữ liệu chỉ có 1 bảng nguồn
  d) Giảm thiểu dữ liệu (Data Reduction) - >= 2 trường hợp
  e) Chuyển đổi & phân tách dữ liệu (Data Transformation & Discretization)
Input : DATA/_intermediate_after_cleaning_python.csv (kết quả của 02_data_cleaning.py)
Output: DATA/after_python.csv (file 'after' cuối cùng nộp bài, pipeline Python)
"""
import numpy as np
import pandas as pd

from common import (
    AFTER_CLEAN_CSV, AFTER_PYTHON_CSV, OUT_DIR, CONSTANT_COLS, BOOLEAN_COLS,
    MNT_COLS, EDUCATION_ORDER, log,
)

LOGFILE = OUT_DIR / "03_transformation_log.txt"
LOGFILE.write_text("", encoding="utf-8")

df = pd.read_csv(AFTER_CLEAN_CSV)
log(f"Kích thước đầu vào: {df.shape}", LOGFILE)

# ---------------------------------------------------------------------------
# (c) TÍCH HỢP DỮ LIỆU (Data Integration)
# ---------------------------------------------------------------------------
log("\n" + "=" * 70, LOGFILE)
log("(c) TÍCH HỢP DỮ LIỆU (Data Integration)", LOGFILE)
log("=" * 70, LOGFILE)
log(
    "Bộ dữ liệu gốc 'marketing_campaign.csv' chỉ gồm DUY NHẤT một bảng (one flat table), "
    "không có bảng phụ nào khác cần hợp nhất (join/merge) nên bước tích hợp dữ liệu KHÔNG áp dụng (N/A) "
    "ở cấp độ bảng nguồn.\n"
    "Tuy nhiên, trong bước (e) bên dưới, quá trình tách field kiểu chuỗi 'Products_Purchased' có sinh ra "
    "nhiều bảng/field trung gian (6 field boolean Has_Wines, Has_Fruits, ...). Các field trung gian này "
    "có cùng cấu trúc (kiểu boolean, cùng ý nghĩa 'khách hàng có mua nhóm sản phẩm X hay không') nên được "
    "gộp lại (tích hợp) thành 1 field số duy nhất 'Product_Categories_Bitmask' để giảm số lượng field thực tế "
    "phải sử dụng, thay vì giữ rời rạc 6 field riêng biệt.",
    LOGFILE,
)

# ---------------------------------------------------------------------------
# (d) GIẢM THIỂU DỮ LIỆU (Data Reduction) - >= 2 trường hợp
# ---------------------------------------------------------------------------
log("\n" + "=" * 70, LOGFILE)
log("(d) GIẢM THIỂU DỮ LIỆU (Data Reduction)", LOGFILE)
log("=" * 70, LOGFILE)

log("\n-- Trường hợp 1: Giảm chiều (attribute/dimensionality reduction) --", LOGFILE)
for c in CONSTANT_COLS:
    log(f"'{c}': số giá trị duy nhất = {df[c].nunique()} -> {df[c].unique()}", LOGFILE)
log(
    f"Hai field {CONSTANT_COLS} là hằng số trên toàn bộ dữ liệu (phương sai = 0), "
    "không mang thông tin phân biệt giữa các khách hàng -> loại bỏ khỏi tập dữ liệu dùng để phân tích.",
    LOGFILE,
)
df_reduced = df.drop(columns=CONSTANT_COLS)
log(f"Số cột trước: {df.shape[1]} -> sau khi giảm chiều: {df_reduced.shape[1]}", LOGFILE)

log("\n-- Trường hợp 2: Giảm số lượng bản ghi (numerosity reduction - stratified sampling) --", LOGFILE)
SAMPLE_FRAC = 0.2
demo_sample = (
    df_reduced.groupby("Education", group_keys=False)[df_reduced.columns]
    .apply(lambda g: g.sample(frac=SAMPLE_FRAC, random_state=42))
)
sample_path = OUT_DIR / "03_reduction_stratified_sample_demo.csv"
demo_sample.to_csv(sample_path, index=False)
log(
    f"Minh hoạ kỹ thuật giảm thiểu dữ liệu bằng lấy mẫu phân tầng (stratified sampling) theo 'Education' "
    f"với tỉ lệ {SAMPLE_FRAC*100:.0f}%: từ {df_reduced.shape[0]} dòng còn {demo_sample.shape[0]} dòng, "
    f"vẫn giữ nguyên tỉ lệ các nhóm Education như tập gốc. Lưu minh hoạ tại: {sample_path.name} "
    "(chỉ dùng để minh hoạ kỹ thuật, KHÔNG dùng tập mẫu này cho các bước phân tích chính phía sau).",
    LOGFILE,
)
log(
    "So sánh tỉ lệ nhóm Education (gốc vs mẫu):\n"
    f"{pd.concat([df_reduced['Education'].value_counts(normalize=True).rename('goc'), demo_sample['Education'].value_counts(normalize=True).rename('mau')], axis=1).round(3).to_string()}",
    LOGFILE,
)

df = df_reduced

# ---------------------------------------------------------------------------
# (e) CHUYỂN ĐỔI & PHÂN TÁCH DỮ LIỆU (Data Transformation & Discretization)
# ---------------------------------------------------------------------------
log("\n" + "=" * 70, LOGFILE)
log("(e) CHUYỂN ĐỔI & PHÂN TÁCH DỮ LIỆU", LOGFILE)
log("=" * 70, LOGFILE)

log("\n-- (e.1) Kiểu THỨ TỰ -> số nguyên: Education --", LOGFILE)
edu_map = {e: i for i, e in enumerate(EDUCATION_ORDER)}
log(f"Bảng ánh xạ thứ tự (giữ đúng quan hệ thứ bậc Basic < 2n Cycle < Graduation < Master < PhD): {edu_map}", LOGFILE)
df["Education_encoded"] = df["Education"].map(edu_map)
log(df[["Education", "Education_encoded"]].drop_duplicates().sort_values("Education_encoded").to_string(index=False), LOGFILE)

log("\n-- (e.2) Kiểu DANH MỤC -> số nguyên: Marital_Status --", LOGFILE)
marital_categories = sorted(df["Marital_Status"].unique())
marital_map = {m: i for i, m in enumerate(marital_categories)}
log(f"Bảng ánh xạ danh mục (không có thứ bậc, chỉ định danh bằng số nguyên): {marital_map}", LOGFILE)
df["Marital_Status_encoded"] = df["Marital_Status"].map(marital_map)

log("\n-- (e.3) Gộp >=5 field BOOLEAN thành 1 field kiểu số (bitmask nhị phân) --", LOGFILE)
log(f"Các field boolean được gộp ({len(BOOLEAN_COLS)} field): {BOOLEAN_COLS}", LOGFILE)
df[BOOLEAN_COLS] = df[BOOLEAN_COLS].astype(int)
bitmask = np.zeros(len(df), dtype=int)
for i, col in enumerate(BOOLEAN_COLS):
    bitmask += df[col].to_numpy() * (2 ** i)
df["Campaigns_Response_Bitmask"] = bitmask
log(f"Công thức: bitmask = sum(field_i * 2^i). Thứ tự bit (từ bit0): {BOOLEAN_COLS}", LOGFILE)
log(df[BOOLEAN_COLS + ["Campaigns_Response_Bitmask"]].head(8).to_string(index=False), LOGFILE)
# kiểm chứng có thể giải mã ngược lại
decoded_check = pd.DataFrame(
    {col: (df["Campaigns_Response_Bitmask"].to_numpy() // (2 ** i)) % 2 for i, col in enumerate(BOOLEAN_COLS)}
)
match = (decoded_check.values == df[BOOLEAN_COLS].values).all()
log(f"Giải mã ngược lại từ bitmask khớp 100% với dữ liệu gốc: {match}", LOGFILE)

log("\n-- (e.4) Field CHUỖI chứa danh sách chuỗi con có ý nghĩa --", LOGFILE)
log(
    "Bộ dữ liệu gốc không có sẵn field dạng 'danh sách sản phẩm đã mua' dạng chuỗi. "
    "Để minh hoạ đúng kỹ thuật theo yêu cầu đề bài, nhóm TỰ XÂY DỰNG field chuỗi "
    "'Products_Purchased' từ 6 field chi tiêu Mnt* sẵn có: với mỗi khách hàng, liệt kê tên "
    "các nhóm sản phẩm có MntX > 0 (đã từng mua), phân tách nhau bởi dấu phẩy - giống ví dụ "
    "'Tên hàng đã mua' trong đề bài.",
    LOGFILE,
)
product_names = {
    "MntWines": "Wines", "MntFruits": "Fruits", "MntMeatProducts": "Meat",
    "MntFishProducts": "Fish", "MntSweetProducts": "Sweet", "MntGoldProds": "Gold",
}


def build_product_list(row):
    return ", ".join(name for col, name in product_names.items() if row[col] > 0)


df["Products_Purchased"] = df.apply(build_product_list, axis=1)
log("Ví dụ field chuỗi mới 'Products_Purchased':", LOGFILE)
log(df[["ID", "Products_Purchased"]].head(8).to_string(index=False), LOGFILE)

log("\nTách field chuỗi trên thành nhiều field boolean trung gian (1 field / 1 sản phẩm):", LOGFILE)
bool_product_cols = []
for col, name in product_names.items():
    new_col = f"Has_{name}"
    df[new_col] = (df[col] > 0).astype(int)
    bool_product_cols.append(new_col)
log(f"Các field trung gian phát sinh: {bool_product_cols}", LOGFILE)
log(df[["ID"] + bool_product_cols].head(8).to_string(index=False), LOGFILE)

log(
    "\nVì có nhiều field mới cùng kiểu boolean & cùng ý nghĩa (nhóm sản phẩm) nên GỘP LẠI (tích hợp, "
    "xem mục (c)) thành 1 field số duy nhất bằng kỹ thuật bitmask tương tự (e.3):",
    LOGFILE,
)
prod_bitmask = np.zeros(len(df), dtype=int)
for i, col in enumerate(bool_product_cols):
    prod_bitmask += df[col].to_numpy() * (2 ** i)
df["Product_Categories_Bitmask"] = prod_bitmask
log(df[bool_product_cols + ["Product_Categories_Bitmask"]].head(8).to_string(index=False), LOGFILE)
# dọn field trung gian sau khi đã gộp (giữ lại field chuỗi gốc + field số cuối cùng để tham khảo)
df = df.drop(columns=bool_product_cols)

log(f"\nKích thước cuối cùng sau toàn bộ bước transformation: {df.shape}", LOGFILE)

# ---------------------------------------------------------------------------
# Lưu file 'after' cuối cùng (pipeline Python)
# ---------------------------------------------------------------------------
df.to_csv(AFTER_PYTHON_CSV, index=False)
log(f"\n>>> Đã lưu file AFTER (Python) tại: {AFTER_PYTHON_CSV}", LOGFILE)
print(f">>> Log chi tiết: {LOGFILE}")
