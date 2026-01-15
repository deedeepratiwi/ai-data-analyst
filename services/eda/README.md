# EDA Metrics Generator

## Overview

The `EDAMetricsGenerator` is a production-ready service that performs comprehensive exploratory data analysis on cleaned pandas DataFrames. It follows the architectural principle of **separating truth from reasoning**: it computes deterministic statistical metrics and generates visualizations, outputting only aggregated data suitable for LLM interpretation.

## Key Features

✓ **NO RAW DATA** - Returns only aggregated statistics, never individual data points  
✓ **Comprehensive Analysis** - 9 categories of metrics including KPIs, trends, correlations, and anomalies  
✓ **Automatic Chart Generation** - Creates distribution plots, bar charts, time series, and correlation heatmaps  
✓ **Time Series Support** - Automatically detects and analyzes temporal patterns  
✓ **Anomaly Detection** - Uses IQR method to identify outliers  
✓ **MCP-Ready** - Structured JSON output designed for LLM consumption  

## Usage

```python
from services.eda.metrics import EDAMetricsGenerator
import pandas as pd

# Load your cleaned dataframe
df = pd.read_csv('cleaned_data.csv')

# Initialize generator
generator = EDAMetricsGenerator(figsize=(10, 6), dpi=100)

# Generate comprehensive metrics
metrics = generator.generate_metrics(df)

# Access results
print(f"Total rows: {metrics['dataset_overview']['total_rows']}")
print(f"KPIs: {metrics['kpis']}")
print(f"Charts generated: {len(metrics['charts'])}")
```

## Output Structure

The `generate_metrics()` method returns a dictionary with the following structure:

```json
{
  "timestamp": "2024-01-15T08:00:00",
  "dataset_overview": {
    "total_rows": 1000,
    "total_columns": 10,
    "numeric_columns": 5,
    "categorical_columns": 3,
    "datetime_columns": 1,
    "memory_usage_mb": 0.5,
    "column_names": ["col1", "col2", ...],
    "column_types": {"col1": "int64", ...}
  },
  "kpis": {
    "revenue_kpis": {
      "total": 1000000.0,
      "average": 1000.0,
      "max": 5000.0,
      "min": 100.0,
      "count": 1000
    },
    "revenue_growth_rate_pct": 15.5
  },
  "numeric_metrics": {
    "revenue": {
      "distribution": {
        "mean": 1000.0,
        "median": 950.0,
        "std": 200.0,
        "variance": 40000.0,
        "min": 100.0,
        "max": 5000.0,
        "q1": 800.0,
        "q3": 1200.0,
        "iqr": 400.0,
        "skewness": 0.5,
        "kurtosis": 0.3,
        "skewness_interpretation": "right_skewed"
      },
      "trend": {
        "detected": true,
        "direction": "increasing",
        "slope": 2.5,
        "r_squared": 0.75,
        "p_value": 0.001,
        "is_significant": true,
        "strength": "strong"
      },
      "percentiles": {
        "p5": 500.0,
        "p25": 800.0,
        "p50": 950.0,
        "p75": 1200.0,
        "p95": 2000.0
      }
    }
  },
  "categorical_metrics": {
    "category": {
      "unique_values": 5,
      "total_count": 1000,
      "diversity_ratio": 0.005,
      "entropy": 1.5,
      "top_categories": [
        {"category": "A", "count": 400, "percentage": 40.0},
        {"category": "B", "count": 300, "percentage": 30.0}
      ],
      "mode": "A",
      "mode_frequency": 400,
      "mode_percentage": 40.0
    }
  },
  "temporal_metrics": {
    "temporal_data_detected": true,
    "patterns": {
      "date": {
        "date_range": {
          "start": "2024-01-01",
          "end": "2024-12-31",
          "span_days": 365
        },
        "records_by_year": {2024: 1000},
        "records_by_month": {1: 100, 2: 95, ...},
        "time_series_metrics": {
          "revenue": {
            "daily_average_mean": 1000.0,
            "daily_average_std": 100.0,
            "peak_date": "2024-12-25",
            "peak_value": 50000.0
          }
        }
      }
    }
  },
  "correlations": {
    "correlation_analysis_available": true,
    "total_numeric_columns": 5,
    "significant_correlations": [
      {
        "column1": "revenue",
        "column2": "profit",
        "correlation": 0.85,
        "strength": "strong",
        "direction": "positive"
      }
    ]
  },
  "anomalies": {
    "anomalies_detected": true,
    "columns_with_anomalies": ["revenue"],
    "details": {
      "revenue": {
        "total_anomalies": 15,
        "lower_outliers": 5,
        "upper_outliers": 10,
        "anomaly_percentage": 1.5,
        "lower_bound": 0.0,
        "upper_bound": 3000.0,
        "iqr": 400.0,
        "extreme_anomalies": 2
      }
    }
  },
  "charts": {
    "distribution_revenue": "base64_encoded_png_string",
    "bar_category": "base64_encoded_png_string",
    "timeseries_date_revenue": "base64_encoded_png_string",
    "correlation_heatmap": "base64_encoded_png_string"
  }
}
```

## Metrics Categories

### 1. Dataset Overview
- Row and column counts
- Data types breakdown
- Memory usage
- Column names and types

### 2. KPIs (Key Performance Indicators)
- **Numeric columns**: Total, average, max, min, count
- **Time series**: Growth rates, rolling averages

### 3. Numeric Metrics
- **Distribution**: Mean, median, std, variance, quartiles, IQR, skewness, kurtosis
- **Trend**: Direction, slope, R², p-value, strength
- **Percentiles**: p5, p10, p25, p50, p75, p90, p95

### 4. Categorical Metrics
- Unique values and diversity ratio
- Entropy
- Top categories (limited to 10)
- Mode and frequency

### 5. Temporal Metrics
- Date range and span
- Records by year, month, day of week
- Time series metrics for numeric columns

### 6. Correlations
- Correlation matrix for numeric columns
- Significant correlation pairs (|r| > 0.3)
- Strength classification (weak/moderate/strong)

### 7. Anomalies
- IQR-based outlier detection
- Lower and upper outliers
- Anomaly percentage
- Extreme anomaly detection (3× IQR)

### 8. Charts
- **Distribution plots**: Histogram + box plot for numeric columns
- **Bar charts**: Top categories for categorical columns
- **Time series plots**: Value over time when datetime column exists
- **Correlation heatmap**: For multiple numeric columns

All charts are returned as base64-encoded PNG strings.

## Architecture Principles

### 1. Truth vs. Reasoning Separation
- **Truth (Python)**: All numerical calculations (means, trends, correlations)
- **Reasoning (LLM)**: Interpretation of the metrics (will be done by Insight Service)
- The EDA service NEVER interprets data, only computes metrics

### 2. No Raw Data Leakage
- Output contains **only aggregated statistics**
- Categorical data limited to top 10 categories
- Correlations limited to top 20 pairs
- Charts are pre-rendered (no raw data needed to recreate)

### 3. MCP-Ready Output
- Structured JSON format
- Type-safe values (proper int/float/bool types)
- Null handling for missing data
- Suitable for direct consumption by LLM via MCP

## Testing

Run the comprehensive test suite:

```bash
pytest tests/test_eda_metrics.py -v
```

Run the example script:

```bash
PYTHONPATH=. python examples/eda_metrics_example.py
```

## Dependencies

```
pandas>=2.2.0
numpy>=1.26.3
scipy>=1.11.4
matplotlib>=3.8.2
seaborn>=0.13.1
```

## Integration with Other Services

### Input: From Data Quality Service
```python
from services.data_quality.profiler import DataQualityProfiler
from services.eda.metrics import EDAMetricsGenerator

# Clean data first
profiler = DataQualityProfiler()
cleaned_df, validation_summary = profiler.profile_and_clean(raw_df)

# Then analyze
generator = EDAMetricsGenerator()
metrics = generator.generate_metrics(cleaned_df)
```

### Output: To Insight Service
```python
# The metrics dictionary can be passed directly to the LLM via MCP
# for business insight generation

from services.insights.generator import InsightGenerator

insight_gen = InsightGenerator()
insights = insight_gen.generate_insights(
    metrics=metrics,
    context={"business_domain": "retail", "goal": "increase_revenue"}
)
```

## Configuration

The generator can be customized:

```python
generator = EDAMetricsGenerator(
    figsize=(12, 8),  # Chart size
    dpi=150           # Chart resolution
)
```

## Best Practices

1. **Always clean data first** using the Data Quality Service
2. **Provide business context** when available (optional parameter)
3. **Store metrics** for reproducibility and audit trail
4. **Separate charts** from metrics when exporting to JSON (charts are large)
5. **Limit chart generation** if working with very large datasets (modify source to reduce chart count)

## Limitations

- Maximum 10 top categories per categorical column (by design)
- Maximum 20 significant correlations (by design)
- Charts limited to first 6 numeric/categorical columns (by design)
- Requires cleaned data (use Data Quality Service first)
- Time series analysis assumes first datetime column is the time dimension

## Performance Considerations

- **Memory**: Charts are stored as base64 strings, can be large
- **Computation**: Correlation matrix is O(n²) for n numeric columns
- **Scalability**: Designed for datasets up to ~1M rows

For larger datasets, consider:
- Sampling before analysis
- Generating fewer charts
- Computing correlations on subset of columns

## Error Handling

The service gracefully handles:
- Empty dataframes
- Missing values (excluded from calculations)
- Single-column dataframes
- No numeric/categorical/datetime columns
- Failed chart generation (logs warning, continues)

## Logging

Follows the standard logging pattern:

```python
import logging
logger = logging.getLogger(__name__)
```

Logs are emitted at:
- **INFO**: Start/completion of analysis, chart generation count
- **WARNING**: Failed chart generation, insufficient data for specific analyses

---

For questions or issues, please refer to the test suite in `tests/test_eda_metrics.py` for usage examples.
