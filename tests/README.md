# Test Suite

This directory contains comprehensive tests for the AI Data Analyst system.

## Test Files

### `test_integration.py` (Main Test Suite)
End-to-end integration tests that validate the complete pipeline.

**Test Classes:**

#### 1. `TestIntegrationPipeline`
Complete pipeline tests with real sample data.

- ✅ **`test_pipeline_with_clean_data`**: Validates full pipeline with high-quality sales data
- ✅ **`test_pipeline_with_messy_data`**: Tests handling of low-quality data with errors
- ✅ **`test_data_quality_scoring`**: Ensures quality scores are consistent and meaningful
- 🔒 **`test_no_raw_data_leakage`** (CRITICAL): Verifies no raw CSV data reaches LLM
- ✅ **`test_outputs_are_generated`**: Validates all outputs (reports, charts, JSON) are created
- ✅ **`test_pipeline_handles_various_data_types`**: Tests with categorical, numeric, time series data
- ✅ **`test_report_structure`**: Validates report has all required sections

#### 2. `TestDataQualityService`
Focused tests for data quality validation and cleaning.

- ✅ **`test_duplicate_detection`**: Verifies duplicate row detection and removal
- ✅ **`test_column_standardization`**: Tests column name standardization (snake_case)

---

## Running Tests

### Quick Start

```bash
# Run all integration tests
pytest tests/test_integration.py -v

# Run a specific test
pytest tests/test_integration.py::TestIntegrationPipeline::test_no_raw_data_leakage -v

# Run with the helper script
python tests/run_tests.py
```

### Test Runner Options

The `run_tests.py` script provides convenient options:

```bash
# All tests
python tests/run_tests.py

# Fast tests only (skip LLM calls)
python tests/run_tests.py --fast

# Critical security tests only
python tests/run_tests.py --critical

# With coverage report
python tests/run_tests.py --coverage

# Verbose output
python tests/run_tests.py --verbose
```

---

## Test Requirements

Install test dependencies:

```bash
pip install pytest pytest-cov
```

Or install all project dependencies:

```bash
pip install -r requirements.txt
```

---

## Understanding the Tests

### 🔒 Critical Test: `test_no_raw_data_leakage`

This is the **most important security test** in the system.

**What it validates:**
- ✅ No individual row data is passed to LLM
- ✅ No cell values appear in LLM context
- ✅ Only aggregated metrics are sent
- ✅ DataFrame objects are excluded
- ✅ Column metadata is OK, but not data values

**Why it matters:**
- Prevents data privacy breaches
- Ensures LLM only interprets, never analyzes raw data
- Core architectural principle: "Truth vs Reasoning separation"

**How it works:**
1. Loads sample CSV with known data
2. Runs pipeline to generate LLM context
3. Serializes context to JSON (what LLM receives)
4. Checks for presence of specific row identifiers (Order IDs)
5. Checks for data values appearing multiple times
6. Validates only metadata and aggregates are present

**Example of what's allowed:**
```json
{
  "data_summary": {
    "row_count": 524,
    "columns": ["order_id", "product_name", "revenue"]
  },
  "metrics": {
    "total_revenue": 345942.15,
    "avg_revenue": 660.39,
    "revenue_by_category": {"Electronics": 125000, ...}
  }
}
```

**Example of what's blocked:**
```json
{
  "rows": [
    {"order_id": "ORD1001", "product": "Laptop", "revenue": 1299.99},  // ❌ RAW DATA
    {"order_id": "ORD1002", "product": "Phone", "revenue": 899.99}     // ❌ RAW DATA
  ]
}
```

---

### Quality Scoring Tests

**`test_data_quality_scoring`**

Validates that the quality scoring algorithm is:
- **Consistent**: Same data = same score
- **Discriminative**: Clean data scores higher than messy data
- **Bounded**: Scores are always between 0-100

**Expected scores:**
- `sales_data.csv`: 90-100 (high quality)
- `financial_data.csv`: 85-100 (high quality)
- `messy_data.csv`: 40-70 (low quality)

---

### Pipeline Tests

**`test_pipeline_with_clean_data`**

Validates the happy path:
1. ✅ Data loads successfully
2. ✅ Quality score is high (>70)
3. ✅ EDA produces metrics and charts
4. ✅ LLM generates insights
5. ✅ Report is created with all sections
6. ✅ All outputs are saved correctly

**`test_pipeline_with_messy_data`**

Validates error handling:
1. ✅ Low quality data is detected
2. ✅ Issues are identified and reported
3. ✅ Transformations are applied
4. ✅ Duplicates are removed
5. ✅ Pipeline completes despite issues
6. ✅ Report includes data quality warnings

---

## Test Data

Tests use sample CSV files from `examples/`:

| File | Rows | Quality | Purpose |
|------|------|---------|---------|
| `sales_data.csv` | 524 | High | Happy path testing |
| `financial_data.csv` | 355 | High | Time series testing |
| `messy_data.csv` | 260 | Low | Error handling testing |

See [examples/README.md](../examples/README.md) for details.

---

## Coverage Reports

Generate coverage reports:

```bash
# Terminal report
pytest tests/ --cov=services --cov-report=term-missing

# HTML report
pytest tests/ --cov=services --cov-report=html
open htmlcov/index.html

# With the helper script
python tests/run_tests.py --coverage
```

**Coverage goals:**
- Services: >80%
- Critical paths (data_quality, insight): >90%
- API endpoints: >70%

---

## Common Test Failures

### "Module not found" errors

```bash
# Ensure you're in project root
cd /path/to/ai-data-analyst

# Install dependencies
pip install -r requirements.txt
```

### LLM-related test failures

If `test_pipeline_with_clean_data` fails with LLM errors:

```bash
# Check your .env file
cat .env

# Ensure API key is set
export OPENAI_API_KEY="your-key-here"
# or
export ANTHROPIC_API_KEY="your-key-here"

# Skip LLM tests during development
pytest tests/ -k "not insight"
```

### "Temporary directory" errors

Tests use `tempfile.mkdtemp()` which should work on all systems. If it fails:

```bash
# Check /tmp is writable
ls -ld /tmp

# Or set custom temp directory
export TMPDIR=/your/writable/path
```

---

## Writing New Tests

### Test Structure Template

```python
def test_my_feature(self, sample_csv_paths, temp_output_dir):
    """Test description"""
    
    # Arrange
    service = MyService()
    input_data = load_sample_data(sample_csv_paths['sales'])
    
    # Act
    result = service.process(input_data)
    
    # Assert
    assert result is not None
    assert result['status'] == 'success'
    assert len(result['outputs']) > 0
```

### Best Practices

1. **Use fixtures**: `sample_csv_paths` and `temp_output_dir` are available
2. **Test one thing**: Each test should validate a single behavior
3. **Clean up**: Use temp directories for outputs
4. **Document**: Add clear docstrings
5. **Fast tests**: Mock LLM calls when possible

---

## Continuous Integration

These tests are designed to run in CI/CD pipelines:

```yaml
# .github/workflows/test.yml
- name: Run tests
  run: |
    pip install -r requirements.txt
    pytest tests/ --cov=services --cov-report=xml
    
- name: Upload coverage
  uses: codecov/codecov-action@v3
```

---

## Test Maintenance

### When to Update Tests

- ✅ Adding new services or features
- ✅ Changing data quality scoring algorithm
- ✅ Modifying LLM prompt structure
- ✅ Updating report format
- ✅ Adding new data types or columns

### Regression Tests

If a bug is found:
1. Write a test that reproduces the bug
2. Fix the bug
3. Verify test passes
4. Keep test to prevent regression

---

## Next Steps

1. Run the full test suite: `python tests/run_tests.py`
2. Examine test coverage: `python tests/run_tests.py --coverage`
3. Run the critical security test: `pytest tests/test_integration.py::TestIntegrationPipeline::test_no_raw_data_leakage -v`
4. Try adding a new test for a custom validation rule
5. Set up CI/CD to run tests automatically

For more information, see the main [README.md](../README.md)
