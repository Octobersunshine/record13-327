import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class MetricsCalculator:
    def __init__(self, df: pd.DataFrame, date_col: str = 'date', value_col: str = 'value'):
        self.df = df.copy()
        self.date_col = date_col
        self.value_col = value_col
        self._validate_data()
        self._prepare_data()

    def _validate_data(self):
        if self.date_col not in self.df.columns:
            raise ValueError(f"日期列 '{self.date_col}' 不存在于数据中")
        if self.value_col not in self.df.columns:
            raise ValueError(f"数值列 '{self.value_col}' 不存在于数据中")

    def _prepare_data(self):
        self.df[self.date_col] = pd.to_datetime(self.df[self.date_col])
        self.df = self.df.sort_values(self.date_col).reset_index(drop=True)

    def get_total(self, start_date=None, end_date=None) -> dict:
        filtered = self._filter_by_date(start_date, end_date)
        total = float(filtered[self.value_col].sum())
        count = len(filtered)
        return {
            "name": "总数",
            "value": round(total, 2),
            "unit": "",
            "description": f"统计周期内累计总和，共 {count} 条记录"
        }

    def get_average(self, start_date=None, end_date=None) -> dict:
        filtered = self._filter_by_date(start_date, end_date)
        avg = float(filtered[self.value_col].mean()) if len(filtered) > 0 else 0
        return {
            "name": "均值",
            "value": round(avg, 2),
            "unit": "",
            "description": "统计周期内数值的算术平均值"
        }

    def get_growth_rate(self, period: str = 'month') -> dict:
        grouped = self._group_by_period(period)
        if len(grouped) < 2:
            return self._empty_growth_result("增长率")

        current = float(grouped.iloc[-1])
        previous = float(grouped.iloc[-2])
        rate = self._calc_percent_change(current, previous)

        return {
            "name": "增长率",
            "value": round(rate, 2),
            "unit": "%",
            "description": f"较上一{self._period_name(period)}的环比增长率",
            "current_value": round(current, 2),
            "previous_value": round(previous, 2)
        }

    def get_yoy_growth(self, period: str = 'month') -> dict:
        grouped = self._group_by_period(period)
        periods = len(grouped)

        if periods <= 12:
            return self._empty_growth_result("同比增长率")

        current = float(grouped.iloc[-1])
        last_year = float(grouped.iloc[-13])
        rate = self._calc_percent_change(current, last_year)

        return {
            "name": "同比增长率",
            "value": round(rate, 2),
            "unit": "%",
            "description": f"较去年同{self._period_name(period)}的同比增长率",
            "current_value": round(current, 2),
            "last_year_value": round(last_year, 2)
        }

    def get_all_metrics(self, start_date=None, end_date=None, period: str = 'month') -> dict:
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "period": self._period_name(period),
            "date_range": {
                "start": str(start_date) if start_date else str(self.df[self.date_col].min().date()),
                "end": str(end_date) if end_date else str(self.df[self.date_col].max().date())
            },
            "metrics": {
                "total": self.get_total(start_date, end_date),
                "average": self.get_average(start_date, end_date),
                "growth_rate": self.get_growth_rate(period),
                "yoy_growth": self.get_yoy_growth(period)
            }
        }

    def get_custom_metrics(self, metrics_list: list, start_date=None, end_date=None, period: str = 'month') -> dict:
        metric_funcs = {
            'total': lambda: self.get_total(start_date, end_date),
            'average': lambda: self.get_average(start_date, end_date),
            'growth_rate': lambda: self.get_growth_rate(period),
            'yoy_growth': lambda: self.get_yoy_growth(period)
        }

        result = {}
        for m in metrics_list:
            if m in metric_funcs:
                result[m] = metric_funcs[m]()

        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "metrics": result
        }

    def get_trend_data(self, period: str = 'month', limit: int = 12) -> dict:
        grouped = self._group_by_period(period)
        recent = grouped.tail(limit)

        trend = []
        for i, (date_val, val) in enumerate(recent.items()):
            trend.append({
                "period": str(date_val),
                "value": round(float(val), 2)
            })

        return {
            "status": "success",
            "trend": trend
        }

    def _filter_by_date(self, start_date, end_date):
        filtered = self.df
        if start_date:
            filtered = filtered[filtered[self.date_col] >= pd.to_datetime(start_date)]
        if end_date:
            filtered = filtered[filtered[self.date_col] <= pd.to_datetime(end_date)]
        return filtered

    def _group_by_period(self, period: str) -> pd.Series:
        freq_map = {
            'day': 'D',
            'week': 'W-MON',
            'month': 'ME',
            'quarter': 'QE',
            'year': 'YE'
        }
        freq = freq_map.get(period, 'ME')
        return self.df.set_index(self.date_col)[self.value_col].resample(freq).sum()

    @staticmethod
    def _calc_percent_change(current: float, previous: float) -> float:
        if previous == 0:
            return 0.0 if current == 0 else float('inf')
        return ((current - previous) / abs(previous)) * 100

    @staticmethod
    def _period_name(period: str) -> str:
        names = {
            'day': '天',
            'week': '周',
            'month': '月',
            'quarter': '季度',
            'year': '年'
        }
        return names.get(period, '周期')

    @staticmethod
    def _empty_growth_result(name: str) -> dict:
        return {
            "name": name,
            "value": None,
            "unit": "%",
            "description": "数据不足，无法计算增长率"
        }
