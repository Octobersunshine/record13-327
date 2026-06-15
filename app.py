import os
import json
import pandas as pd
from flask import Flask, request, jsonify
from flask_cors import CORS
from metrics import MetricsCalculator


app = Flask(__name__)
CORS(app)

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(DATA_DIR, exist_ok=True)


def load_dataset(dataset_name: str = 'default') -> pd.DataFrame:
    csv_path = os.path.join(DATA_DIR, f'{dataset_name}.csv')
    if os.path.exists(csv_path):
        return pd.read_csv(csv_path)
    raise FileNotFoundError(f"数据集 '{dataset_name}' 不存在")


def save_dataset(df: pd.DataFrame, dataset_name: str = 'default'):
    csv_path = os.path.join(DATA_DIR, f'{dataset_name}.csv')
    df.to_csv(csv_path, index=False)


@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "指标卡片服务",
        "version": "1.0.0"
    })


@app.route('/api/datasets', methods=['GET'])
def list_datasets():
    datasets = []
    for f in os.listdir(DATA_DIR):
        if f.endswith('.csv'):
            name = f[:-4]
            datasets.append(name)
    return jsonify({
        "status": "success",
        "datasets": datasets
    })


@app.route('/api/datasets/<dataset_name>', methods=['GET'])
def get_dataset_info(dataset_name):
    try:
        df = load_dataset(dataset_name)
        return jsonify({
            "status": "success",
            "dataset": dataset_name,
            "rows": len(df),
            "columns": list(df.columns),
            "preview": df.head(5).to_dict(orient='records')
        })
    except FileNotFoundError as e:
        return jsonify({"status": "error", "message": str(e)}), 404


@app.route('/api/datasets', methods=['POST'])
def upload_dataset():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "请求体不能为空"}), 400

        dataset_name = data.get('name', 'default')
        records = data.get('records', [])
        date_col = data.get('date_col', 'date')
        value_col = data.get('value_col', 'value')

        if not records:
            return jsonify({"status": "error", "message": "数据记录不能为空"}), 400

        df = pd.DataFrame(records)
        if date_col not in df.columns:
            return jsonify({"status": "error", "message": f"缺少日期列 '{date_col}'"}), 400
        if value_col not in df.columns:
            return jsonify({"status": "error", "message": f"缺少数值列 '{value_col}'"}), 400

        save_dataset(df, dataset_name)
        return jsonify({
            "status": "success",
            "message": f"数据集 '{dataset_name}' 已保存",
            "rows": len(df)
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/metrics/all', methods=['GET'])
def get_all_metrics():
    try:
        dataset_name = request.args.get('dataset', 'default')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        period = request.args.get('period', 'month')
        date_col = request.args.get('date_col', 'date')
        value_col = request.args.get('value_col', 'value')

        df = load_dataset(dataset_name)
        calc = MetricsCalculator(df, date_col=date_col, value_col=value_col)
        result = calc.get_all_metrics(start_date, end_date, period)
        return jsonify(result)
    except FileNotFoundError as e:
        return jsonify({"status": "error", "message": str(e)}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/metrics/custom', methods=['GET', 'POST'])
def get_custom_metrics():
    try:
        if request.method == 'GET':
            dataset_name = request.args.get('dataset', 'default')
            metrics_str = request.args.get('metrics', 'total,average')
            metrics_list = metrics_str.split(',')
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            period = request.args.get('period', 'month')
            date_col = request.args.get('date_col', 'date')
            value_col = request.args.get('value_col', 'value')
        else:
            data = request.get_json() or {}
            dataset_name = data.get('dataset', 'default')
            metrics_list = data.get('metrics', ['total', 'average'])
            start_date = data.get('start_date')
            end_date = data.get('end_date')
            period = data.get('period', 'month')
            date_col = data.get('date_col', 'date')
            value_col = data.get('value_col', 'value')

        df = load_dataset(dataset_name)
        calc = MetricsCalculator(df, date_col=date_col, value_col=value_col)
        result = calc.get_custom_metrics(metrics_list, start_date, end_date, period)
        return jsonify(result)
    except FileNotFoundError as e:
        return jsonify({"status": "error", "message": str(e)}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/metrics/total', methods=['GET'])
def get_total():
    try:
        dataset_name = request.args.get('dataset', 'default')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        date_col = request.args.get('date_col', 'date')
        value_col = request.args.get('value_col', 'value')

        df = load_dataset(dataset_name)
        calc = MetricsCalculator(df, date_col=date_col, value_col=value_col)
        return jsonify({"status": "success", "metric": calc.get_total(start_date, end_date)})
    except FileNotFoundError as e:
        return jsonify({"status": "error", "message": str(e)}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/metrics/average', methods=['GET'])
def get_average():
    try:
        dataset_name = request.args.get('dataset', 'default')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        date_col = request.args.get('date_col', 'date')
        value_col = request.args.get('value_col', 'value')

        df = load_dataset(dataset_name)
        calc = MetricsCalculator(df, date_col=date_col, value_col=value_col)
        return jsonify({"status": "success", "metric": calc.get_average(start_date, end_date)})
    except FileNotFoundError as e:
        return jsonify({"status": "error", "message": str(e)}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/metrics/growth-rate', methods=['GET'])
def get_growth_rate():
    try:
        dataset_name = request.args.get('dataset', 'default')
        period = request.args.get('period', 'month')
        date_col = request.args.get('date_col', 'date')
        value_col = request.args.get('value_col', 'value')

        df = load_dataset(dataset_name)
        calc = MetricsCalculator(df, date_col=date_col, value_col=value_col)
        return jsonify({"status": "success", "metric": calc.get_growth_rate(period)})
    except FileNotFoundError as e:
        return jsonify({"status": "error", "message": str(e)}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/metrics/yoy-growth', methods=['GET'])
def get_yoy_growth():
    try:
        dataset_name = request.args.get('dataset', 'default')
        period = request.args.get('period', 'month')
        date_col = request.args.get('date_col', 'date')
        value_col = request.args.get('value_col', 'value')

        df = load_dataset(dataset_name)
        calc = MetricsCalculator(df, date_col=date_col, value_col=value_col)
        return jsonify({"status": "success", "metric": calc.get_yoy_growth(period)})
    except FileNotFoundError as e:
        return jsonify({"status": "error", "message": str(e)}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/trend', methods=['GET'])
def get_trend():
    try:
        dataset_name = request.args.get('dataset', 'default')
        period = request.args.get('period', 'month')
        limit = int(request.args.get('limit', 12))
        date_col = request.args.get('date_col', 'date')
        value_col = request.args.get('value_col', 'value')

        df = load_dataset(dataset_name)
        calc = MetricsCalculator(df, date_col=date_col, value_col=value_col)
        result = calc.get_trend_data(period, limit)
        return jsonify(result)
    except FileNotFoundError as e:
        return jsonify({"status": "error", "message": str(e)}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/dashboard', methods=['GET'])
def get_dashboard():
    try:
        dataset_name = request.args.get('dataset', 'default')
        period = request.args.get('period', 'month')
        date_col = request.args.get('date_col', 'date')
        value_col = request.args.get('value_col', 'value')

        df = load_dataset(dataset_name)
        calc = MetricsCalculator(df, date_col=date_col, value_col=value_col)

        metrics = calc.get_all_metrics(period=period)
        trend = calc.get_trend_data(period=period, limit=12)

        return jsonify({
            "status": "success",
            "timestamp": metrics["timestamp"],
            "cards": metrics,
            "chart": trend
        })
    except FileNotFoundError as e:
        return jsonify({"status": "error", "message": str(e)}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/comparison/all', methods=['GET'])
def get_all_comparisons():
    try:
        dataset_name = request.args.get('dataset', 'default')
        period = request.args.get('period', 'month')
        date_col = request.args.get('date_col', 'date')
        value_col = request.args.get('value_col', 'value')

        df = load_dataset(dataset_name)
        calc = MetricsCalculator(df, date_col=date_col, value_col=value_col)
        result = calc.get_all_comparisons(period=period)
        return jsonify(result)
    except FileNotFoundError as e:
        return jsonify({"status": "error", "message": str(e)}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/comparison/<metric_type>', methods=['GET'])
def get_comparison(metric_type):
    try:
        dataset_name = request.args.get('dataset', 'default')
        period = request.args.get('period', 'month')
        date_col = request.args.get('date_col', 'date')
        value_col = request.args.get('value_col', 'value')

        df = load_dataset(dataset_name)
        calc = MetricsCalculator(df, date_col=date_col, value_col=value_col)
        result = calc.get_comparison(metric_type=metric_type, period=period)
        return jsonify({"status": "success", "comparison": result})
    except FileNotFoundError as e:
        return jsonify({"status": "error", "message": str(e)}), 404
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/comparison/period', methods=['GET'])
def get_period_comparison():
    try:
        dataset_name = request.args.get('dataset', 'default')
        period = request.args.get('period', 'month')
        date_col = request.args.get('date_col', 'date')
        value_col = request.args.get('value_col', 'value')

        df = load_dataset(dataset_name)
        calc = MetricsCalculator(df, date_col=date_col, value_col=value_col)
        result = calc.get_period_comparison(period=period)
        return jsonify(result)
    except FileNotFoundError as e:
        return jsonify({"status": "error", "message": str(e)}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


def init_sample_data():
    sample_file = os.path.join(DATA_DIR, 'default.csv')
    if not os.path.exists(sample_file):
        from sample_data import generate_sample_sales
        df = generate_sample_sales()
        save_dataset(df, 'default')
        print(f"[初始化] 已创建示例数据集: {len(df)} 条记录")


if __name__ == '__main__':
    init_sample_data()
    print("=" * 60)
    print("指标卡片服务启动中...")
    print("API 文档:")
    print("  GET  /api/health                  健康检查")
    print("  GET  /api/dashboard               仪表盘综合数据")
    print("  GET  /api/metrics/all             获取全部指标")
    print("  GET  /api/metrics/total           获取总数")
    print("  GET  /api/metrics/average         获取均值")
    print("  GET  /api/metrics/growth-rate     获取增长率(环比)")
    print("  GET  /api/metrics/yoy-growth      获取同比增长率")
    print("  GET  /api/trend                   获取趋势数据")
    print("  GET  /api/comparison/all          获取全部对比指标")
    print("  GET  /api/comparison/total        总数对比(本期vs上期)")
    print("  GET  /api/comparison/average      均值对比(本期vs上期)")
    print("  GET  /api/comparison/period       周期综合对比")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=True)
