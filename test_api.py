import requests
import json

BASE_URL = "http://127.0.0.1:5000"


def print_section(title):
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def test_health():
    print_section("测试1: 健康检查 /api/health")
    resp = requests.get(f"{BASE_URL}/api/health")
    data = resp.json()
    print(json.dumps(data, ensure_ascii=False, indent=2))
    assert data["status"] == "healthy"
    print("✓ 通过")


def test_datasets():
    print_section("测试2: 数据集列表 /api/datasets")
    resp = requests.get(f"{BASE_URL}/api/datasets")
    data = resp.json()
    print(json.dumps(data, ensure_ascii=False, indent=2))
    assert "default" in data["datasets"]
    print("✓ 通过")


def test_all_metrics():
    print_section("测试3: 全部指标 /api/metrics/all")
    resp = requests.get(f"{BASE_URL}/api/metrics/all?period=month")
    data = resp.json()
    print(f"状态: {data['status']}")
    print(f"周期: {data['period']}")
    print(f"日期范围: {data['date_range']['start']} ~ {data['date_range']['end']}")
    for key, metric in data["metrics"].items():
        val = f"{metric['value']}{metric.get('unit', '')}" if metric["value"] is not None else "N/A"
        print(f"  {metric['name']}({key}): {val}")
    assert data["status"] == "success"
    assert len(data["metrics"]) == 4
    print("✓ 通过")
    return data


def test_single_metrics():
    print_section("测试4: 单个指标接口")

    endpoints = [
        ("/api/metrics/total", "总数"),
        ("/api/metrics/average", "均值"),
        ("/api/metrics/growth-rate?period=month", "环比增长率"),
        ("/api/metrics/yoy-growth?period=month", "同比增长率"),
    ]

    for endpoint, name in endpoints:
        resp = requests.get(f"{BASE_URL}{endpoint}")
        data = resp.json()
        metric = data["metric"]
        val = f"{metric['value']}{metric.get('unit', '')}" if metric["value"] is not None else "N/A"
        print(f"  {name}: {val}")
        assert data["status"] == "success"
    print("✓ 通过")


def test_custom_metrics():
    print_section("测试5: 自定义指标 /api/metrics/custom")

    params = {"metrics": "total,growth_rate", "period": "quarter"}
    resp = requests.get(f"{BASE_URL}/api/metrics/custom", params=params)
    data = resp.json()
    print(f"请求指标: total, growth_rate")
    print(f"返回指标: {list(data['metrics'].keys())}")
    for key, metric in data["metrics"].items():
        val = f"{metric['value']}{metric.get('unit', '')}" if metric["value"] is not None else "N/A"
        print(f"  {metric['name']}: {val}")
    assert "total" in data["metrics"]
    assert "growth_rate" in data["metrics"]
    print("✓ 通过")


def test_date_filter():
    print_section("测试6: 日期范围过滤")
    params = {
        "start_date": "2025-01-01",
        "end_date": "2025-12-31",
        "period": "month"
    }
    resp = requests.get(f"{BASE_URL}/api/metrics/total", params=params)
    data = resp.json()
    total_2025 = data["metric"]["value"]
    print(f"  2025年总数: {total_2025}")
    print(f"  记录数: {data['metric']['description']}")

    resp2 = requests.get(f"{BASE_URL}/api/metrics/all", params=params)
    data2 = resp2.json()
    assert data2["date_range"]["start"] == "2025-01-01"
    assert data2["date_range"]["end"] == "2025-12-31"
    print("✓ 通过")


def test_trend():
    print_section("测试7: 趋势数据 /api/trend")
    params = {"period": "month", "limit": 6}
    resp = requests.get(f"{BASE_URL}/api/trend", params=params)
    data = resp.json()
    print(f"数据点数量: {len(data['trend'])}")
    for item in data["trend"]:
        date_str = str(item["period"])[:7]
        print(f"  {date_str}: {item['value']}")
    assert len(data["trend"]) == 6
    print("✓ 通过")


def test_dashboard():
    print_section("测试8: 仪表盘综合接口 /api/dashboard")
    params = {"period": "month"}
    resp = requests.get(f"{BASE_URL}/api/dashboard", params=params)
    data = resp.json()
    print(f"状态: {data['status']}")
    print(f"指标卡片: {len(data['cards']['metrics'])} 个指标")
    print(f"趋势图: {len(data['chart']['trend'])} 个数据点")
    print("  指标概览:")
    for key, metric in data["cards"]["metrics"].items():
        val = f"{metric['value']}{metric.get('unit', '')}" if metric["value"] is not None else "N/A"
        print(f"    - {metric['name']}: {val}")
    assert data["status"] == "success"
    assert "cards" in data
    assert "chart" in data
    print("✓ 通过")


def test_upload_dataset():
    print_section("测试9: 上传数据集 /api/datasets (POST)")

    new_records = []
    for i in range(365):
        from datetime import datetime, timedelta
        import random
        d = (datetime(2025, 12, 31) - timedelta(days=i)).strftime("%Y-%m-%d")
        new_records.append({
            "date": d,
            "revenue": round(random.uniform(5000, 20000), 2),
            "orders": random.randint(50, 300)
        })

    payload = {
        "name": "revenue_data",
        "records": new_records,
        "date_col": "date",
        "value_col": "revenue"
    }

    resp = requests.post(
        f"{BASE_URL}/api/datasets",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    data = resp.json()
    print(f"状态: {data['status']}")
    print(f"消息: {data.get('message', '')}")
    print(f"行数: {data.get('rows', 0)}")
    assert data["status"] == "success"

    resp2 = requests.get(f"{BASE_URL}/api/metrics/all?dataset=revenue_data&value_col=revenue")
    data2 = resp2.json()
    print(f"\n使用新数据集计算:")
    print(f"  总数: {data2['metrics']['total']['value']}")
    print(f"  均值: {data2['metrics']['average']['value']}")
    print("✓ 通过")


def run_all_tests():
    print("\n" + "╔" + "═" * 58 + "╗")
    print("║" + " " * 18 + "Flask API 接口测试" + " " * 23 + "║")
    print("╚" + "═" * 58 + "╝")

    try:
        test_health()
        test_datasets()
        test_all_metrics()
        test_single_metrics()
        test_custom_metrics()
        test_date_filter()
        test_trend()
        test_dashboard()
        test_upload_dataset()

        print("\n" + "=" * 60)
        print("🎉 所有 API 接口测试全部通过！")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        raise
    except Exception as e:
        print(f"\n❌ 发生错误: {type(e).__name__}: {e}")
        raise


if __name__ == "__main__":
    run_all_tests()
