"""
Bước 3.b - Làm sạch dữ liệu (Data Cleaning) bằng Python
Thực hiện lần lượt:
  0) Loại bỏ dòng trống hoàn toàn & xử lý trùng lặp (duplicate rows / duplicate ID)
  i) Điền giá trị còn thiếu (>=5 trường hợp, dùng công thức tính toán, không điền giá trị đơn giản)
 ii) Làm mịn dữ liệu (binning theo miền giá trị lớn nhất + điều chỉnh 10% theo độ lệch chuẩn lớn nhất)
iii) Xác định giá trị ngoại lệ bằng five-number summary (IQR) cho các field số
 iv) Xử lý dữ liệu không nhất quán (ngày tháng + field danh nghĩa) - gồm demo tự làm lỗi rồi tự sửa
Kết quả: DATA/_intermediate_after_cleaning_python.csv
"""
import numpy as np
import pandas as pd

from common import (
    load_before, OUT_DIR, AFTER_CLEAN_CSV, NUMERIC_COLS, BOOLEAN_COLS,
    DATE_COL, NOMINAL_COLS, ORDINAL_COLS, EDUCATION_ORDER, lowest_mode, log,
)

LOGFILE = OUT_DIR / "02_cleaning_log.txt"
LOGFILE.write_text("", encoding="utf-8")

df = load_before()
log(f"[0] Kích thước ban đầu (file before): {df.shape}", LOGFILE)

# ---------------------------------------------------------------------------
# Chuẩn hoá kiểu dữ liệu thô: numeric string -> float, giữ nguyên NaN
# ---------------------------------------------------------------------------
for col in NUMERIC_COLS + BOOLEAN_COLS + ["ID"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Year_Birth: "Unknown" -> NaN (đã coerce ở trên), kiểm tra lại
log(f"Year_Birth NaN sau coerce: {df['Year_Birth'].isna().sum()}", LOGFILE)

# ---------------------------------------------------------------------------
# BƯỚC 0a. Loại bỏ các dòng trống hoàn toàn (Empty Rows)
# ---------------------------------------------------------------------------
empty_mask = df.isna().all(axis=1)
log(f"\n[0a] Số dòng trống hoàn toàn bị loại: {empty_mask.sum()}", LOGFILE)
df = df.loc[~empty_mask].copy()
log(f"Kích thước sau khi loại dòng trống: {df.shape}", LOGFILE)

# ---------------------------------------------------------------------------
# BƯỚC 0b. Loại bỏ dòng trùng lặp hoàn toàn (Duplicate Rows)
# ---------------------------------------------------------------------------
n_dup = df.duplicated().sum()
log(f"\n[0b] Số dòng trùng lặp hoàn toàn bị loại: {n_dup}", LOGFILE)
df = df.drop_duplicates(keep="first").copy()
log(f"Kích thước sau khi loại dòng trùng: {df.shape}", LOGFILE)

# ---------------------------------------------------------------------------
# BƯỚC 0c. Xử lý ID trùng lặp nhưng dữ liệu KHÁC nhau (Key Issue)
#   -> giữ bản ghi có ít giá trị NULL nhất (đầy đủ thông tin hơn); nếu bằng nhau giữ bản đầu tiên
# ---------------------------------------------------------------------------
dup_id_mask = df["ID"].duplicated(keep=False)
log(f"\n[0c] Số dòng còn liên quan đến ID trùng (key issue) sau khi loại dup hoàn toàn: {dup_id_mask.sum()}", LOGFILE)
log(df.loc[dup_id_mask, ["ID", "Year_Birth", "Education", "Marital_Status", "Income"]].to_string(), LOGFILE)

df["_n_missing"] = df.isna().sum(axis=1)
df = (
    df.sort_values("_n_missing")
    .drop_duplicates(subset="ID", keep="first")
    .drop(columns="_n_missing")
    .sort_index()
    .copy()
)
log(f"Kích thước sau khi xử lý ID trùng (giữ bản ghi đầy đủ hơn): {df.shape}", LOGFILE)

df = df.reset_index(drop=True)

# ---------------------------------------------------------------------------
# (i) ĐIỀN GIÁ TRỊ CÒN THIẾU - 5 trường hợp, dùng công thức tính toán phức tạp hơn mean/mode/median đơn giản
# ---------------------------------------------------------------------------
log("\n" + "=" * 70, LOGFILE)
log("(i) ĐIỀN GIÁ TRỊ CÒN THIẾU", LOGFILE)
log("=" * 70, LOGFILE)

# Trường hợp 1: Income (liên tục) -> median theo nhóm (Education, Marital_Status), làm tròn đến hàng trăm
log("\n-- Trường hợp 1: Income --", LOGFILE)
n_missing_income = df["Income"].isna().sum()
group_median = df.groupby(["Education", "Marital_Status"])["Income"].transform(
    lambda s: np.round(s.median(), -2)
)
overall_median = np.round(df["Income"].median(), -2)
fill_income = group_median.fillna(overall_median)
log(f"Số giá trị NULL trước khi điền: {n_missing_income}", LOGFILE)
df.loc[df["Income"].isna(), "Income"] = fill_income[df["Income"].isna()]
log(f"Số giá trị NULL sau khi điền: {df['Income'].isna().sum()}", LOGFILE)
log("Công thức: median(Income) theo nhóm (Education, Marital_Status), làm tròn đến hàng trăm; "
    "nếu nhóm không có dữ liệu thì dùng median toàn cục.", LOGFILE)

# Trường hợp 2: Year_Birth (rời rạc) -> mode; nếu có nhiều mode chọn mode thấp nhất
log("\n-- Trường hợp 2: Year_Birth --", LOGFILE)
n_missing_yb = df["Year_Birth"].isna().sum()
yb_mode = lowest_mode(df["Year_Birth"])
log(f"Số giá trị NULL trước khi điền: {n_missing_yb}; mode (thấp nhất nếu có nhiều mode) = {yb_mode}", LOGFILE)
df["Year_Birth"] = df["Year_Birth"].fillna(yb_mode)
log(f"Số giá trị NULL sau khi điền: {df['Year_Birth'].isna().sum()}", LOGFILE)

# Trường hợp 3: Education (thứ tự) -> mode theo nhóm Marital_Status; tie-break theo mode thấp nhất
log("\n-- Trường hợp 3: Education --", LOGFILE)
n_missing_edu = df["Education"].isna().sum()


def mode_in_group(s):
    m = s.mode(dropna=True)
    return m.iloc[0] if len(m) else np.nan


edu_group_mode = df.groupby("Marital_Status")["Education"].transform(mode_in_group)
edu_overall_mode = df["Education"].mode(dropna=True).iloc[0]
df.loc[df["Education"].isna(), "Education"] = edu_group_mode[df["Education"].isna()].fillna(edu_overall_mode)
log(f"Số giá trị NULL trước khi điền: {n_missing_edu}; sau khi điền: {df['Education'].isna().sum()}", LOGFILE)
log("Công thức: mode(Education) theo nhóm Marital_Status; nếu nhóm rỗng dùng mode toàn cục.", LOGFILE)

# Trường hợp 4: Marital_Status (danh nghĩa) -> mode theo nhóm Education
log("\n-- Trường hợp 4: Marital_Status --", LOGFILE)
n_missing_ms = df["Marital_Status"].isna().sum()
ms_group_mode = df.groupby("Education")["Marital_Status"].transform(mode_in_group)
ms_overall_mode = df["Marital_Status"].mode(dropna=True).iloc[0]
df.loc[df["Marital_Status"].isna(), "Marital_Status"] = ms_group_mode[df["Marital_Status"].isna()].fillna(ms_overall_mode)
log(f"Số giá trị NULL trước khi điền: {n_missing_ms}; sau khi điền: {df['Marital_Status'].isna().sum()}", LOGFILE)
log("Công thức: mode(Marital_Status) theo nhóm Education.", LOGFILE)

# Trường hợp 5: Dt_Customer (ngày) -> median ngày (chuyển sang epoch day, tính median, chuyển ngược lại)
log("\n-- Trường hợp 5: Dt_Customer --", LOGFILE)
dt_parsed = pd.to_datetime(df[DATE_COL].str.strip(), format="%Y-%m-%d", errors="coerce")
n_missing_dt = dt_parsed.isna().sum()
epoch_days = (dt_parsed - pd.Timestamp("1970-01-01")).dt.days
median_epoch = int(np.round(epoch_days.median()))
median_date = pd.Timestamp("1970-01-01") + pd.Timedelta(days=median_epoch)
dt_parsed = dt_parsed.fillna(median_date)
log(f"Số giá trị NULL/không hợp lệ trước khi điền: {n_missing_dt}; median ngày = {median_date.date()}", LOGFILE)
log(f"Số giá trị NULL sau khi điền: {dt_parsed.isna().sum()}", LOGFILE)
df[DATE_COL] = dt_parsed  # lưu dạng datetime, sẽ format lại ở bước (iv)

# Các field số còn lại (nếu còn NaN rải rác, ví dụ do các dòng gốc bị xoá) -> median toàn cục (dự phòng)
other_numeric = [c for c in NUMERIC_COLS + BOOLEAN_COLS if c not in ["Income", "Year_Birth"]]
for col in other_numeric:
    if df[col].isna().any():
        med = df[col].median()
        log(f"[Dự phòng] Điền nốt {df[col].isna().sum()} NaN còn lại ở '{col}' bằng median = {med}", LOGFILE)
        df[col] = df[col].fillna(med)

log(f"\n>>> Tổng số NaN còn lại sau bước (i): {int(df.isna().sum().sum())}", LOGFILE)

# ---------------------------------------------------------------------------
# (ii) LÀM MỊN DỮ LIỆU
# ---------------------------------------------------------------------------
log("\n" + "=" * 70, LOGFILE)
log("(ii) LÀM MỊN DỮ LIỆU", LOGFILE)
log("=" * 70, LOGFILE)

ranges = {c: df[c].max() - df[c].min() for c in NUMERIC_COLS}
range_col = max(ranges, key=ranges.get)
log(f"\nMiền giá trị (range) từng thuộc tính số:\n{pd.Series(ranges).sort_values(ascending=False).to_string()}", LOGFILE)
log(f"\n>> Thuộc tính có miền giá trị LỚN NHẤT: '{range_col}' (range = {ranges[range_col]:,.0f})", LOGFILE)
log(">> Phương pháp làm mịn được chọn: smoothing theo giá trị trung bình (mean) của từng nhóm (bin).", LOGFILE)

N_BINS = 6
df["_bin"] = pd.cut(df[range_col], bins=N_BINS)
bin_means = df.groupby("_bin")[range_col].transform("mean")
log(f"\nSố nhóm (bins) = {N_BINS}. Biên các nhóm:", LOGFILE)
log(df["_bin"].cat.categories.astype(str).tolist(), LOGFILE)
df[f"{range_col}_smoothed"] = bin_means.round(2)
log(f"Đã tạo cột mới '{range_col}_smoothed' = giá trị trung bình của nhóm chứa nó.", LOGFILE)
log(df[[range_col, "_bin", f"{range_col}_smoothed"]].head(10).to_string(), LOGFILE)
df = df.drop(columns="_bin")

stds = {c: df[c].std() for c in NUMERIC_COLS}
std_col = max(stds, key=stds.get)
log(f"\nĐộ lệch chuẩn từng thuộc tính số:\n{pd.Series(stds).sort_values(ascending=False).to_string()}", LOGFILE)
log(f"\n>> Thuộc tính có ĐỘ LỆCH CHUẨN LỚN NHẤT: '{std_col}' (std = {stds[std_col]:,.2f})", LOGFILE)

sorted_vals = df[std_col].sort_values()
smallest5_idx = sorted_vals.index[:5]
largest5_idx = sorted_vals.index[-5:]
log(f"5 giá trị nhỏ nhất (index): {list(smallest5_idx)} -> {df.loc[smallest5_idx, std_col].tolist()}", LOGFILE)
log(f"5 giá trị lớn nhất (index): {list(largest5_idx)} -> {df.loc[largest5_idx, std_col].tolist()}", LOGFILE)

df.loc[smallest5_idx, std_col] = (df.loc[smallest5_idx, std_col] * 1.10).round(2)
df.loc[largest5_idx, std_col] = (df.loc[largest5_idx, std_col] * 0.90).round(2)
log(f"Sau điều chỉnh (+10% cho 5 giá trị nhỏ nhất, -10% cho 5 giá trị lớn nhất):", LOGFILE)
log(f"  nhỏ nhất -> {df.loc[smallest5_idx, std_col].tolist()}", LOGFILE)
log(f"  lớn nhất -> {df.loc[largest5_idx, std_col].tolist()}", LOGFILE)

# ---------------------------------------------------------------------------
# (iii) XÁC ĐỊNH GIÁ TRỊ NGOẠI LỆ (Five-number summary / IQR)
# ---------------------------------------------------------------------------
log("\n" + "=" * 70, LOGFILE)
log("(iii) XÁC ĐỊNH GIÁ TRỊ NGOẠI LỆ (Five-Number Summary)", LOGFILE)
log("=" * 70, LOGFILE)

outlier_summary = []
for col in NUMERIC_COLS:
    q0, q1, q2, q3, q4 = df[col].min(), df[col].quantile(0.25), df[col].median(), df[col].quantile(0.75), df[col].max()
    iqr = q3 - q1
    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    n_out = ((df[col] < lower) | (df[col] > upper)).sum()
    outlier_summary.append(dict(field=col, min=q0, Q1=q1, median=q2, Q3=q3, max=q4,
                                 IQR=iqr, lower_bound=lower, upper_bound=upper, n_outliers=n_out))

outlier_df = pd.DataFrame(outlier_summary)
log(outlier_df.to_string(index=False), LOGFILE)
outlier_df.to_csv(OUT_DIR / "02_outlier_five_number_summary.csv", index=False)

# Xử lý ngoại lệ: PHÂN BIỆT 2 nhóm outlier thay vì clip đồng loạt toàn bộ field số
#   - Nhóm A (các field Mnt*/Num*): outlier phản ánh hành vi chi tiêu/mua sắm tự nhiên của
#     từng khách hàng (phân phối lệch phải) -> đây là đặc điểm thật của dữ liệu, KHÔNG phải lỗi,
#     nên GIỮ NGUYÊN, chỉ ghi nhận lại trong five-number-summary ở trên để phục vụ phân tích.
#   - Nhóm B (Income, Year_Birth, Recency): các giá trị vượt xa biên IQR RẤT NHIỀU lần và đồng thời
#     vi phạm ràng buộc nghiệp vụ hiển nhiên (thu nhập âm, thu nhập 2.500.000 gấp ~15 lần Q3,
#     năm sinh 1893 -> tuổi >120, Recency = 999 trong khi miền hợp lệ là 0-99 ngày)
#     -> đây chính là các outlier đã bị CHỦ ĐỘNG CHÈN LỖI, cần xử lý (winsorize theo biên IQR).
log("\n>> Quyết định xử lý: CHỈ winsorize (clip theo biên IQR) cho Income, Year_Birth, Recency "
    "vì đây là các outlier do lỗi nhập liệu/chèn lỗi có chủ đích (vi phạm ràng buộc nghiệp vụ). "
    "Các field Mnt*/Num* được GIỮ NGUYÊN vì outlier phản ánh hành vi mua sắm thật của khách hàng.", LOGFILE)
log(">> Riêng Income: biên dưới IQR tính ra vẫn âm (~-12.782), nhưng thu nhập không thể âm "
    "về nghiệp vụ -> chặn thêm biên dưới tại 0 (MAX(lower_bound, 0)) trước khi winsorize.", LOGFILE)

TREAT_AS_ERROR_OUTLIER = ["Income", "Year_Birth", "Recency"]
before_extremes = {
    "Income_max_before": df["Income"].max(),
    "Income_min_before": df["Income"].min(),
    "Year_Birth_min_before": df["Year_Birth"].min(),
    "Recency_max_before": df["Recency"].max(),
}
# Income: biên dưới IQR (~-12.782) vẫn âm, trong khi thu nhập không thể âm về nghiệp vụ
# -> chặn thêm biên dưới tại 0 (business-rule floor) trước khi winsorize.
for row in outlier_summary:
    if row["field"] in TREAT_AS_ERROR_OUTLIER:
        lower = max(row["lower_bound"], 0) if row["field"] == "Income" else row["lower_bound"]
        df[row["field"]] = df[row["field"]].clip(lower=lower, upper=row["upper_bound"])

log(f"Trước xử lý: {before_extremes}", LOGFILE)
log(f"Sau xử lý  : Income[min={df['Income'].min()}, max={df['Income'].max()}], "
    f"Year_Birth[min={df['Year_Birth'].min()}], Recency[max={df['Recency'].max()}]", LOGFILE)
log(f"Số outlier được GIỮ NGUYÊN (không xử lý) ở các field Mnt*/Num*: "
    f"{sum(r['n_outliers'] for r in outlier_summary if r['field'] not in TREAT_AS_ERROR_OUTLIER)} giá trị "
    f"trên {len([r for r in outlier_summary if r['field'] not in TREAT_AS_ERROR_OUTLIER])} field.", LOGFILE)

# ---------------------------------------------------------------------------
# (iv) XỬ LÝ DỮ LIỆU KHÔNG NHẤT QUÁN
# ---------------------------------------------------------------------------
log("\n" + "=" * 70, LOGFILE)
log("(iv) XỬ LÝ DỮ LIỆU KHÔNG NHẤT QUÁN", LOGFILE)
log("=" * 70, LOGFILE)

log("\n-- (iv.1) Field kiểu NGÀY (Dt_Customer) --", LOGFILE)
log("Chuyển kiểu dữ liệu ngày hiện tại (yyyy-mm-dd) thành chuỗi, sau đó CHỦ ĐỘNG sửa 5 giá trị "
    "sang định dạng khác (dd/mm/yyyy) để mô phỏng lỗi không nhất quán, rồi viết lệnh phát hiện & "
    "chuẩn hoá lại về yyyy-mm-dd.", LOGFILE)

df[DATE_COL] = df[DATE_COL].dt.strftime("%Y-%m-%d")  # đổi kiểu dữ liệu ngày -> chuỗi

demo_idx = df.index[:5]
original_demo_values = df.loc[demo_idx, DATE_COL].copy()
# chủ động sửa 5 giá trị sang định dạng dd/mm/yyyy
corrupted_demo_values = pd.to_datetime(original_demo_values).dt.strftime("%d/%m/%Y")
df.loc[demo_idx, DATE_COL] = corrupted_demo_values
log(f"5 giá trị gốc (yyyy-mm-dd): {original_demo_values.tolist()}", LOGFILE)
log(f"5 giá trị sau khi SV chủ động làm lỗi định dạng (dd/mm/yyyy): {df.loc[demo_idx, DATE_COL].tolist()}", LOGFILE)


def normalize_date(v: str) -> str:
    """Phát hiện định dạng và chuẩn hoá mọi giá trị về yyyy-mm-dd."""
    v = v.strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y"):
        try:
            return pd.to_datetime(v, format=fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return pd.to_datetime(v, errors="coerce")


df[DATE_COL] = df[DATE_COL].astype(str).apply(normalize_date)
log(f"5 giá trị sau khi chuẩn hoá lại: {df.loc[demo_idx, DATE_COL].tolist()}", LOGFILE)
match = (df.loc[demo_idx, DATE_COL].values == original_demo_values.values).all()
log(f"Khớp hoàn toàn với giá trị gốc sau khi sửa lỗi: {match}", LOGFILE)

# đồng thời xử lý khoảng trắng thừa vốn có sẵn trong file before cho toàn bộ cột ngày
df[DATE_COL] = df[DATE_COL].astype(str).str.strip()

log("\n-- (iv.2) Field kiểu DANH NGHĨA/THỨ TỰ (Marital_Status, Education) --", LOGFILE)
log("Trước tiên xử lý các lỗi CÓ SẴN trong dữ liệu bẩn: khoảng trắng thừa + không nhất quán hoa/thường.", LOGFILE)

canonical_education = {e.lower(): e for e in ["Basic", "2n Cycle", "Graduation", "Master", "PhD"]}
canonical_marital = {m.lower(): m for m in ["Single", "Married", "Together", "Divorced", "Widow", "Alone", "Absurd", "YOLO"]}

df["Education"] = df["Education"].astype(str).str.strip()
df["Education"] = df["Education"].apply(lambda v: canonical_education.get(v.lower(), v))

df["Marital_Status"] = df["Marital_Status"].astype(str).str.strip()
df["Marital_Status"] = df["Marital_Status"].apply(lambda v: canonical_marital.get(v.lower(), v))

log(f"Education sau chuẩn hoá: {sorted(df['Education'].unique())}", LOGFILE)
log(f"Marital_Status sau chuẩn hoá: {sorted(df['Marital_Status'].unique())}", LOGFILE)

log("\nMô phỏng thêm: SV chủ động làm lỗi 5 giá trị Education rồi tự sửa lại bằng lệnh hiệu chỉnh.", LOGFILE)
demo_idx2 = df.index[5:10]
original_demo_edu = df.loc[demo_idx2, "Education"].copy()
# chủ động làm lỗi: đổi hoa/thường + chèn khoảng trắng ngẫu nhiên
corrupt_fn = [str.upper, str.lower, lambda s: "  " + s + "  ", str.title, lambda s: s.replace(" ", "")]
corrupted = [f(v) for f, v in zip(corrupt_fn, original_demo_edu)]
df.loc[demo_idx2, "Education"] = corrupted
log(f"Giá trị gốc: {original_demo_edu.tolist()}", LOGFILE)
log(f"Giá trị sau khi chủ động làm lỗi: {corrupted}", LOGFILE)

# lệnh hiệu chỉnh lại: strip + map theo canonical (so khớp không phân biệt hoa/thường và khoảng trắng)
nospace_map = {e.lower().replace(" ", ""): e for e in EDUCATION_ORDER}
df.loc[demo_idx2, "Education"] = df.loc[demo_idx2, "Education"].apply(
    lambda v: nospace_map.get(v.strip().lower().replace(" ", ""), v.strip())
)
log(f"Giá trị sau khi hiệu chỉnh lại: {df.loc[demo_idx2, 'Education'].tolist()}", LOGFILE)
log(f"Khớp hoàn toàn với giá trị gốc: {(df.loc[demo_idx2, 'Education'].values == original_demo_edu.values).all()}", LOGFILE)

# ---------------------------------------------------------------------------
# Lưu kết quả trung gian
# ---------------------------------------------------------------------------
df.to_csv(AFTER_CLEAN_CSV, index=False)
log(f"\n>>> Đã lưu dữ liệu sau bước Data Cleaning vào: {AFTER_CLEAN_CSV}", LOGFILE)
log(f">>> Kích thước cuối cùng sau Data Cleaning: {df.shape}", LOGFILE)
print(f"\n>>> Log chi tiết: {LOGFILE}")
