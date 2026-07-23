import sqlite3
import random
import csv
from datetime import date, timedelta
import os

random.seed(42)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, "branches.db")
CSV_PATH = os.path.join(DATA_DIR, "inventory.csv")

# ---- Branches ----
branches = [
    (1, "Zaiqa Bites - Clifton",      "Karachi",     "Sindh"),
    (2, "Zaiqa Bites - Gulshan",      "Karachi",     "Sindh"),
    (3, "Zaiqa Bites - DHA Lahore",   "Lahore",      "Punjab"),
    (4, "Zaiqa Bites - Gulberg",      "Lahore",      "Punjab"),
    (5, "Zaiqa Bites - F-7 Blue Area","Islamabad",   "Islamabad Capital Territory"),
    (6, "Zaiqa Bites - Faisalabad",   "Faisalabad",  "Punjab"),
]

menu_items = [
    "Chicken Karahi", "Beef Biryani", "Zinger Burger", "Seekh Kebab Platter",
    "Chicken Handi", "Club Sandwich", "Nihari", "Chapli Kebab",
    "Fried Rice", "Chicken Tikka",
]

# base performance multipliers to create realistic winners/underperformers
branch_strength = {1: 1.25, 2: 0.85, 3: 1.15, 4: 0.70, 5: 1.05, 6: 0.60}
item_strength_by_city = {
    "Karachi":    {"Chicken Karahi": 1.3, "Zinger Burger": 1.2},
    "Lahore":     {"Nihari": 1.4, "Chapli Kebab": 1.3},
    "Islamabad":  {"Club Sandwich": 1.2, "Chicken Tikka": 1.1},
    "Faisalabad": {"Chapli Kebab": 1.2},
}

start_date = date(2025, 5, 1)
end_date = date(2025, 7, 22)  # ~3 months of daily data

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.executescript("""
DROP TABLE IF EXISTS branches;
DROP TABLE IF EXISTS sales;
DROP TABLE IF EXISTS footfall;

CREATE TABLE branches (
    branch_id INTEGER PRIMARY KEY,
    branch_name TEXT NOT NULL,
    city TEXT NOT NULL,
    region TEXT NOT NULL
);

CREATE TABLE sales (
    sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
    branch_id INTEGER NOT NULL,
    sale_date TEXT NOT NULL,
    menu_item TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price REAL NOT NULL,
    revenue REAL NOT NULL,
    FOREIGN KEY (branch_id) REFERENCES branches(branch_id)
);

CREATE TABLE footfall (
    footfall_id INTEGER PRIMARY KEY AUTOINCREMENT,
    branch_id INTEGER NOT NULL,
    visit_date TEXT NOT NULL,
    customer_count INTEGER NOT NULL,
    FOREIGN KEY (branch_id) REFERENCES branches(branch_id)
);
""")

cur.executemany("INSERT INTO branches VALUES (?,?,?,?)", branches)

item_base_price = {item: random.randint(450, 1400) for item in menu_items}

sales_rows = []
footfall_rows = []

d = start_date
while d <= end_date:
    weekday_factor = 1.3 if d.weekday() in (4, 5) else 1.0
    for b_id, b_name, city, region in branches:
        strength = branch_strength[b_id]
        
        anomaly_factor = 1.0
        if b_id == 6 and d >= end_date - timedelta(days=14):
            anomaly_factor = 0.55

        base_customers = 120 * strength * weekday_factor * anomaly_factor
        customers = max(5, int(random.gauss(base_customers, base_customers * 0.12)))
        footfall_rows.append((b_id, d.isoformat(), customers))

        # each branch sells a random subset of items each day
        items_today = random.sample(menu_items, k=random.randint(5, 8))
        for item in items_today:
            city_boost = item_strength_by_city.get(city, {}).get(item, 1.0)
            base_qty = 8 * strength * weekday_factor * city_boost * anomaly_factor
            qty = max(0, int(random.gauss(base_qty, base_qty * 0.25)))
            if qty == 0:
                continue
            price = item_base_price[item] * random.uniform(0.95, 1.05)
            revenue = round(qty * price, 2)
            sales_rows.append((b_id, d.isoformat(), item, qty, round(price, 2), revenue))
    d += timedelta(days=1)

cur.executemany(
    "INSERT INTO sales (branch_id, sale_date, menu_item, quantity, unit_price, revenue) VALUES (?,?,?,?,?,?)",
    sales_rows,
)
cur.executemany(
    "INSERT INTO footfall (branch_id, visit_date, customer_count) VALUES (?,?,?)",
    footfall_rows,
)

conn.commit()
conn.close()

# ---- CSV connector source: inventory snapshot per branch ----
inventory_items = [
    "Chicken (kg)", "Beef (kg)", "Rice (kg)", "Cooking Oil (L)",
    "Flour (kg)", "Spice Mix (packs)", "Packaging Boxes (units)",
]

with open(CSV_PATH, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["branch_id", "branch_name", "item", "stock_on_hand", "reorder_level", "unit"])
    for b_id, b_name, city, region in branches:
        strength = branch_strength[b_id]
        for item in inventory_items:
            reorder_level = random.randint(20, 60)
            # Faisalabad (the anomaly branch) also shows a low-stock item, giving
            # a plausible operational explanation to correlate with the footfall drop
            stock = int(reorder_level * random.uniform(1.2, 3.0))
            if b_id == 6 and item in ("Chicken (kg)", "Cooking Oil (L)"):
                stock = int(reorder_level * random.uniform(0.3, 0.7))
            writer.writerow([b_id, b_name, item, stock, reorder_level, item.split(" (")[-1].rstrip(")")])

print(f"Created {DB_PATH} with {len(branches)} branches, {len(sales_rows)} sales rows, {len(footfall_rows)} footfall rows.")
print(f"Created {CSV_PATH} with inventory snapshot.")
