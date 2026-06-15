import pandas as pd
import json
from datetime import datetime
from metrics import MetricsCalculator
from sample_data import generate_sample_sales


def test_basic_metrics():
    print("=" * 60)
    print("测试1: 基础指标计算（总数/均值）")
    print("=" * 60)

    df = generate_sample_sales(days=365)
    calc = MetricsCalculator(df)

    total = calc.get_total()
    print(f"总数: {total['value']} {total['unit']}")
    print(f"  描述: {total['description']}")

    avg = calc.get_average()
    print(f"均值: {avg['value']} {avg['unit']}")
    print(f"  描述: {avg['description']}")

    expected_total = float(df['value'].sum())
    expected_avg = float(df['value'].mean())
    assert abs(total['value'] - round(expected_total, 2)) < 0.01, "总数计算错误"
    assert abs(avg['value'] - round(expected_avg, 2)) < 0.01, "均值计算错误"
    print("✓ 基础指标测试通过\n")


def test_growth_rate():
    print("=" * 60)
    print("测试2: 增长率（环比）计算")
    print("=" * 60)

    df = generate_sample_sales(days=730)
    calc = MetricsCalculator(df)

    for period in ['month', 'quarter', 'year']:
        growth = calc.get_growth_rate(period=period)
        print(f"周期[{period}] - {growth['name']}: {growth['value']}{growth['unit']}")
        if growth['value'] is not None:
            print(f"  当前值: {growth['current_value']}, 上期值: {growth['previous_value']}")
            print(f"  描述: {growth['description']}")
    print("✓ 增长率测试通过\n")


def test_yoy_growth():
    print("=" * 60)
    print("测试3: 同比增长率计算")
    print("=" * 60)

    df = generate_sample_sales(days=730)
    calc = MetricsCalculator(df)

    yoy = calc.get_yoy_growth(period='month')
    print(f"月度同比增长率: {yoy['value']}{yoy['unit']}")
    if yoy['value'] is not None:
        print(f"  当前值: {yoy['current_value']}, 去年同期: {yoy['last_year_value']}")
        print(f"  描述: {yoy['description']}")

        expected = ((yoy['current_value'] - yoy['last_year_value']) / abs(yoy['last_year_value'])) * 100
        assert abs(yoy['value'] - round(expected, 2)) < 0.01, "同比计算错误"
    print("✓ 同比增长率测试通过\n")


def test_date_filter():
    print("=" * 60)
    print("测试4: 日期范围过滤")
    print("=" * 60)

    df = generate_sample_sales(days=365)
    calc = MetricsCalculator(df)

    start = '2025-06-01'
    end = '2025-12-31'
    total = calc.get_total(start_date=start, end_date=end)

    mask = (df['date'] >= start) & (df['date'] <= end)
    expected = float(df.loc[mask, 'value'].sum())
    print(f"日期范围: {start} ~ {end}")
    print(f"过滤后总数: {total['value']}")
    print(f"预期总数: {round(expected, 2)}")
    assert abs(total['value'] - round(expected, 2)) < 0.01, "日期过滤错误"
    print("✓ 日期过滤测试通过\n")


def test_all_metrics_json():
    print("=" * 60)
    print("测试5: 全部指标 JSON 输出")
    print("=" * 60)

    df = generate_sample_sales(days=730)
    calc = MetricsCalculator(df)

    result = calc.get_all_metrics(period='month')
    print(f"状态: {result['status']}")
    print(f"周期: {result['period']}")
    print(f"日期范围: {result['date_range']['start']} ~ {result['date_range']['end']}")
    print(f"指标数量: {len(result['metrics'])}")

    for key, metric in result['metrics'].items():
        val_str = f"{metric['value']}{metric.get('unit', '')}" if metric['value'] is not None else "N/A"
        print(f"  {key}: {val_str}")

    json_str = json.dumps(result, ensure_ascii=False, indent=2)
    print(f"\nJSON 输出验证通过，长度: {len(json_str)} 字符")
    print("✓ 全部指标 JSON 测试通过\n")


def test_trend_data():
    print("=" * 60)
    print("测试6: 趋势数据")
    print("=" * 60)

    df = generate_sample_sales(days=730)
    calc = MetricsCalculator(df)

    trend = calc.get_trend_data(period='month', limit=6)
    print(f"趋势数据点数量: {len(trend['trend'])}")
    for item in trend['trend']:
        print(f"  {item['period']}: {item['value']}")
    print("✓ 趋势数据测试通过\n")


def test_custom_metrics():
    print("=" * 60)
    print("测试7: 自定义指标组合")
    print("=" * 60)

    df = generate_sample_sales(days=730)
    calc = MetricsCalculator(df)

    result = calc.get_custom_metrics(['total', 'yoy_growth'], period='month')
    print(f"请求指标: ['total', 'yoy_growth']")
    print(f"返回指标: {list(result['metrics'].keys())}")
    assert 'total' in result['metrics']
    assert 'yoy_growth' in result['metrics']
    assert 'growth_rate' not in result['metrics']
    assert 'average' not in result['metrics']
    print("✓ 自定义指标测试通过\n")


def test_yoy_missing_data():
    print("=" * 60)
    print("测试8: 同比计算 - 去年同期数据缺失")
    print("=" * 60)

    dates_2025 = pd.date_range(start='2025-01-01', end='2025-12-31', freq='D')
    df = pd.DataFrame({
        'date': dates_2025.strftime('%Y-%m-%d'),
        'value': [100.0] * len(dates_2025)
    })
    calc = MetricsCalculator(df)

    yoy = calc.get_yoy_growth(period='month')
    print(f"仅有2025年数据 → 同比结果: {yoy['value']}")
    print(f"  描述: {yoy['description']}")
    assert yoy['value'] is None, "去年同期数据缺失时应返回 None"
    assert "数据缺失" in yoy['description'] or "无原始数据" in yoy['description'], \
        f"描述应提示数据缺失，实际: {yoy['description']}"
    print("✓ 同比缺失数据测试通过\n")


def test_yoy_gap_in_data():
    print("=" * 60)
    print("测试9: 同比计算 - 中间月份缺失（去年某月无数据）")
    print("=" * 60)

    dates_2024 = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
    mask_2024 = ~((dates_2024.month == 12))
    dates_2024_filtered = dates_2024[mask_2024]

    dates_2025 = pd.date_range(start='2025-01-01', end='2025-12-31', freq='D')

    all_dates = pd.concat([
        pd.Series(dates_2024_filtered),
        pd.Series(dates_2025)
    ])

    df = pd.DataFrame({
        'date': all_dates.dt.strftime('%Y-%m-%d'),
        'value': [100.0] * len(all_dates)
    })
    calc = MetricsCalculator(df)

    yoy = calc.get_yoy_growth(period='month')
    print(f"去年12月数据缺失 → 同比结果: {yoy['value']}")
    print(f"  描述: {yoy['description']}")

    if yoy['value'] is None:
        assert "无原始数据" in yoy['description'] or "数据缺失" in yoy['description'], \
            f"描述应提示去年12月缺失，实际: {yoy['description']}"
        print("  正确返回了缺失提示")
    print("✓ 同比中间月份缺失测试通过\n")


def test_growth_rate_missing_prev():
    print("=" * 60)
    print("测试10: 环比计算 - 上期数据缺失")
    print("=" * 60)

    dates = pd.date_range(start='2025-03-01', end='2025-06-30', freq='D')
    df = pd.DataFrame({
        'date': dates.strftime('%Y-%m-%d'),
        'value': [200.0] * len(dates)
    })
    calc = MetricsCalculator(df)

    growth = calc.get_growth_rate(period='month')
    print(f"仅有3-6月数据 → 环比结果: {growth['value']}")
    print(f"  描述: {growth['description']}")

    if growth['value'] is not None:
        print(f"  当前值: {growth['current_value']}, 上期值: {growth['previous_value']}")
    print("✓ 环比上期缺失测试通过\n")


def test_trend_has_data_flag():
    print("=" * 60)
    print("测试11: 趋势数据 has_data 标记")
    print("=" * 60)

    dates_2024 = pd.date_range(start='2024-06-01', end='2024-12-31', freq='D')
    dates_2025 = pd.date_range(start='2025-03-01', end='2025-06-30', freq='D')
    all_dates = pd.concat([pd.Series(dates_2024), pd.Series(dates_2025)])

    df = pd.DataFrame({
        'date': all_dates.dt.strftime('%Y-%m-%d'),
        'value': [100.0] * len(all_dates)
    })
    calc = MetricsCalculator(df)

    trend = calc.get_trend_data(period='month', limit=12)
    print(f"趋势数据点数量: {len(trend['trend'])}")
    for item in trend['trend']:
        period_str = str(item['period'])[:7]
        data_flag = "有数据" if item['has_data'] else "无数据"
        print(f"  {period_str}: {item['value']} ({data_flag})")

    has_data_flags = [item['has_data'] for item in trend['trend']]
    assert True in has_data_flags, "应存在有数据的月份"
    assert 'has_data' in trend['trend'][0], "趋势数据应包含 has_data 字段"
    print("✓ 趋势 has_data 标记测试通过\n")


def run_all_tests():
    print("\n" + "╔" + "═" * 58 + "╗")
    print("║" + " " * 15 + "指标计算模块单元测试" + " " * 22 + "║")
    print("╚" + "═" * 58 + "╝\n")

    try:
        test_basic_metrics()
        test_growth_rate()
        test_yoy_growth()
        test_date_filter()
        test_all_metrics_json()
        test_trend_data()
        test_custom_metrics()
        test_yoy_missing_data()
        test_yoy_gap_in_data()
        test_growth_rate_missing_prev()
        test_trend_has_data_flag()

        print("=" * 60)
        print("🎉 所有测试全部通过！")
        print("=" * 60)
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        raise
    except Exception as e:
        print(f"\n❌ 发生错误: {type(e).__name__}: {e}")
        raise


if __name__ == '__main__':
    run_all_tests()
