import pandas as pd
import random
from datetime import datetime, timedelta

random.seed(42)

# ---------- CUSTOMERS ----------
cities = ["Kyiv", "Lviv", "Odesa", "Kharkiv", "Dnipro"]

customers = []
for i in range(1, 3001):
    customers.append({
        "customer_id": i,
        "city": random.choice(cities),
        "age": random.randint(18, 65),
        "created_at": (
            datetime(2021, 1, 1) + timedelta(days=random.randint(0, 1200))
        ).date()
    })

customers_df = pd.DataFrame(customers)
customers_df.to_csv("customers.csv", index=False)

# ---------- ORDERS ----------
orders = []
order_id = 1

for customer in customers:
    r = random.random()
    if r < 0.6:
        order_count = random.randint(1, 2)
    elif r < 0.9:
        order_count = random.randint(3, 10)
    else:
        order_count = random.randint(15, 50)

    for _ in range(order_count):
        orders.append({
            "order_id": order_id,
            "customer_id": customer["customer_id"],
            "amount": random.randint(50, 5000),
            "order_date": (
                datetime(2021, 1, 1) + timedelta(days=random.randint(0, 1200))
            ).date()
        })
        order_id += 1

orders_df = pd.DataFrame(orders)
orders_df.to_csv("orders.csv", index=False)

print("✅ Дані згенеровано")
print("Customers:", len(customers_df))
print("Orders:", len(orders_df))