# Examples Directory

This directory contains sample CSV files and example scripts demonstrating the AI Data Analyst system.

## Sample Data Files

### 1. `sales_data.csv` (524 rows)
**High-quality e-commerce sales data**

- **Characteristics**: Clean, well-structured data with consistent formatting
- **Columns**: Order ID, Date, Product Category, Product Name, Region, Customer Segment, Unit Price, Quantity, Total Revenue, Discount, Customer Satisfaction, Shipping Days
- **Use Case**: Demonstrates the system working with good quality data
- **Expected Quality Score**: 90-100
- **Date Range**: 2023-01-01 to 2024-06-24
- **Total Revenue**: ~$346K
- **Categories**: Electronics, Clothing, Home & Garden, Books, Sports, Toys

**Insights you should expect:**
- Revenue trends by category and region
- Customer segment analysis
- Seasonal patterns
- Satisfaction correlations with segments

---

### 2. `financial_data.csv` (355 rows)
**Multi-year financial metrics with time series**

- **Characteristics**: Clean financial data with temporal patterns
- **Columns**: Transaction ID, Date, Quarter, Business Unit, Revenue, Cost, Profit, Profit Margin, Employees, Active Customers, Customer Acquisition Cost, Average Contract Value
- **Use Case**: Demonstrates time series analysis and trend detection
- **Expected Quality Score**: 85-100
- **Date Range**: 2021-01-01 to 2023-11-17 (3 years)
- **Business Units**: Digital Services, Hardware Sales, Consulting, Cloud Infrastructure
- **Total Revenue**: ~$72.8M

**Insights you should expect:**
- Growth trends by business unit
- Profit margin analysis
- Customer acquisition efficiency
- Quarterly performance patterns

---

### 3. `messy_data.csv` (260 rows including duplicates)
**Low-quality data with multiple issues**

- **Characteristics**: Intentionally messy to test data quality service
- **Issues Present**:
  - Missing values (~5% of cells)
  - Duplicate rows (~10%)
  - Inconsistent naming (laptop, LAPTOP, Laptop)
  - Inconsistent column names (spaces, underscores, trailing spaces)
  - Invalid values (ERROR, UNKNOWN, N/A, #REF!, --)
  - Invalid dates and negative numbers
  - Calculation errors (revenue ≠ price × quantity)
  
- **Use Case**: Demonstrates data cleaning and quality assessment
- **Expected Quality Score**: 40-70
- **Issues Detected**: 8-12 different types of problems
- **Transformations Applied**: 5-8 cleaning operations

**Insights you should expect:**
- Comprehensive list of data quality issues
- Before/after comparison
- Recommendations for data collection improvements
- Limited business insights due to quality concerns

---

## Running the Examples

### End-to-End Analysis Script

The `run_analysis.py` script demonstrates the complete pipeline without using the API:

```bash
# Analyze high-quality sales data
python examples/run_analysis.py examples/sales_data.csv

# Analyze financial time series
python examples/run_analysis.py examples/financial_data.csv

# Analyze messy data (shows data quality handling)
python examples/run_analysis.py examples/messy_data.csv

# Specify custom output directory
python examples/run_analysis.py examples/sales_data.csv /tmp/my_analysis
```

### What the Script Does

1. **Data Quality Validation**
   - Loads the CSV file
   - Detects and fixes quality issues
   - Standardizes column names
   - Removes duplicates
   - Generates quality score

2. **Exploratory Data Analysis**
   - Computes KPIs and metrics
   - Detects trends and patterns
   - Generates visualizations
   - Identifies anomalies

3. **Insight Generation (LLM)**
   - Creates business insights
   - Generates recommendations
   - Provides executive summary
   - **Note**: Only receives aggregated metrics, never raw data

4. **Report Building**
   - Combines all components
   - Creates Markdown report
   - Includes visualizations
   - Exports to file

### Output Structure

After running the analysis, you'll find:

```
storage/jobs/<timestamp>/
├── cleaned_data.csv           # Cleaned version of input
├── 01_validation.json         # Data quality report
├── 02_eda_metrics.json        # Computed metrics
├── 03_insights.json           # LLM-generated insights
├── final_report.md            # Complete report
└── charts/                    # Visualizations
    ├── distribution_*.png
    ├── correlation_heatmap.png
    └── trend_*.png
```

---

## Using with the API

You can also upload these files through the REST API:

```bash
# Start the API server
uvicorn api.main:app --reload

# Upload and analyze
curl -X POST "http://localhost:8000/upload" \
  -F "file=@examples/sales_data.csv" \
  -F "business_context=E-commerce sales analysis"

# Check job status
curl "http://localhost:8000/job/{job_id}"

# Get report
curl "http://localhost:8000/report/{job_id}"
```

---

## Integration Tests

Run the complete test suite:

```bash
# Run all integration tests
pytest tests/test_integration.py -v

# Run specific test
pytest tests/test_integration.py::TestIntegrationPipeline::test_no_raw_data_leakage -v

# Run with coverage
pytest tests/test_integration.py --cov=services --cov-report=html
```

### Critical Tests

1. **`test_no_raw_data_leakage`**: Verifies that no raw CSV data reaches the LLM
2. **`test_data_quality_scoring`**: Ensures quality scoring is consistent
3. **`test_pipeline_with_messy_data`**: Tests handling of poor quality data
4. **`test_outputs_are_generated`**: Validates all outputs are created

---

## Expected Results Summary

| Dataset | Quality Score | KPIs | Charts | Issues | Processing Time |
|---------|--------------|------|--------|--------|----------------|
| sales_data.csv | 90-100 | 15-20 | 5-8 | 0-2 | 15-30s |
| financial_data.csv | 85-100 | 12-18 | 5-7 | 0-3 | 15-30s |
| messy_data.csv | 40-70 | 8-12 | 3-5 | 8-12 | 20-40s |

---

## Creating Your Own Test Data

To create custom test CSV files:

```python
import pandas as pd
import numpy as np

# Your data
df = pd.DataFrame({
    'date': pd.date_range('2023-01-01', periods=100),
    'revenue': np.random.uniform(1000, 5000, 100),
    'category': np.random.choice(['A', 'B', 'C'], 100)
})

df.to_csv('examples/my_data.csv', index=False)

# Then analyze
# python examples/run_analysis.py examples/my_data.csv
```

---

## Troubleshooting

**"Module not found" errors**
```bash
# Make sure you're in the project root
cd /path/to/ai-data-analyst

# Install dependencies
pip install -r requirements.txt
```

**LLM timeout or errors**
```bash
# Check your .env file has valid API key
cp .env.example .env
# Edit .env and add your OpenAI/Anthropic API key
```

**No charts generated**
```bash
# Install visualization dependencies
pip install matplotlib seaborn plotly
```

---

## Next Steps

1. Try running the example script with all three datasets
2. Examine the generated reports in `storage/jobs/`
3. Run the integration tests to validate the system
4. Create your own test CSV and analyze it
5. Explore the API endpoints with the provided curl commands

For more information, see the main [README.md](../README.md)
