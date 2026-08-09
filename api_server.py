from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sqlite3

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB = r"Z:\Projects\VMPOS\app\database\vmpos.db"


@app.get("/sales")
def sales():
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    rows = cursor.execute("""
        SELECT id, created_at, total_amount, payment_method, status
        FROM sales
        ORDER BY id DESC
        LIMIT 20
    """).fetchall()

    conn.close()

    return [
        {
            "id": row[0],
            "created_at": row[1],
            "total_amount": row[2],
            "payment_method": row[3],
            "status": row[4],
        }
        for row in rows
    ]

@app.get("/sales/today")
def today_sales():
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    result = cursor.execute("""
        SELECT COALESCE(SUM(total_amount), 0)
        FROM sales
        WHERE DATE(created_at) = DATE('now', 'localtime')
          AND status = 'completed'
    """).fetchone()

    conn.close()

    return {"total": result[0]}

@app.get("/sales")
def sales():
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    rows = cursor.execute("""
        SELECT id, created_at, total_amount, payment_method, status
        FROM sales
        ORDER BY id DESC
        LIMIT 20
    """).fetchall()

    conn.close()

    return [
        {
            "id": row[0],
            "created_at": row[1],
            "total_amount": row[2],
            "payment_method": row[3],
            "status": row[4],
        }
        for row in rows
    ]

@app.get("/products")
def products():
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    rows = cursor.execute("""
        SELECT id, barcode, name, category, sell_price, unit, quantity
        FROM products
        ORDER BY name
    """).fetchall()

    conn.close()

    return [
        {
            "id": row[0],
            "barcode": row[1],
            "name": row[2],
            "category": row[3],
            "sell_price": row[4],
            "unit": row[5],
            "quantity": row[6],
        }
        for row in rows
    ]

@app.get("/reports/today")
def today_report():
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    row = cursor.execute("""
        SELECT
            COALESCE(SUM(total_amount), 0),
            COUNT(*),
            COALESCE(SUM(CASE WHEN payment_method = 'cash' THEN total_amount ELSE 0 END), 0),
            COALESCE(SUM(CASE WHEN payment_method = 'card' THEN total_amount ELSE 0 END), 0),
            COALESCE(SUM(CASE WHEN payment_method = 'debt' THEN total_amount ELSE 0 END), 0)
        FROM sales
        WHERE DATE(created_at) = DATE('now', 'localtime')
          AND status = 'completed'
    """).fetchone()

    conn.close()

    return {
        "total": row[0],
        "checks": row[1],
        "cash": row[2],
        "card": row[3],
        "debt": row[4],
    }

@app.get("/customers")
def customers():
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    rows = cursor.execute("""
        SELECT id, name, phone, address, debt_amount, debt_date
        FROM customers
        ORDER BY name
    """).fetchall()

    conn.close()

    return [
        {
            "id": row[0],
            "name": row[1],
            "phone": row[2],
            "address": row[3],
            "debt_amount": row[4],
            "debt_date": row[5],
        }
        for row in rows
    ]