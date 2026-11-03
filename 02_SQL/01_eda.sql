-- ============================================================================
-- Bước 3.a - Giới thiệu bộ dữ liệu thô ban đầu (dùng SQL / SQLite)
-- Thống kê số lượng giá trị của các field định danh/thứ tự để phát hiện giá trị
-- không nhất quán, đồng thời rà soát NULL, trùng lặp.
-- Bảng nguồn: customers_before (import nguyên trạng từ file 'before', kiểu TEXT)
-- ============================================================================

-- 1) Value counts cho Education (phát hiện khoảng trắng thừa + "phd" viết thường)
SELECT Education, COUNT(*) AS so_luong
FROM customers_before
GROUP BY Education
ORDER BY so_luong DESC;

-- 2) Value counts cho Marital_Status (phát hiện "single", "MARRIED", khoảng trắng thừa)
SELECT Marital_Status, COUNT(*) AS so_luong
FROM customers_before
GROUP BY Marital_Status
ORDER BY so_luong DESC;

-- 3) Đếm NULL theo từng field quan trọng
SELECT
    SUM(CASE WHEN ID IS NULL THEN 1 ELSE 0 END) AS null_ID,
    SUM(CASE WHEN Year_Birth IS NULL THEN 1 ELSE 0 END) AS null_Year_Birth,
    SUM(CASE WHEN Education IS NULL THEN 1 ELSE 0 END) AS null_Education,
    SUM(CASE WHEN Marital_Status IS NULL THEN 1 ELSE 0 END) AS null_Marital_Status,
    SUM(CASE WHEN Income IS NULL THEN 1 ELSE 0 END) AS null_Income,
    SUM(CASE WHEN Dt_Customer IS NULL THEN 1 ELSE 0 END) AS null_Dt_Customer
FROM customers_before;

-- 4) Số dòng trống hoàn toàn (toàn bộ field đều NULL -> ID cũng NULL)
SELECT COUNT(*) AS so_dong_trong
FROM customers_before
WHERE ID IS NULL;

-- 5) Số ID bị trùng lặp (key issue)
SELECT ID, COUNT(*) AS so_lan_xuat_hien
FROM customers_before
WHERE ID IS NOT NULL
GROUP BY ID
HAVING COUNT(*) > 1;

-- 6) Số dòng trùng lặp hoàn toàn (duplicate rows) trên toàn bộ các cột
SELECT COUNT(*) AS so_dong_du_thua FROM (
    SELECT ID, Year_Birth, Education, Marital_Status, Income, Kidhome, Teenhome,
           Dt_Customer, Recency, MntWines, MntFruits, MntMeatProducts, MntFishProducts,
           MntSweetProducts, MntGoldProds, NumDealsPurchases, NumWebPurchases,
           NumCatalogPurchases, NumStorePurchases, NumWebVisitsMonth,
           AcceptedCmp3, AcceptedCmp4, AcceptedCmp5, AcceptedCmp1, AcceptedCmp2,
           Complain, Z_CostContact, Z_Revenue, Response, COUNT(*) AS cnt
    FROM customers_before
    WHERE ID IS NOT NULL
    GROUP BY ID, Year_Birth, Education, Marital_Status, Income, Kidhome, Teenhome,
             Dt_Customer, Recency, MntWines, MntFruits, MntMeatProducts, MntFishProducts,
             MntSweetProducts, MntGoldProds, NumDealsPurchases, NumWebPurchases,
             NumCatalogPurchases, NumStorePurchases, NumWebVisitsMonth,
             AcceptedCmp3, AcceptedCmp4, AcceptedCmp5, AcceptedCmp1, AcceptedCmp2,
             Complain, Z_CostContact, Z_Revenue, Response
    HAVING COUNT(*) > 1
);

-- 7) Field Income: thống kê nhanh để phát hiện ngoại lệ (-15000 và 2500000)
SELECT MIN(CAST(Income AS REAL)) AS income_min, MAX(CAST(Income AS REAL)) AS income_max
FROM customers_before WHERE Income IS NOT NULL;

-- 8) Field Recency: phát hiện giá trị 999 bất thường (miền hợp lệ 0-99)
SELECT COUNT(*) AS so_dong_recency_999
FROM customers_before WHERE CAST(Recency AS REAL) = 999;

-- 9) Field Year_Birth: phát hiện giá trị không phải số ("Unknown") và năm quá nhỏ
SELECT Year_Birth, COUNT(*) AS so_luong
FROM customers_before
WHERE Year_Birth IS NOT NULL AND CAST(Year_Birth AS INTEGER) = 0
GROUP BY Year_Birth;
