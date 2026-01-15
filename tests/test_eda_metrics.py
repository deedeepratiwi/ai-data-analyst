"""Test EDA metrics generator."""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from services.eda.metrics import EDAMetricsGenerator


@pytest.fixture
def sample_numeric_df():
    """Create sample dataframe with numeric columns."""
    np.random.seed(42)
    return pd.DataFrame({
        'revenue': np.random.normal(1000, 200, 100),
        'cost': np.random.normal(500, 100, 100),
        'profit': np.random.normal(500, 150, 100)
    })


@pytest.fixture
def sample_categorical_df():
    """Create sample dataframe with categorical columns."""
    return pd.DataFrame({
        'category': ['A', 'B', 'C', 'A', 'B'] * 20,
        'region': ['North', 'South', 'East', 'West'] * 25,
        'status': ['Active', 'Inactive'] * 50
    })


@pytest.fixture
def sample_time_series_df():
    """Create sample dataframe with time series data."""
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    np.random.seed(42)
    return pd.DataFrame({
        'date': dates,
        'sales': np.random.normal(1000, 200, 100) + np.arange(100) * 5,  # Trending up
        'visits': np.random.poisson(50, 100)
    })


@pytest.fixture
def sample_mixed_df():
    """Create sample dataframe with mixed data types."""
    dates = pd.date_range(start='2024-01-01', periods=50, freq='D')
    np.random.seed(42)
    return pd.DataFrame({
        'date': dates,
        'revenue': np.random.normal(1000, 200, 50),
        'category': ['A', 'B', 'C'] * 16 + ['A', 'B'],
        'region': ['North', 'South'] * 25,
        'cost': np.random.normal(500, 100, 50)
    })


class TestEDAMetricsGenerator:
    """Test EDA metrics generator."""
    
    def test_initialization(self):
        """Test generator initialization."""
        generator = EDAMetricsGenerator()
        assert generator.figsize == (10, 6)
        assert generator.dpi == 100
        
        generator_custom = EDAMetricsGenerator(figsize=(12, 8), dpi=150)
        assert generator_custom.figsize == (12, 8)
        assert generator_custom.dpi == 150
    
    def test_generate_metrics_structure(self, sample_mixed_df):
        """Test that generate_metrics returns correct structure."""
        generator = EDAMetricsGenerator()
        metrics = generator.generate_metrics(sample_mixed_df)
        
        # Check top-level keys
        assert 'timestamp' in metrics
        assert 'dataset_overview' in metrics
        assert 'kpis' in metrics
        assert 'numeric_metrics' in metrics
        assert 'categorical_metrics' in metrics
        assert 'temporal_metrics' in metrics
        assert 'correlations' in metrics
        assert 'anomalies' in metrics
        assert 'charts' in metrics
    
    def test_dataset_overview(self, sample_mixed_df):
        """Test dataset overview generation."""
        generator = EDAMetricsGenerator()
        metrics = generator.generate_metrics(sample_mixed_df)
        
        overview = metrics['dataset_overview']
        assert overview['total_rows'] == 50
        assert overview['total_columns'] == 5
        assert overview['numeric_columns'] == 2
        assert overview['categorical_columns'] == 2
        assert overview['datetime_columns'] == 1
        assert 'memory_usage_mb' in overview
        assert 'column_names' in overview
        assert 'column_types' in overview
    
    def test_kpi_computation(self, sample_numeric_df):
        """Test KPI computation."""
        generator = EDAMetricsGenerator()
        metrics = generator.generate_metrics(sample_numeric_df)
        
        kpis = metrics['kpis']
        
        # Check revenue KPIs
        assert 'revenue_kpis' in kpis
        assert 'total' in kpis['revenue_kpis']
        assert 'average' in kpis['revenue_kpis']
        assert 'max' in kpis['revenue_kpis']
        assert 'min' in kpis['revenue_kpis']
        assert 'count' in kpis['revenue_kpis']
        
        # Verify calculations
        assert kpis['revenue_kpis']['count'] == 100
        assert kpis['revenue_kpis']['total'] == pytest.approx(sample_numeric_df['revenue'].sum(), rel=0.01)
        assert kpis['revenue_kpis']['average'] == pytest.approx(sample_numeric_df['revenue'].mean(), rel=0.01)
    
    def test_growth_rates(self, sample_time_series_df):
        """Test growth rate calculation for time series."""
        generator = EDAMetricsGenerator()
        metrics = generator.generate_metrics(sample_time_series_df)
        
        kpis = metrics['kpis']
        
        # Should have growth rate for sales (since it's time series)
        assert 'sales_growth_rate_pct' in kpis
        assert isinstance(kpis['sales_growth_rate_pct'], float)
        
        # Sales should show positive growth (we added trend)
        assert kpis['sales_growth_rate_pct'] > 0
    
    def test_numeric_metrics(self, sample_numeric_df):
        """Test numeric column analysis."""
        generator = EDAMetricsGenerator()
        metrics = generator.generate_metrics(sample_numeric_df)
        
        numeric_metrics = metrics['numeric_metrics']
        
        # Check revenue metrics
        assert 'revenue' in numeric_metrics
        revenue_metrics = numeric_metrics['revenue']
        
        # Check distribution
        assert 'distribution' in revenue_metrics
        dist = revenue_metrics['distribution']
        assert 'mean' in dist
        assert 'median' in dist
        assert 'std' in dist
        assert 'variance' in dist
        assert 'q1' in dist
        assert 'q3' in dist
        assert 'iqr' in dist
        assert 'skewness' in dist
        assert 'kurtosis' in dist
        
        # Check trend
        assert 'trend' in revenue_metrics
        
        # Check percentiles
        assert 'percentiles' in revenue_metrics
        assert 'p50' in revenue_metrics['percentiles']
    
    def test_trend_detection(self, sample_time_series_df):
        """Test trend detection."""
        generator = EDAMetricsGenerator()
        metrics = generator.generate_metrics(sample_time_series_df)
        
        numeric_metrics = metrics['numeric_metrics']
        sales_metrics = numeric_metrics['sales']
        
        trend = sales_metrics['trend']
        assert trend['detected'] is True
        assert trend['direction'] == 'increasing'  # We added upward trend
        assert 'slope' in trend
        assert 'r_squared' in trend
        assert 'p_value' in trend
        assert 'is_significant' in trend
    
    def test_categorical_metrics(self, sample_categorical_df):
        """Test categorical column analysis."""
        generator = EDAMetricsGenerator()
        metrics = generator.generate_metrics(sample_categorical_df)
        
        categorical_metrics = metrics['categorical_metrics']
        
        # Check category column
        assert 'category' in categorical_metrics
        cat_metrics = categorical_metrics['category']
        
        assert 'unique_values' in cat_metrics
        assert 'total_count' in cat_metrics
        assert 'diversity_ratio' in cat_metrics
        assert 'entropy' in cat_metrics
        assert 'top_categories' in cat_metrics
        assert 'mode' in cat_metrics
        assert 'mode_frequency' in cat_metrics
        
        # Top categories should be limited to 10
        assert len(cat_metrics['top_categories']) <= 10
        
        # Each top category should have required fields
        for cat in cat_metrics['top_categories']:
            assert 'category' in cat
            assert 'count' in cat
            assert 'percentage' in cat
    
    def test_temporal_analysis(self, sample_time_series_df):
        """Test temporal pattern analysis."""
        generator = EDAMetricsGenerator()
        metrics = generator.generate_metrics(sample_time_series_df)
        
        temporal_metrics = metrics['temporal_metrics']
        
        assert temporal_metrics['temporal_data_detected'] is True
        assert 'patterns' in temporal_metrics
        assert 'date' in temporal_metrics['patterns']
        
        date_pattern = temporal_metrics['patterns']['date']
        assert 'date_range' in date_pattern
        assert 'start' in date_pattern['date_range']
        assert 'end' in date_pattern['date_range']
        assert 'span_days' in date_pattern['date_range']
        
        # Should have time series metrics for numeric columns
        assert 'time_series_metrics' in date_pattern
    
    def test_correlations(self, sample_numeric_df):
        """Test correlation analysis."""
        generator = EDAMetricsGenerator()
        metrics = generator.generate_metrics(sample_numeric_df)
        
        correlations = metrics['correlations']
        
        assert correlations['correlation_analysis_available'] is True
        assert 'total_numeric_columns' in correlations
        assert 'significant_correlations' in correlations
        assert 'correlation_matrix_shape' in correlations
        
        # Check significant correlations structure
        for corr in correlations['significant_correlations']:
            assert 'column1' in corr
            assert 'column2' in corr
            assert 'correlation' in corr
            assert 'strength' in corr
            assert 'direction' in corr
            assert corr['strength'] in ['weak', 'moderate', 'strong']
            assert corr['direction'] in ['positive', 'negative']
    
    def test_anomaly_detection(self):
        """Test anomaly detection using IQR."""
        # Create data with outliers
        np.random.seed(42)
        data = np.random.normal(100, 10, 100)
        data = np.append(data, [200, 250, -50])  # Add outliers
        
        df = pd.DataFrame({'value': data})
        
        generator = EDAMetricsGenerator()
        metrics = generator.generate_metrics(df)
        
        anomalies = metrics['anomalies']
        
        assert anomalies['anomalies_detected'] is True
        assert 'value' in anomalies['columns_with_anomalies']
        
        value_anomalies = anomalies['details']['value']
        assert 'total_anomalies' in value_anomalies
        assert 'lower_outliers' in value_anomalies
        assert 'upper_outliers' in value_anomalies
        assert 'anomaly_percentage' in value_anomalies
        assert 'lower_bound' in value_anomalies
        assert 'upper_bound' in value_anomalies
        assert value_anomalies['total_anomalies'] > 0
    
    def test_chart_generation(self, sample_mixed_df):
        """Test chart generation."""
        generator = EDAMetricsGenerator()
        metrics = generator.generate_metrics(sample_mixed_df)
        
        charts = metrics['charts']
        
        # Should have some charts
        assert len(charts) > 0
        
        # Check that charts are base64 encoded strings
        for chart_name, chart_data in charts.items():
            assert isinstance(chart_data, str)
            assert len(chart_data) > 0
            
            # Base64 string check (basic)
            try:
                import base64
                base64.b64decode(chart_data)
            except:
                pytest.fail(f"Chart {chart_name} is not valid base64")
    
    def test_no_raw_data_in_output(self, sample_mixed_df):
        """Verify that output contains NO raw data, only aggregates."""
        generator = EDAMetricsGenerator()
        metrics = generator.generate_metrics(sample_mixed_df)
        
        # Convert to string and check for common data leakage patterns
        import json
        metrics_str = json.dumps(metrics)
        
        # Should not contain large arrays of values
        # (charts are base64 encoded, so they're strings)
        
        # Check that we don't have lists of raw values in KPIs
        for key, value in metrics['kpis'].items():
            if isinstance(value, dict):
                for k, v in value.items():
                    assert not isinstance(v, list) or len(v) < 20, f"Suspicious list in KPIs: {key}.{k}"
        
        # Numeric metrics should only have aggregated stats
        for col_name, col_metrics in metrics['numeric_metrics'].items():
            dist = col_metrics['distribution']
            assert isinstance(dist['mean'], (int, float))
            assert isinstance(dist['median'], (int, float))
            # Should not have arrays of values
    
    def test_empty_dataframe(self):
        """Test handling of empty dataframe."""
        df = pd.DataFrame()
        generator = EDAMetricsGenerator()
        metrics = generator.generate_metrics(df)
        
        assert metrics['dataset_overview']['total_rows'] == 0
        assert metrics['dataset_overview']['total_columns'] == 0
    
    def test_single_column(self):
        """Test handling of single column dataframe."""
        df = pd.DataFrame({'value': [1, 2, 3, 4, 5]})
        generator = EDAMetricsGenerator()
        metrics = generator.generate_metrics(df)
        
        assert metrics['dataset_overview']['total_columns'] == 1
        assert 'value' in metrics['numeric_metrics']
        # Correlation should not be available (need at least 2 numeric columns)
        assert metrics['correlations']['correlation_analysis_available'] is False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
