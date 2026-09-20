import mysql.connector
import sqlite3
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

print("Connecting to MySQL...")
mysql_conn = mysql.connector.connect(
    host=os.getenv("DB_HOST", "localhost"),
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME", "olist_retail")
)

sqlite_path = "olist_retail.db"
if os.path.exists(sqlite_path):
    os.remove(sqlite_path)

sqlite_conn = sqlite3.connect(sqlite_path)

tables = [
    "category_translation",
    "customers",
    "orders",
    "order_items",
    "order_payments",
    "order_reviews",
    "products",
    "sellers"
]

print("Exporting tables to SQLite...")
for table in tables:
    print(f"  Exporting {table}...")
    df = pd.read_sql(f"SELECT * FROM {table}", mysql_conn)
    df.to_sql(table, sqlite_conn, index=False, if_exists="replace")
    print(f"    Done: {len(df):,} rows.")

print("Creating database indexes for instant query performance...")
cursor = sqlite_conn.cursor()
indexes = [
    "CREATE INDEX idx_orders_id ON orders(order_id);",
    "CREATE INDEX idx_orders_cust ON orders(customer_id);",
    "CREATE INDEX idx_order_items_ord ON order_items(order_id);",
    "CREATE INDEX idx_order_items_prod ON order_items(product_id);",
    "CREATE INDEX idx_order_payments_ord ON order_payments(order_id);",
    "CREATE INDEX idx_order_reviews_ord ON order_reviews(order_id);",
    "CREATE INDEX idx_customers_id ON customers(customer_id);",
    "CREATE INDEX idx_customers_uniq ON customers(customer_unique_id);",
    "CREATE INDEX idx_products_id ON products(product_id);",
]
for idx_sql in indexes:
    cursor.execute(idx_sql)

sqlite_conn.commit()
sqlite_conn.close()
mysql_conn.close()

size_mb = os.path.getsize(sqlite_path) / (1024 * 1024)
print(f"\nSUCCESS! Created {sqlite_path} ({size_mb:.2f} MB)")
