"""
Step 3: Load Olist CSV files into MySQL
Run this script ONCE to set up your database.
Usage: python load_data.py
"""

import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME", "olist_retail")

# Path to extracted CSV files
DATA_FOLDER = r"C:\Users\Pratik Bhoodatt\Desktop\olist_data"

# MySQL connection
engine = create_engine(f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}")

# All CSV files and their table names
FILES = {
    "olist_customers_dataset.csv": "customers",
    "olist_orders_dataset.csv": "orders",
    "olist_order_items_dataset.csv": "order_items",
    "olist_order_payments_dataset.csv": "order_payments",
    "olist_order_reviews_dataset.csv": "order_reviews",
    "olist_products_dataset.csv": "products",
    "olist_sellers_dataset.csv": "sellers",
    "olist_geolocation_dataset.csv": "geolocation",
    "product_category_name_translation.csv": "category_translation",
}

print("=" * 50)
print("Loading Olist data into MySQL...")
print("=" * 50)

for csv_file, table_name in FILES.items():
    file_path = os.path.join(DATA_FOLDER, csv_file)

    if not os.path.exists(file_path):
        print(f"  [X] File not found: {csv_file} -- SKIPPING")
        continue

    print(f"\n>> Loading: {csv_file}")

    # Read CSV
    df = pd.read_csv(file_path, low_memory=False)

    # Clean column names — lowercase, no spaces
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")

    # Show info
    print(f"   Rows: {len(df):,}  |  Columns: {len(df.columns)}")
    print(f"   Columns: {list(df.columns)}")

    # Load into MySQL (replace if table already exists)
    df.to_sql(table_name, engine, if_exists="replace", index=False, chunksize=5000)

    print(f"   [OK] Loaded into table: `{table_name}`")

print("\n" + "=" * 50)
print("[DONE] ALL DONE! Your database is ready.")
print(f"   Database: {DB_NAME}")
print(f"   Tables: {list(FILES.values())}")
print("=" * 50)
