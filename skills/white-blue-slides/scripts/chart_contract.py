"""A small declarative chart contract; no executable ECharts options in deck data."""
import math


def chart_errors(block):
    errors = []
    kind = block.get('chart_type')
    if not isinstance(kind, str) or kind not in {'bar', 'line', 'donut'}:
        errors.append('chart_type 可选 bar / line / donut')
    categories, series = block.get('categories'), block.get('series')
    if not isinstance(categories, list) or not 2 <= len(categories) <= 8 or any(not isinstance(v, str) or not v.strip() for v in categories):
        errors.append('chart.categories 需要 2–8 个非空类别'); categories = []
    if not isinstance(series, list) or not 1 <= len(series) <= 3 or any(not isinstance(v, dict) for v in series):
        errors.append('chart.series 需要 1–3 个数据序列'); series = []
    for item in series:
        if not isinstance(item.get('name'), str) or not item['name'].strip():
            errors.append('chart.series[].name 必填')
        values = item.get('values')
        if not isinstance(values, list) or len(values) != len(categories):
            errors.append('chart.series[].values 必须逐项对应 categories'); continue
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0 for v in values):
            errors.append('当前图表模板需要有限的非负数；缺失值不能假装为 0')
        elif kind == 'donut' and sum(values) <= 0:
            errors.append('donut 数据合计须大于 0')
    if kind == 'donut' and len(series) != 1:
        errors.append('donut 需要一个数据序列')
    for key in ('unit', 'source'):
        if not isinstance(block.get(key), str) or not block[key].strip():
            errors.append(f'chart.{key} 必填；示例数据须明确标注，真实数据须有来源和口径')
    return errors
