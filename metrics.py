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
        sums, counts = self._group_by_period(period)

        current_val, current_period = self._get_last_valid_period(sums, counts)
        if current_val is None:
            return self._empty_growth_result("增长率", "当前周期无有效数据")

        prev_idx = sums.index.get_loc(current_period) - 1
        if prev_idx < 0:
            return self._empty_growth_result("增长率", "无上一周期数据")

        prev_period = sums.index[prev_idx]
        prev_count = int(counts.loc[prev_period])
        if prev_count == 0:
            return self._empty_growth_result(
                "增长率",
                f"上一{self._period_name(period)}（{prev_period.strftime('%Y-%m')}）无原始数据覆盖，无法计算环比"
            )

        previous = float(sums.loc[prev_period])
        rate = self._calc_percent_change(current_val, previous)

        return {
            "name": "增长率",
            "value": round(rate, 2),
            "unit": "%",
            "description": f"较上一{self._period_name(period)}的环比增长率",
            "current_value": round(current_val, 2),
            "previous_value": round(previous, 2)
        }

    def get_yoy_growth(self, period: str = 'month') -> dict:
        sums, counts = self._group_by_period(period)

        current_val, current_period = self._get_last_valid_period(sums, counts)
        if current_val is None:
            return self._empty_growth_result("同比增长率", "当前周期无有效数据")

        year_offset = relativedelta(years=1)
        last_year_period = current_period - year_offset

        if last_year_period not in sums.index:
            return self._empty_growth_result(
                "同比增长率",
                f"去年同期（{last_year_period.strftime('%Y-%m')}）数据缺失，无法计算同比"
            )

        last_year_count = int(counts.loc[last_year_period])
        if last_year_count == 0:
            return self._empty_growth_result(
                "同比增长率",
                f"去年同期（{last_year_period.strftime('%Y-%m')}）无原始数据覆盖，无法计算同比"
            )

        last_year = float(sums.loc[last_year_period])
        rate = self._calc_percent_change(current_val, last_year)

        return {
            "name": "同比增长率",
            "value": round(rate, 2),
            "unit": "%",
            "description": f"较去年同{self._period_name(period)}的同比增长率",
            "current_value": round(current_val, 2),
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
        sums, counts = self._group_by_period(period)
        recent_sums = sums.tail(limit)
        recent_counts = counts.tail(limit)

        trend = []
        for date_val in recent_sums.index:
            val = float(recent_sums.loc[date_val])
            cnt = int(recent_counts.loc[date_val])
            trend.append({
                "period": str(date_val),
                "value": round(val, 2),
                "has_data": cnt > 0
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

    def _group_by_period(self, period: str) -> tuple[pd.Series, pd.Series]:
        freq_map = {
            'day': 'D',
            'week': 'W-MON',
            'month': 'ME',
            'quarter': 'QE',
            'year': 'YE'
        }
        freq = freq_map.get(period, 'ME')
        grouped = self.df.set_index(self.date_col)[self.value_col].resample(freq)
        sums = grouped.sum()
        counts = grouped.count()
        return sums, counts

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
    def _empty_growth_result(name: str, reason: str = "数据不足，无法计算增长率") -> dict:
        return {
            "name": name,
            "value": None,
            "unit": "%",
            "description": reason
        }

    @staticmethod
    def _get_last_valid_period(sums: pd.Series, counts: pd.Series) -> tuple:
        for i in range(len(sums) - 1, -1, -1):
            if int(counts.iloc[i]) > 0:
                return float(sums.iloc[i]), sums.index[i]
        return None, None
