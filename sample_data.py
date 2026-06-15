import pandas as pd
import numpy as np
from datetime import datetime, timedelta


def generate_sample_sales(days: int = 730, seed: int = 42) -> pd.DataFrame:
    np.random.seed(seed)
    end_date = datetime(2025, 12, 31)
    start_date = end_date - timedelta(days=days - 1)
    dates = pd.date_range(start=start_date, end=end_date, freq='D')

    base = 1000
    trend = np.linspace(0, 500, days)
    seasonality = 200 * np.sin(np.linspace(0, 4 * np.pi, days))
    weekly = np.array([150 if i % 7 in [5, 6] else 0 for i in range(days)])
    noise = np.random.normal(0, 100, days)

    values = base + trend + seasonality + weekly + noise
    values = np.maximum(values, 100)

    categories = np.random.choice(['A', 'B', 'C'], size=days, p=[0.4, 0.35, 0.25])

    df = pd.DataFrame({
        'date': dates.strftime('%Y-%m-%d'),
        'value': np.round(values, 2),
        'category': categories,
        'orders': np.random.randint(10, 100, days)
    })

    return df


def generate_sample_orders(months: int = 24, seed: int = 123) -> pd.DataFrame:
    np.random.seed(seed)
    end_date = datetime(2025, 12, 1)
    start_date = end_date - pd.DateOffset(months=months - 1)
    dates = pd.date_range(start=start_date, end=end_date, freq='MS')

    revenue = []
    base = 50000
    for i in range(months):
        growth = 1 + (i * 0.02)
        seasonal = 1 + 0.15 * np.sin(i * np.pi / 6)
        noise = np.random.normal(1, 0.05)
        revenue.append(round(base * growth * seasonal * noise, 2))

    df = pd.DataFrame({
        'month': dates.strftime('%Y-%m-%d'),
        'revenue': revenue,
        'new_users': np.random.randint(500, 2000, months),
        'active_users': np.random.randint(5000, 15000, months),
        'conversion_rate': np.round(np.random.uniform(0.02, 0.08, months), 4)
    })

    return df


if __name__ == '__main__':
    print("生成示例销售数据（日粒度）...")
    df_sales = generate_sample_sales()
    df_sales.to_csv('data/default.csv', index=False)
    print(f"  共 {len(df_sales)} 条记录，日期范围: {df_sales['date'].min()} ~ {df_sales['date'].max()}")
    print(f"  销售额范围: {df_sales['value'].min()} ~ {df_sales['value'].max()}")

    print("\n生成示例订单数据（月粒度）...")
    df_orders = generate_sample_orders()
    df_orders.to_csv('data/orders.csv', index=False)
    print(f"  共 {len(df_orders)} 条记录")

    print("\n示例数据生成完成！")
