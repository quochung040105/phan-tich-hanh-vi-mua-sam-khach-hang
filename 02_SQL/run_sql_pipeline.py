"""
Orchestrator chạy toàn bộ pipeline SQL (SQLite) cho bước Tiền xử lý dữ liệu.
Cách dùng:  python3 run_sql_pipeline.py
Yêu cầu: các file .sql trong cùng thư mục, chạy theo đúng thứ tự tên file.

Quy trình:
  1. Tạo database SQLite mới, import file 'before' (giữ nguyên dạng TEXT để không mất lỗi)
  2. Lần lượt chạy 01_eda.sql, 02_cleaning.sql, 03_transformation.sql
     - Với các câu lệnh SELECT (để xem/kiểm tra), kết quả được in ra và ghi log
     - Với các câu lệnh UPDATE/DELETE/CREATE/ALTER, thực thi trực tiếp
  3. Xuất bảng kết quả cuối cùng ra DATA/after_sql.csv
"""
import re
import sqlite3
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "DATA"
SQL_DIR = ROOT / "02_SQL"
OUT_DIR = ROOT / "outputs" / "sql"
OUT_DIR.mkdir(parents=True, exist_ok=True)

BEFORE_CSV = DATA_DIR / "NguyenQuocHung_customer_personality.csv"
DB_PATH = OUT_DIR / "pipeline.db"
AFTER_SQL_CSV = DATA_DIR / "after_sql.csv"
LOGFILE = OUT_DIR / "sql_run_log.txt"

SQL_FILES = ["01_eda.sql", "02_cleaning.sql", "03_transformation.sql"]


def log(msg, f):
    print(msg)
    f.write(str(msg) + "\n")


def split_statements(sql_text: str):
    """Tách file .sql thành từng statement (ngăn cách bởi dấu ';'), bỏ comment dòng '--'."""
    cleaned_lines = []
    for line in sql_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("--"):
            continue
        cleaned_lines.append(line)
    cleaned = "\n".join(cleaned_lines)
    stmts = [s.strip() for s in re.split(r";\s*(?:\n|$)", cleaned) if s.strip()]
    return stmts


def main():
    if DB_PATH.exists():
        DB_PATH.unlink()
    conn = sqlite3.connect(DB_PATH)

    with open(LOGFILE, "w", encoding="utf-8") as f:
        log(f"=== Khởi tạo database SQLite: {DB_PATH} ===", f)

        # Import file 'before' -> bảng customers_before (giữ nguyên dạng TEXT)
        before_df = pd.read_csv(BEFORE_CSV, dtype=str)
        before_df.to_sql("customers_before", conn, if_exists="replace", index=False)
        log(f"Đã import '{BEFORE_CSV.name}' vào bảng 'customers_before': {before_df.shape[0]} dòng x {before_df.shape[1]} cột", f)
        conn.commit()

        for sql_file in SQL_FILES:
            path = SQL_DIR / sql_file
            log(f"\n{'='*70}\n>>> ĐANG CHẠY: {sql_file}\n{'='*70}", f)
            statements = split_statements(path.read_text(encoding="utf-8"))
            for stmt in statements:
                first_word = stmt.strip().split(None, 1)[0].upper() if stmt.strip() else ""
                try:
                    cur = conn.execute(stmt)
                    if first_word == "SELECT":
                        cols = [d[0] for d in cur.description]
                        rows = cur.fetchall()
                        res_df = pd.DataFrame(rows, columns=cols)
                        log(f"\n-- SQL --\n{stmt}\n-- KẾT QUẢ ({len(res_df)} dòng, hiển thị tối đa 20) --", f)
                        log(res_df.head(20).to_string(index=False), f)
                    else:
                        conn.commit()
                        log(f"\n-- SQL --\n{stmt}\n-- Đã thực thi (rowcount={cur.rowcount}) --", f)
                except sqlite3.Error as e:
                    log(f"\n-- SQL --\n{stmt}\n!! LỖI: {e}", f)
                    raise

        # Xuất bảng cuối cùng ra CSV
        final_df = pd.read_sql("SELECT * FROM customers_after", conn)
        final_df.to_csv(AFTER_SQL_CSV, index=False)
        log(f"\n>>> Đã xuất kết quả cuối cùng ra: {AFTER_SQL_CSV} ({final_df.shape[0]} dòng x {final_df.shape[1]} cột)", f)

    conn.close()
    print(f"\nLog đầy đủ tại: {LOGFILE}")


if __name__ == "__main__":
    main()
