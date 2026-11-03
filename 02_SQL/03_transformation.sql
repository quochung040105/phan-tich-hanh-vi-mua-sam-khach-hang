-- ============================================================================
-- Bước 3.c, 3.d, 3.e (dùng SQL / SQLite)
-- Input : bảng customers_work (đã làm sạch ở 02_cleaning.sql)
-- Output: bảng customers_after (file 'after' cuối cùng, pipeline SQL)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- (c) TÍCH HỢP DỮ LIỆU: bộ dữ liệu chỉ có 1 bảng nguồn -> không áp dụng (N/A).
-- Ghi chú chi tiết được trình bày trong báo cáo (05_Report), SQL không cần join
-- bảng nào khác ở đây.
-- ----------------------------------------------------------------------------

-- ----------------------------------------------------------------------------
-- (d) GIẢM THIỂU DỮ LIỆU (Data Reduction)
-- ----------------------------------------------------------------------------

-- Trường hợp 1: Giảm chiều - kiểm chứng Z_CostContact, Z_Revenue là hằng số rồi loại bỏ
SELECT COUNT(DISTINCT Z_CostContact) AS so_gia_tri_duy_nhat_Z_CostContact,
       COUNT(DISTINCT Z_Revenue) AS so_gia_tri_duy_nhat_Z_Revenue
FROM customers_work;

ALTER TABLE customers_work DROP COLUMN Z_CostContact;
ALTER TABLE customers_work DROP COLUMN Z_Revenue;

-- Trường hợp 2: Giảm số bản ghi - minh hoạ lấy mẫu phân tầng (stratified sampling) 20% theo Education
DROP TABLE IF EXISTS customers_sample_demo;
CREATE TABLE customers_sample_demo AS
SELECT * FROM (
    SELECT *,
           ROW_NUMBER() OVER (PARTITION BY Education ORDER BY RANDOM()) AS rn_,
           COUNT(*) OVER (PARTITION BY Education) AS grp_cnt_
    FROM customers_work
)
WHERE rn_ <= CAST(grp_cnt_ * 0.2 AS INTEGER);

SELECT (SELECT COUNT(*) FROM customers_work) AS so_dong_goc,
       (SELECT COUNT(*) FROM customers_sample_demo) AS so_dong_mau_20_phan_tram;

-- ----------------------------------------------------------------------------
-- (e) CHUYỂN ĐỔI & PHÂN TÁCH DỮ LIỆU
-- ----------------------------------------------------------------------------

-- (e.1) Education (thứ tự) -> số nguyên
ALTER TABLE customers_work ADD COLUMN Education_encoded INTEGER;
UPDATE customers_work SET Education_encoded = CASE Education
    WHEN 'Basic' THEN 0 WHEN '2n Cycle' THEN 1 WHEN 'Graduation' THEN 2
    WHEN 'Master' THEN 3 WHEN 'PhD' THEN 4 END;

SELECT DISTINCT Education, Education_encoded FROM customers_work ORDER BY Education_encoded;

-- (e.2) Marital_Status (danh mục) -> số nguyên
ALTER TABLE customers_work ADD COLUMN Marital_Status_encoded INTEGER;
UPDATE customers_work SET Marital_Status_encoded = CASE Marital_Status
    WHEN 'Absurd' THEN 0 WHEN 'Alone' THEN 1 WHEN 'Divorced' THEN 2 WHEN 'Married' THEN 3
    WHEN 'Single' THEN 4 WHEN 'Together' THEN 5 WHEN 'Widow' THEN 6 WHEN 'YOLO' THEN 7 END;

SELECT DISTINCT Marital_Status, Marital_Status_encoded FROM customers_work ORDER BY Marital_Status_encoded;

-- (e.3) Gộp 7 field boolean (AcceptedCmp1-5, Complain, Response) thành 1 field bitmask
ALTER TABLE customers_work ADD COLUMN Campaigns_Response_Bitmask INTEGER;
UPDATE customers_work
SET Campaigns_Response_Bitmask =
    CAST(AcceptedCmp3 AS INTEGER) * 1 + CAST(AcceptedCmp4 AS INTEGER) * 2 +
    CAST(AcceptedCmp5 AS INTEGER) * 4 + CAST(AcceptedCmp1 AS INTEGER) * 8 +
    CAST(AcceptedCmp2 AS INTEGER) * 16 + CAST(Complain AS INTEGER) * 32 +
    CAST(Response AS INTEGER) * 64;

SELECT AcceptedCmp3, AcceptedCmp4, AcceptedCmp5, AcceptedCmp1, AcceptedCmp2, Complain, Response,
       Campaigns_Response_Bitmask
FROM customers_work LIMIT 8;

-- (e.4) Field CHUỖI chứa danh sách chuỗi con: xây dựng 'Products_Purchased' từ 6 field Mnt*,
-- tách thành field trung gian boolean rồi gộp lại thành 1 field bitmask (giống (c))
ALTER TABLE customers_work ADD COLUMN Products_Purchased TEXT;
UPDATE customers_work
SET Products_Purchased = RTRIM(
    (CASE WHEN MntWines > 0 THEN 'Wines, ' ELSE '' END) ||
    (CASE WHEN MntFruits > 0 THEN 'Fruits, ' ELSE '' END) ||
    (CASE WHEN MntMeatProducts > 0 THEN 'Meat, ' ELSE '' END) ||
    (CASE WHEN MntFishProducts > 0 THEN 'Fish, ' ELSE '' END) ||
    (CASE WHEN MntSweetProducts > 0 THEN 'Sweet, ' ELSE '' END) ||
    (CASE WHEN MntGoldProds > 0 THEN 'Gold, ' ELSE '' END),
    ', '
);

SELECT ID, Products_Purchased FROM customers_work LIMIT 8;

ALTER TABLE customers_work ADD COLUMN Product_Categories_Bitmask INTEGER;
UPDATE customers_work
SET Product_Categories_Bitmask =
    (CASE WHEN MntWines > 0 THEN 1 ELSE 0 END) + (CASE WHEN MntFruits > 0 THEN 2 ELSE 0 END) +
    (CASE WHEN MntMeatProducts > 0 THEN 4 ELSE 0 END) + (CASE WHEN MntFishProducts > 0 THEN 8 ELSE 0 END) +
    (CASE WHEN MntSweetProducts > 0 THEN 16 ELSE 0 END) + (CASE WHEN MntGoldProds > 0 THEN 32 ELSE 0 END);

SELECT ID, Products_Purchased, Product_Categories_Bitmask FROM customers_work LIMIT 8;

-- ----------------------------------------------------------------------------
-- Lưu bảng 'after' cuối cùng (pipeline SQL)
-- ----------------------------------------------------------------------------
DROP TABLE IF EXISTS customers_after;
CREATE TABLE customers_after AS SELECT * FROM customers_work;

SELECT COUNT(*) AS so_dong_cuoi_cung, COUNT(*) AS so_cot_kiem_tra FROM customers_after;
