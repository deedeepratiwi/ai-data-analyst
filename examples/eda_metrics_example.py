"""
Example usage of EDA Metrics Generator.

This script demonstrates how to use the EDAMetricsGenerator to analyze a dataset.
"""
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta
from services.eda.metrics import EDAMetricsGenerator


def create_sample_sales_data():
    """Create sample sales dataset."""
    np.random.seed(42)
    
    # Generate dates
    dates = pd.date_range(start='2024-01-01', periods=365, freq='D')
    
    # Generate sales with upward trend and seasonality
    base_sales = 1000
    trend = np.arange(365) * 2
    seasonality = 200 * np.sin(np.arange(365) * 2 * np.pi / 30)  # Monthly seasonality
    noise = np.random.normal(0, 100, 365)
    sales = base_sales + trend + seasonality + noise
    
    # Generate other metrics
    data = {
        'date': dates,
        'sales': sales,
        'units_sold': (sales / 25 + np.random.normal(0, 5, 365)).astype(int),
        'customer_count': (sales / 50 + np.random.normal(0, 10, 365)).astype(int),
        'category': np.random.choice(['Electronics', 'Clothing', 'Food', 'Books'], 365),
        'region': np.random.choice(['North', 'South', 'East', 'West'], 365),
        'channel': np.random.choice(['Online', 'Retail', 'Mobile'], 365, p=[0.5, 0.3, 0.2])
    }
    
    return pd.DataFrame(data)


def main():
    """Run example EDA analysis."""
    print("=" * 80)
    print("EDA Metrics Generator - Example Usage")
    print("=" * 80)
    print()
    
    # Create sample data
    print("1. Creating sample sales dataset...")
    df = create_sample_sales_data()
    print(f"   Dataset shape: {df.shape}")
    print(f"   Columns: {', '.join(df.columns)}")
    print()
    
    # Initialize EDA generator
    print("2. Initializing EDA Metrics Generator...")
    generator = EDAMetricsGenerator(figsize=(12, 6), dpi=100)
    print("   Generator initialized")
    print()
    
    # Generate metrics
    print("3. Generating comprehensive metrics...")
    metrics = generator.generate_metrics(df)
    print(f"   Metrics generated at: {metrics['timestamp']}")
    print()
    
    # Display overview
    print("4. Dataset Overview:")
    overview = metrics['dataset_overview']
    print(f"   - Total rows: {overview['total_rows']}")
    print(f"   - Total columns: {overview['total_columns']}")
    print(f"   - Numeric columns: {overview['numeric_columns']}")
    print(f"   - Categorical columns: {overview['categorical_columns']}")
    print(f"   - Datetime columns: {overview['datetime_columns']}")
    print(f"   - Memory usage: {overview['memory_usage_mb']:.2f} MB")
    print()
    
    # Display KPIs
    print("5. Key Performance Indicators:")
    kpis = metrics['kpis']
    if 'sales_kpis' in kpis:
        sales_kpis = kpis['sales_kpis']
        print(f"   Sales:")
        print(f"   - Total: ${sales_kpis['total']:,.2f}")
        print(f"   - Average: ${sales_kpis['average']:,.2f}")
        print(f"   - Max: ${sales_kpis['max']:,.2f}")
        print(f"   - Min: ${sales_kpis['min']:,.2f}")
        print(f"   - Count: {sales_kpis['count']}")
    
    if 'sales_growth_rate_pct' in kpis:
        print(f"   - Growth rate: {kpis['sales_growth_rate_pct']:.2f}%")
    print()
    
    # Display numeric metrics
    print("6. Numeric Column Analysis:")
    numeric_metrics = metrics['numeric_metrics']
    for col_name, col_metrics in list(numeric_metrics.items())[:2]:  # Show first 2
        print(f"   {col_name}:")
        dist = col_metrics['distribution']
        print(f"   - Mean: {dist['mean']:.2f}, Median: {dist['median']:.2f}, Std: {dist['std']:.2f}")
        print(f"   - Skewness: {dist.get('skewness', 'N/A')} ({dist.get('skewness_interpretation', 'N/A')})")
        
        trend = col_metrics['trend']
        if trend.get('detected'):
            print(f"   - Trend: {trend['direction']} ({trend['strength']}, R²={trend['r_squared']:.3f})")
    print()
    
    # Display categorical metrics
    print("7. Categorical Column Analysis:")
    categorical_metrics = metrics['categorical_metrics']
    for col_name, col_metrics in list(categorical_metrics.items())[:2]:  # Show first 2
        print(f"   {col_name}:")
        print(f"   - Unique values: {col_metrics['unique_values']}")
        print(f"   - Mode: {col_metrics['mode']} ({col_metrics['mode_percentage']:.1f}%)")
        print(f"   - Top 3 categories:")
        for cat in col_metrics['top_categories'][:3]:
            print(f"     • {cat['category']}: {cat['count']} ({cat['percentage']:.1f}%)")
    print()
    
    # Display temporal patterns
    print("8. Temporal Patterns:")
    temporal_metrics = metrics['temporal_metrics']
    if temporal_metrics['temporal_data_detected']:
        for date_col, pattern in temporal_metrics['patterns'].items():
            print(f"   {date_col}:")
            date_range = pattern['date_range']
            print(f"   - Range: {date_range['start']} to {date_range['end']}")
            print(f"   - Span: {date_range['span_days']} days")
            
            if 'time_series_metrics' in pattern:
                print(f"   - Time series metrics available for {len(pattern['time_series_metrics'])} columns")
    print()
    
    # Display correlations
    print("9. Correlation Analysis:")
    correlations = metrics['correlations']
    if correlations['correlation_analysis_available']:
        print(f"   - Total numeric columns: {correlations['total_numeric_columns']}")
        print(f"   - Significant correlations found: {len(correlations['significant_correlations'])}")
        if correlations['significant_correlations']:
            print(f"   - Top 3 correlations:")
            for corr in correlations['significant_correlations'][:3]:
                print(f"     • {corr['column1']} ↔ {corr['column2']}: {corr['correlation']:.3f} ({corr['strength']}, {corr['direction']})")
    print()
    
    # Display anomalies
    print("10. Anomaly Detection:")
    anomalies = metrics['anomalies']
    if anomalies['anomalies_detected']:
        print(f"    Anomalies detected in {len(anomalies['columns_with_anomalies'])} columns:")
        for col_name, col_anomalies in list(anomalies['details'].items())[:3]:  # Show first 3
            print(f"    - {col_name}: {col_anomalies['total_anomalies']} anomalies ({col_anomalies['anomaly_percentage']:.2f}%)")
            print(f"      Bounds: [{col_anomalies['lower_bound']:.2f}, {col_anomalies['upper_bound']:.2f}]")
    else:
        print("    No anomalies detected")
    print()
    
    # Display charts
    print("11. Visualizations Generated:")
    charts = metrics['charts']
    print(f"    Total charts: {len(charts)}")
    for chart_name in list(charts.keys())[:5]:  # Show first 5 names
        print(f"    - {chart_name} (base64 encoded PNG)")
    print()
    
    # Summary
    print("=" * 80)
    print("Summary:")
    print("=" * 80)
    print(f"✓ Analyzed {overview['total_rows']} rows and {overview['total_columns']} columns")
    print(f"✓ Generated {len(kpis)} KPIs")
    print(f"✓ Analyzed {len(numeric_metrics)} numeric columns")
    print(f"✓ Analyzed {len(categorical_metrics)} categorical columns")
    print(f"✓ Detected {'temporal patterns' if temporal_metrics['temporal_data_detected'] else 'no temporal data'}")
    print(f"✓ Found {len(correlations.get('significant_correlations', []))} significant correlations")
    print(f"✓ Detected anomalies in {len(anomalies.get('columns_with_anomalies', []))} columns")
    print(f"✓ Generated {len(charts)} visualization charts")
    print()
    print("✓ NO RAW DATA in output - only aggregated statistics")
    print("✓ Ready for LLM interpretation via MCP")
    print()
    
    # Optional: Save metrics to JSON
    # Remove charts from JSON export (they're too large)
    metrics_export = {k: v for k, v in metrics.items() if k != 'charts'}
    
    with open('/tmp/eda_metrics_example.json', 'w') as f:
        json.dump(metrics_export, f, indent=2)
    print("Metrics exported to: /tmp/eda_metrics_example.json")
    print(f"Charts saved: {len(charts)} (not included in JSON export due to size)")
    print()


if __name__ == '__main__':
    main()
