-- ============================================================================
-- Bước 3.b - Làm sạch dữ liệu (Data Cleaning) bằng SQL (SQLite)
-- Input : bảng customers_before (TEXT, nguyên trạng)
-- Output: bảng customers_work (đã làm sạch, kiểu dữ liệu đúng)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- BƯỚC CHUẨN BỊ: tạo bảng làm việc với kiểu dữ liệu đúng (REAL/TEXT), đồng thời
-- TRIM khoảng trắng thừa và quy "Unknown" (Year_Birth) về NULL
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS customers_work;

CREATE TABLE customers_work (
    ID REAL, Year_Birth REAL, Education TEXT, Marital_Status TEXT, Income REAL,
    Kidhome REAL, Teenhome REAL, Dt_Customer TEXT, Recency REAL,
    MntWines REAL, MntFruits REAL, MntMeatProducts REAL, MntFishProducts REAL,
    MntSweetProducts REAL, MntGoldProds REAL,
    NumDealsPurchases REAL, NumWebPurchases REAL, NumCatalogPurchases REAL,
    NumStorePurchases REAL, NumWebVisitsMonth REAL,
    AcceptedCmp3 REAL, AcceptedCmp4 REAL, AcceptedCmp5 REAL, AcceptedCmp1 REAL,
    AcceptedCmp2 REAL, Complain REAL, Z_CostContact REAL, Z_Revenue REAL, Response REAL
);

INSERT INTO customers_work
SELECT
    CAST(ID AS REAL),
    CASE WHEN TRIM(Year_Birth) = 'Unknown' THEN NULL ELSE CAST(Year_Birth AS REAL) END,
    TRIM(Education), TRIM(Marital_Status), CAST(Income AS REAL),
    CAST(Kidhome AS REAL), CAST(Teenhome AS REAL), TRIM(Dt_Customer), CAST(Recency AS REAL),
    CAST(MntWines AS REAL), CAST(MntFruits AS REAL), CAST(MntMeatProducts AS REAL), CAST(MntFishProducts AS REAL),
    CAST(MntSweetProducts AS REAL), CAST(MntGoldProds AS REAL),
    CAST(NumDealsPurchases AS REAL), CAST(NumWebPurchases AS REAL), CAST(NumCatalogPurchases AS REAL),
    CAST(NumStorePurchases AS REAL), CAST(NumWebVisitsMonth AS REAL),
    CAST(AcceptedCmp3 AS REAL), CAST(AcceptedCmp4 AS REAL), CAST(AcceptedCmp5 AS REAL), CAST(AcceptedCmp1 AS REAL),
    CAST(AcceptedCmp2 AS REAL), CAST(Complain AS REAL), CAST(Z_CostContact AS REAL), CAST(Z_Revenue AS REAL), CAST(Response AS REAL)
FROM customers_before;

SELECT COUNT(*) AS so_dong_ban_dau FROM customers_work;

-- ----------------------------------------------------------------------------
-- 0a) Loại bỏ dòng trống hoàn toàn (ID NULL)
-- ----------------------------------------------------------------------------
DELETE FROM customers_work WHERE ID IS NULL;

SELECT COUNT(*) AS so_dong_sau_khi_xoa_dong_trong FROM customers_work;

-- ----------------------------------------------------------------------------
-- 0b) Loại bỏ dòng trùng lặp hoàn toàn (giữ rowid nhỏ nhất của mỗi nhóm)
-- ----------------------------------------------------------------------------
DELETE FROM customers_work
WHERE rowid NOT IN (
    SELECT MIN(rowid) FROM customers_work
    GROUP BY ID, Year_Birth, Education, Marital_Status, Income, Kidhome, Teenhome,
             Dt_Customer, Recency, MntWines, MntFruits, MntMeatProducts, MntFishProducts,
             MntSweetProducts, MntGoldProds, NumDealsPurchases, NumWebPurchases,
             NumCatalogPurchases, NumStorePurchases, NumWebVisitsMonth,
             AcceptedCmp3, AcceptedCmp4, AcceptedCmp5, AcceptedCmp1, AcceptedCmp2,
             Complain, Z_CostContact, Z_Revenue, Response
);

SELECT COUNT(*) AS so_dong_sau_khi_xoa_trung_lap_hoan_toan FROM customers_work;

-- ----------------------------------------------------------------------------
-- 0c) ID trùng lặp nhưng dữ liệu khác nhau (key issue) -> giữ bản ghi ít NULL nhất
-- ----------------------------------------------------------------------------
DELETE FROM customers_work
WHERE rowid NOT IN (
    SELECT rowid FROM (
        SELECT rowid,
            ROW_NUMBER() OVER (
                PARTITION BY ID
                ORDER BY (
                    (CASE WHEN Income IS NULL THEN 1 ELSE 0 END) +
                    (CASE WHEN Education IS NULL THEN 1 ELSE 0 END) +
                    (CASE WHEN Marital_Status IS NULL THEN 1 ELSE 0 END) +
                    (CASE WHEN Dt_Customer IS NULL THEN 1 ELSE 0 END)
                ) ASC, rowid ASC
            ) AS rn
        FROM customers_work
    )
    WHERE rn = 1
);

SELECT COUNT(*) AS so_dong_sau_khi_xu_ly_ID_trung FROM customers_work;

-- ============================================================================
-- (i) ĐIỀN GIÁ TRỊ CÒN THIẾU - 5 trường hợp
-- ============================================================================

-- Trường hợp 1: Income -> median theo nhóm Education (làm tròn đến hàng trăm)
SELECT COUNT(*) AS income_null_truoc_khi_dien FROM customers_work WHERE Income IS NULL;

CREATE TEMP TABLE income_median_by_edu AS
WITH ranked AS (
    SELECT Education, Income,
           ROW_NUMBER() OVER (PARTITION BY Education ORDER BY Income) AS rn,
           COUNT(*) OVER (PARTITION BY Education) AS cnt
    FROM customers_work WHERE Income IS NOT NULL AND Education IS NOT NULL
)
SELECT Education,
       CAST(ROUND(AVG(Income) / 100.0) AS INTEGER) * 100 AS median_income
FROM ranked
WHERE rn IN ((cnt + 1) / 2, (cnt + 2) / 2)
GROUP BY Education;

SELECT * FROM income_median_by_edu;

UPDATE customers_work
SET Income = (SELECT median_income FROM income_median_by_edu WHERE income_median_by_edu.Education = customers_work.Education)
WHERE Income IS NULL AND Education IS NOT NULL
  AND EXISTS (SELECT 1 FROM income_median_by_edu WHERE income_median_by_edu.Education = customers_work.Education);

CREATE TEMP TABLE income_median_global AS
WITH ranked AS (
    SELECT Income, ROW_NUMBER() OVER (ORDER BY Income) AS rn, COUNT(*) OVER () AS cnt
    FROM customers_work WHERE Income IS NOT NULL
)
SELECT CAST(ROUND(AVG(Income) / 100.0) AS INTEGER) * 100 AS median_income
FROM ranked WHERE rn IN ((cnt + 1) / 2, (cnt + 2) / 2);

UPDATE customers_work SET Income = (SELECT median_income FROM income_median_global) WHERE Income IS NULL;

SELECT COUNT(*) AS income_null_sau_khi_dien FROM customers_work WHERE Income IS NULL;

-- Trường hợp 2: Year_Birth -> mode (nếu nhiều mode, chọn mode thấp nhất)
SELECT COUNT(*) AS year_birth_null_truoc_khi_dien FROM customers_work WHERE Year_Birth IS NULL;

CREATE TEMP TABLE yb_mode AS
SELECT Year_Birth, COUNT(*) AS cnt
FROM customers_work WHERE Year_Birth IS NOT NULL
GROUP BY Year_Birth
ORDER BY cnt DESC, Year_Birth ASC
LIMIT 1;

SELECT * FROM yb_mode;

UPDATE customers_work SET Year_Birth = (SELECT Year_Birth FROM yb_mode) WHERE Year_Birth IS NULL;

SELECT COUNT(*) AS year_birth_null_sau_khi_dien FROM customers_work WHERE Year_Birth IS NULL;

-- Trường hợp 3: Education -> mode theo nhóm Marital_Status
SELECT COUNT(*) AS education_null_truoc_khi_dien FROM customers_work WHERE Education IS NULL;

CREATE TEMP TABLE edu_mode_by_marital AS
WITH edu_counts AS (
    SELECT Marital_Status, Education, COUNT(*) AS cnt
    FROM customers_work WHERE Education IS NOT NULL AND Marital_Status IS NOT NULL
    GROUP BY Marital_Status, Education
),
edu_ranked AS (
    SELECT Marital_Status, Education, cnt,
           ROW_NUMBER() OVER (PARTITION BY Marital_Status ORDER BY cnt DESC, Education ASC) AS rn
    FROM edu_counts
)
SELECT Marital_Status, Education FROM edu_ranked WHERE rn = 1;

SELECT * FROM edu_mode_by_marital;

UPDATE customers_work
SET Education = (SELECT Education FROM edu_mode_by_marital WHERE edu_mode_by_marital.Marital_Status = customers_work.Marital_Status)
WHERE Education IS NULL AND Marital_Status IS NOT NULL
  AND EXISTS (SELECT 1 FROM edu_mode_by_marital WHERE edu_mode_by_marital.Marital_Status = customers_work.Marital_Status);

CREATE TEMP TABLE edu_mode_global AS
SELECT Education, COUNT(*) AS cnt FROM customers_work WHERE Education IS NOT NULL
GROUP BY Education ORDER BY cnt DESC, Education ASC LIMIT 1;

UPDATE customers_work SET Education = (SELECT Education FROM edu_mode_global) WHERE Education IS NULL;

SELECT COUNT(*) AS education_null_sau_khi_dien FROM customers_work WHERE Education IS NULL;

-- Trường hợp 4: Marital_Status -> mode theo nhóm Education
SELECT COUNT(*) AS marital_null_truoc_khi_dien FROM customers_work WHERE Marital_Status IS NULL;

CREATE TEMP TABLE marital_mode_by_edu AS
WITH ms_counts AS (
    SELECT Education, Marital_Status, COUNT(*) AS cnt
    FROM customers_work WHERE Marital_Status IS NOT NULL AND Education IS NOT NULL
    GROUP BY Education, Marital_Status
),
ms_ranked AS (
    SELECT Education, Marital_Status, cnt,
           ROW_NUMBER() OVER (PARTITION BY Education ORDER BY cnt DESC, Marital_Status ASC) AS rn
    FROM ms_counts
)
SELECT Education, Marital_Status FROM ms_ranked WHERE rn = 1;

SELECT * FROM marital_mode_by_edu;

UPDATE customers_work
SET Marital_Status = (SELECT Marital_Status FROM marital_mode_by_edu WHERE marital_mode_by_edu.Education = customers_work.Education)
WHERE Marital_Status IS NULL AND Education IS NOT NULL
  AND EXISTS (SELECT 1 FROM marital_mode_by_edu WHERE marital_mode_by_edu.Education = customers_work.Education);

SELECT COUNT(*) AS marital_null_sau_khi_dien FROM customers_work WHERE Marital_Status IS NULL;

-- Trường hợp 5: Dt_Customer -> median ngày (qua julianday)
SELECT COUNT(*) AS dt_null_truoc_khi_dien FROM customers_work WHERE Dt_Customer IS NULL;

CREATE TEMP TABLE dt_median AS
WITH ranked AS (
    SELECT Dt_Customer, julianday(Dt_Customer) AS jd,
           ROW_NUMBER() OVER (ORDER BY julianday(Dt_Customer)) AS rn,
           COUNT(*) OVER () AS cnt
    FROM customers_work WHERE Dt_Customer IS NOT NULL
)
SELECT date(AVG(jd)) AS median_date FROM ranked WHERE rn IN ((cnt + 1) / 2, (cnt + 2) / 2);

SELECT * FROM dt_median;

UPDATE customers_work SET Dt_Customer = (SELECT median_date FROM dt_median) WHERE Dt_Customer IS NULL;

SELECT COUNT(*) AS dt_null_sau_khi_dien FROM customers_work WHERE Dt_Customer IS NULL;

SELECT SUM(
    (CASE WHEN Income IS NULL THEN 1 ELSE 0 END) + (CASE WHEN Year_Birth IS NULL THEN 1 ELSE 0 END) +
    (CASE WHEN Education IS NULL THEN 1 ELSE 0 END) + (CASE WHEN Marital_Status IS NULL THEN 1 ELSE 0 END) +
    (CASE WHEN Dt_Customer IS NULL THEN 1 ELSE 0 END)
) AS tong_null_con_lai_5_field_chinh FROM customers_work;

-- ============================================================================
-- (ii) LÀM MỊN DỮ LIỆU
-- Field miền giá trị lớn nhất & độ lệch chuẩn lớn nhất đã xác định ở pipeline Python
-- là 'Income' -> áp dụng kỹ thuật làm mịn bằng equal-FREQUENCY binning (NTILE),
-- khác với equal-WIDTH binning (pd.cut) đã dùng ở Python, để minh hoạ thêm 1 kỹ thuật.
-- ============================================================================
ALTER TABLE customers_work ADD COLUMN Income_smoothed REAL;

CREATE TEMP TABLE income_bins AS
SELECT rowid AS rid, Income, NTILE(6) OVER (ORDER BY Income) AS bin
FROM customers_work;

CREATE TEMP TABLE income_bin_means AS
SELECT bin, AVG(Income) AS bin_mean FROM income_bins GROUP BY bin;

SELECT * FROM income_bin_means ORDER BY bin;

UPDATE customers_work
SET Income_smoothed = (
    SELECT ROUND(bm.bin_mean, 2) FROM income_bins ib JOIN income_bin_means bm ON ib.bin = bm.bin
    WHERE ib.rid = customers_work.rowid
);

-- Độ lệch chuẩn Income (SQLite không có hàm STDEV dựng sẵn -> tính thủ công sqrt(E[X^2]-E[X]^2))
SELECT
    AVG(Income) AS mean_income,
    SQRT(AVG(Income * Income) - AVG(Income) * AVG(Income)) AS std_income
FROM customers_work;

-- Tăng 10% cho 5 giá trị Income nhỏ nhất
UPDATE customers_work
SET Income = Income * 1.10
WHERE rowid IN (SELECT rowid FROM customers_work ORDER BY Income ASC LIMIT 5);

-- Giảm 10% cho 5 giá trị Income lớn nhất
UPDATE customers_work
SET Income = Income * 0.90
WHERE rowid IN (SELECT rowid FROM customers_work ORDER BY Income DESC LIMIT 5);

-- ============================================================================
-- (iii) XÁC ĐỊNH & XỬ LÝ GIÁ TRỊ NGOẠI LỆ (Five-Number Summary / IQR)
-- Áp dụng cho 3 field có outlier do lỗi nhập liệu: Income, Year_Birth, Recency
-- (phương pháp nearest-rank cho Q1/Q3, khác với phép nội suy tuyến tính của Python
--  - là một biến thể hợp lệ khác của five-number summary)
-- ============================================================================
CREATE TEMP TABLE income_bounds AS
WITH ranked AS (
    SELECT Income, ROW_NUMBER() OVER (ORDER BY Income) AS rn, COUNT(*) OVER () AS cnt
    FROM customers_work
),
q AS (
    SELECT
        (SELECT Income FROM ranked WHERE rn = CAST(cnt * 0.25 AS INTEGER) + 1) AS q1,
        (SELECT Income FROM ranked WHERE rn = CAST(cnt * 0.75 AS INTEGER) + 1) AS q3
    FROM ranked LIMIT 1
)
-- Biên dưới IQR tự nhiên ra âm (~-12.918), nhưng thu nhập không thể âm về nghiệp vụ
-- -> chặn thêm biên dưới tại 0 (MAX(lower_bound, 0)) trước khi winsorize.
SELECT q1, q3, (q3 - q1) AS iqr, MAX(q1 - 1.5 * (q3 - q1), 0) AS lower_b, q3 + 1.5 * (q3 - q1) AS upper_b FROM q;

SELECT 'Income' AS field, * FROM income_bounds;
SELECT COUNT(*) AS income_so_outlier
FROM customers_work, income_bounds
WHERE customers_work.Income < income_bounds.lower_b OR customers_work.Income > income_bounds.upper_b;

UPDATE customers_work
SET Income = CASE
    WHEN Income < (SELECT lower_b FROM income_bounds) THEN (SELECT lower_b FROM income_bounds)
    WHEN Income > (SELECT upper_b FROM income_bounds) THEN (SELECT upper_b FROM income_bounds)
    ELSE Income END;

CREATE TEMP TABLE yearbirth_bounds AS
WITH ranked AS (
    SELECT Year_Birth, ROW_NUMBER() OVER (ORDER BY Year_Birth) AS rn, COUNT(*) OVER () AS cnt
    FROM customers_work
),
q AS (
    SELECT
        (SELECT Year_Birth FROM ranked WHERE rn = CAST(cnt * 0.25 AS INTEGER) + 1) AS q1,
        (SELECT Year_Birth FROM ranked WHERE rn = CAST(cnt * 0.75 AS INTEGER) + 1) AS q3
    FROM ranked LIMIT 1
)
SELECT q1, q3, (q3 - q1) AS iqr, q1 - 1.5 * (q3 - q1) AS lower_b, q3 + 1.5 * (q3 - q1) AS upper_b FROM q;

SELECT 'Year_Birth' AS field, * FROM yearbirth_bounds;
SELECT COUNT(*) AS yearbirth_so_outlier
FROM customers_work, yearbirth_bounds
WHERE customers_work.Year_Birth < yearbirth_bounds.lower_b OR customers_work.Year_Birth > yearbirth_bounds.upper_b;

UPDATE customers_work
SET Year_Birth = CASE
    WHEN Year_Birth < (SELECT lower_b FROM yearbirth_bounds) THEN (SELECT lower_b FROM yearbirth_bounds)
    WHEN Year_Birth > (SELECT upper_b FROM yearbirth_bounds) THEN (SELECT upper_b FROM yearbirth_bounds)
    ELSE Year_Birth END;

CREATE TEMP TABLE recency_bounds AS
WITH ranked AS (
    SELECT Recency, ROW_NUMBER() OVER (ORDER BY Recency) AS rn, COUNT(*) OVER () AS cnt
    FROM customers_work
),
q AS (
    SELECT
        (SELECT Recency FROM ranked WHERE rn = CAST(cnt * 0.25 AS INTEGER) + 1) AS q1,
        (SELECT Recency FROM ranked WHERE rn = CAST(cnt * 0.75 AS INTEGER) + 1) AS q3
    FROM ranked LIMIT 1
)
SELECT q1, q3, (q3 - q1) AS iqr, q1 - 1.5 * (q3 - q1) AS lower_b, q3 + 1.5 * (q3 - q1) AS upper_b FROM q;

SELECT 'Recency' AS field, * FROM recency_bounds;
SELECT COUNT(*) AS recency_so_outlier
FROM customers_work, recency_bounds
WHERE customers_work.Recency < recency_bounds.lower_b OR customers_work.Recency > recency_bounds.upper_b;

UPDATE customers_work
SET Recency = CASE
    WHEN Recency < (SELECT lower_b FROM recency_bounds) THEN (SELECT lower_b FROM recency_bounds)
    WHEN Recency > (SELECT upper_b FROM recency_bounds) THEN (SELECT upper_b FROM recency_bounds)
    ELSE Recency END;

SELECT MIN(Income) AS income_min_sau, MAX(Income) AS income_max_sau,
       MIN(Year_Birth) AS yearbirth_min_sau, MAX(Recency) AS recency_max_sau
FROM customers_work;

-- ============================================================================
-- (iv) XỬ LÝ DỮ LIỆU KHÔNG NHẤT QUÁN
-- ============================================================================

-- (iv.1) Chuẩn hoá hoa/thường có sẵn trong dữ liệu bẩn (vd: 'phd', 'single', 'MARRIED')
UPDATE customers_work SET Education = 'PhD' WHERE LOWER(Education) = 'phd';
UPDATE customers_work SET Education = 'Graduation' WHERE LOWER(Education) = 'graduation';
UPDATE customers_work SET Education = 'Master' WHERE LOWER(Education) = 'master';
UPDATE customers_work SET Education = '2n Cycle' WHERE LOWER(Education) = '2n cycle';
UPDATE customers_work SET Education = 'Basic' WHERE LOWER(Education) = 'basic';

UPDATE customers_work SET Marital_Status = 'Single' WHERE LOWER(Marital_Status) = 'single';
UPDATE customers_work SET Marital_Status = 'Married' WHERE LOWER(Marital_Status) = 'married';
UPDATE customers_work SET Marital_Status = 'Together' WHERE LOWER(Marital_Status) = 'together';
UPDATE customers_work SET Marital_Status = 'Divorced' WHERE LOWER(Marital_Status) = 'divorced';
UPDATE customers_work SET Marital_Status = 'Widow' WHERE LOWER(Marital_Status) = 'widow';

SELECT DISTINCT Education FROM customers_work ORDER BY Education;
SELECT DISTINCT Marital_Status FROM customers_work ORDER BY Marital_Status;

-- (iv.2) DEMO: chủ động làm lỗi định dạng NGÀY cho 5 dòng rồi tự phát hiện & sửa lại
CREATE TEMP TABLE date_demo_backup AS
SELECT rowid AS rid, Dt_Customer AS original_value
FROM customers_work ORDER BY rowid LIMIT 5;

SELECT * FROM date_demo_backup;

-- chủ động sửa sang định dạng dd/mm/yyyy (khác định dạng chuẩn yyyy-mm-dd)
UPDATE customers_work
SET Dt_Customer = substr(Dt_Customer, 9, 2) || '/' || substr(Dt_Customer, 6, 2) || '/' || substr(Dt_Customer, 1, 4)
WHERE rowid IN (SELECT rid FROM date_demo_backup);

SELECT rowid, Dt_Customer FROM customers_work WHERE rowid IN (SELECT rid FROM date_demo_backup);

-- phát hiện định dạng dd/mm/yyyy (có dấu '/') và chuẩn hoá lại về yyyy-mm-dd
UPDATE customers_work
SET Dt_Customer = substr(Dt_Customer, 7, 4) || '-' || substr(Dt_Customer, 4, 2) || '-' || substr(Dt_Customer, 1, 2)
WHERE Dt_Customer LIKE '__/__/____';

SELECT b.rid, b.original_value, w.Dt_Customer AS value_after_fix,
       (b.original_value = w.Dt_Customer) AS khop_voi_ban_goc
FROM date_demo_backup b JOIN customers_work w ON b.rid = w.rowid;

-- (iv.3) DEMO: chủ động làm lỗi field DANH NGHĨA (Marital_Status) cho 5 dòng khác rồi sửa lại
CREATE TEMP TABLE marital_demo_backup AS
SELECT rowid AS rid, Marital_Status AS original_value
FROM customers_work ORDER BY rowid LIMIT 5 OFFSET 5;

SELECT * FROM marital_demo_backup;

UPDATE customers_work
SET Marital_Status = UPPER(Marital_Status)
WHERE rowid IN (SELECT rid FROM marital_demo_backup);

SELECT rowid, Marital_Status FROM customers_work WHERE rowid IN (SELECT rid FROM marital_demo_backup);

-- hiệu chỉnh lại: chữ cái đầu hoa, còn lại thường (Title Case)
UPDATE customers_work
SET Marital_Status = UPPER(SUBSTR(Marital_Status, 1, 1)) || LOWER(SUBSTR(Marital_Status, 2))
WHERE rowid IN (SELECT rid FROM marital_demo_backup);

SELECT b.rid, b.original_value, w.Marital_Status AS value_after_fix,
       (b.original_value = w.Marital_Status) AS khop_voi_ban_goc
FROM marital_demo_backup b JOIN customers_work w ON b.rid = w.rowid;

SELECT COUNT(*) AS so_dong_cuoi_cung_sau_cleaning FROM customers_work;
