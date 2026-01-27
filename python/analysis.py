import pandas as pd
import matplotlib.pyplot as plt

customers = pd.read_csv("data/customers.csv")
orders = pd.read_csv("data/orders.csv")

print(customers.shape)
print(orders.shape)

## clv по клієнтах
clv = (
    orders
    .groupby("customer_id")
    .agg(
        orders_count=("order_id", "count"),
        total_revenue=("amount", "sum"),
        avg_order_value=("amount", "mean")
    )
    .reset_index()
)

print(clv.head())

## Додаємо клієнтів без замовлень
customer_metrics = customers.merge(
    clv,
    on="customer_id",
    how="left"
)

customers_full = customer_metrics.copy()

customer_metrics[["orders_count", "total_revenue", "avg_order_value"]] = (
    customer_metrics[["orders_count", "total_revenue", "avg_order_value"]]
    .fillna(0)
)

print(customer_metrics.head())

## Перша перевірка
print("Total customers:", customer_metrics.shape[0])
print("Customers with revenue > 0:", (customer_metrics["total_revenue"] > 0).sum())

## Гістогарама clv 
customer_metrics["total_revenue"].plot(kind="hist", bins=50)
plt.title("Розподіл доходу на клієнта (CLV)")
plt.xlabel("Total revenue")
plt.ylabel("Customers")
plt.tight_layout()
plt.show()

## Видіоляємо vip (топ 20%)
customers_full = customers_full.sort_values(
    by="total_revenue",
    ascending=False
).reset_index(drop=True)

customers_full["cum_revenue"] = customers_full["total_revenue"].cumsum()
total_revenue = customers_full["total_revenue"].sum()

customers_full["cum_revenue_pct"] = (
    customers_full["cum_revenue"] / total_revenue
)

customers_full["vip_status"] = customers_full["cum_revenue_pct"].apply(
    lambda x: "VIP" if x <= 0.8 else "Regular"
)


## Перевіряємо pareto
vip_summary = (
    customers_full
    .groupby("vip_status")
    .agg(
        customers=("customer_id", "count"),
        total_revenue=("total_revenue", "sum")
    )
)

vip_summary["revenue_share_%"] = (
    vip_summary["total_revenue"] / vip_summary["total_revenue"].sum() * 100
)

print(vip_summary)

## Pareto-графік
plt.figure(figsize=(8,5))
plt.plot(customers_full["cum_revenue_pct"])
plt.axhline(0.8, color="red", linestyle="--")
plt.title("Pareto analysis (80% доходу)")
plt.xlabel("Клієнти, відсортовані за доходом")
plt.ylabel("Кумулятивна частка доходу")
plt.tight_layout()
plt.show()

## Додаємо кумулятивний дохід
customers_full["revenue_share"] = (
    customers_full["total_revenue"] / customers_full["total_revenue"].sum()
)

customers_full["cumulative_revenue_share"] = (
    customers_full["revenue_share"].cumsum()
)

## Сегментація клієнтів за CLV
def clv_segment(value):
    if value == 0:
        return "no_revenue"
    elif value < 5000:
        return "low_value"
    elif value < 20000:
        return "mid_value"
    else:
        return "high_value"

customers_full["clv_segment"] = customers_full["total_revenue"].apply(clv_segment)
customers_full["clv_segment"].value_counts()
## Аналіз сегметнів
clv_summary = (
    customers_full
    .groupby("clv_segment")
    .agg(
        customers=("customer_id", "count"),
        total_revenue=("total_revenue", "sum"),
        avg_revenue=("total_revenue", "mean")
    )
)

print(clv_summary)

## Візуалізація сегментів
## Кількість клієнтів
customers_full["clv_segment"].value_counts().plot(kind="bar")
plt.title("Customers by CLV segment")
plt.tight_layout()
plt.show()

## Дохід
clv_summary["total_revenue"].plot(kind="bar")
plt.title("Revenue by CLV segment")
plt.tight_layout()
plt.show()

## Підготовка дат
orders["order_date"] = pd.to_datetime(orders["order_date"])
orders["order_month"] = orders["order_date"].dt.to_period("M")

## Остання покупка кожеого клієнта
last_order = (
    orders
    .groupby("customer_id")
    .agg(last_order_date=("order_date", "max"))
    .reset_index()
)

print(last_order.head())

## Додаємо в основну таблицю
customers_full = customers_full.merge(
    last_order,
    on="customer_id",
    how="left"
)

## Визначаємо churn
cutoff_date = pd.to_datetime("2024-01-01")

customers_full["churn_status"] = customers_full["last_order_date"].apply(
    lambda x: "churned" if pd.isna(x) or x < cutoff_date else "active"
)

## Churn-метрики
churn_summary = (
    customers_full
    .groupby("churn_status")
    .agg(
        customers=("customer_id", "count"),
        total_revenue=("total_revenue", "sum"),
        avg_revenue=("total_revenue", "mean")
    )
)

print(churn_summary)
customers_full[["customer_id", "last_order_date", "churn_status"]].head(10)

## Поєжнюємо churn + clv
pivot = (
    customers_full
    .groupby(["churn_status", "vip_status"])
    .agg(
        customers=("customer_id", "count"),
        revenue=("total_revenue", "sum")
    )
)

print(pivot)

## Cohort month
first_order = (
    orders
    .groupby("customer_id")
    .agg(cohort_month=("order_month", "min"))
    .reset_index()
)

## Додаємо cohort в orders
orders = orders.merge(
    first_order,
    on="customer_id",
    how="left"
)
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   
## Рахуємо номер місця
orders["cohort_index"] = (
    orders["order_month"] - orders["cohort_month"]
).apply(lambda x: x.n)

## Створюємо cohort table 
cohort_data = (
    orders
    .groupby(["cohort_month", "cohort_index"])
    .agg(customers=("customer_id", "nunique"))
    .reset_index()
)

## Pivot
cohort_table = cohort_data.pivot(
    index="cohort_month",
    columns="cohort_index",
    values="customers"
)

## Retention
retention = cohort_table.divide(cohort_table[0], axis=0) * 100
retention = retention.round(1)

print(retention)

## Візуалізація
plt.figure(figsize=(10, 6))
plt.imshow(retention, aspect="auto")
plt.colorbar(label="Retention %")
plt.xlabel("Months since first purchase")
plt.ylabel("Cohort month")
plt.title("Customer Retention Cohort Analysis")
plt.show()

## Revenue по когортам і місяцям
cohort_revenue = (
    orders
    .groupby(["cohort_month", "cohort_index"])
    .agg(revenue=("amount", "sum"))
    .reset_index()
)

## Pivot revenue 
revenue_cohort_table = cohort_revenue.pivot(
    index="cohort_month",
    columns="cohort_index",
    values="revenue"
)

print(revenue_cohort_table.head())

## Revenue retention
revenue_retention = (
    revenue_cohort_table
    .divide(revenue_cohort_table[0], axis=0)
    * 100
).round(1)

print(revenue_retention)

## Візуалізація revenue retention
plt.figure(figsize=(10, 6))
plt.imshow(revenue_retention, aspect="auto")
plt.colorbar(label="Revenue retention %")
plt.xlabel("Months since first purchase")
plt.ylabel("Cohort month")
plt.title("Revenue Retention Cohort Analysis")
plt.show()

## Ідкя прогнозу CLV
avg_order_value = orders["amount"].mean()

## Замовлення на клієнта
orders_per_customer = (
    orders
    .groupby("customer_id")
    .size()
    .mean()
)

## Середній lifetime(в місяцях)
customer_lifetime = (
    orders
    .groupby("customer_id")["order_date"]
    .agg(lambda x: (x.max() - x.min()).days / 30)
    .mean()
)

## Прогноз CLV
predicted_clv = avg_order_value * orders_per_customer * customer_lifetime

print(f"Прогнозований середній CLV: {predicted_clv:,.0f}")

## CLV-прогноз по сегментах
clv_forecast = (
    customers_full
    .groupby("clv_segment")
    .agg(
        avg_orders=("orders_count", "mean"),
        avg_revenue=("total_revenue", "mean")
    )
)

print(clv_forecast)

## Загальний KPI 
total_customers = customers_full["customer_id"].nunique()
total_revenue = customers_full["total_revenue"].sum()
avg_clv = customers_full["total_revenue"].mean()
repeat_rate = (
    (customers_full["orders_count"] > 1).sum() / total_customers
)

print("=== КЛЮЧОВІ МЕТРИКИ ===")
print(f"Загальна кількість клієнтів: {total_customers}")
print(f"Загальний дохід: {total_revenue:,.0f}")
print(f"Середній CLV: {avg_clv:,.0f}")
print(f"Repeat rate: {repeat_rate:.2%}")
