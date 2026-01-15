"""
Integration Tests for Complete Pipeline

These tests validate:
1. End-to-end pipeline execution
2. Output quality and structure
3. Data quality scoring
4. Prevention of raw data leakage to LLM
"""

import pytest
import json
import pandas as pd
from pathlib import Path
import tempfile
import shutil

from services.data_quality.validator import DataQualityService
from services.eda.analyzer import EDAService
from services.insight.generator import InsightService
from services.report.builder import ReportBuilder


class TestIntegrationPipeline:
    """Integration tests for the complete analysis pipeline"""
    
    @pytest.fixture
    def temp_output_dir(self):
        """Create a temporary directory for test outputs"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def sample_csv_paths(self):
        """Paths to sample CSV files"""
        examples_dir = Path(__file__).parent.parent / "examples"
        return {
            'sales': examples_dir / "sales_data.csv",
            'financial': examples_dir / "financial_data.csv",
            'messy': examples_dir / "messy_data.csv"
        }
    
    def test_pipeline_with_clean_data(self, sample_csv_paths, temp_output_dir):
        """Test pipeline with high-quality sales data"""
        
        # Step 1: Data Quality
        dq_service = DataQualityService()
        dq_result = dq_service.validate_and_clean(str(sample_csv_paths['sales']))
        
        assert dq_result is not None
        assert 'quality_score' in dq_result
        assert dq_result['quality_score'] >= 70, "Clean data should score >= 70"
        assert 'cleaned_df' in dq_result
        assert len(dq_result['cleaned_df']) > 0
        
        # Step 2: EDA
        eda_service = EDAService()
        eda_result = eda_service.analyze(
            df=dq_result['cleaned_df'],
            output_dir=str(Path(temp_output_dir) / "charts")
        )
        
        assert eda_result is not None
        assert 'summary' in eda_result
        assert 'kpis' in eda_result['summary']
        assert len(eda_result['summary']['kpis']) > 0
        assert 'visualizations' in eda_result
        
        # Step 3: Insights
        insight_service = InsightService()
        llm_context = {
            "data_summary": {
                "filename": "sales_data.csv",
                "row_count": dq_result['cleaned_row_count'],
                "column_count": dq_result['column_count'],
                "columns": dq_result['schema'],
                "quality_score": dq_result['quality_score']
            },
            "metrics": eda_result['summary'],
            "data_types": eda_result.get('column_types', {}),
            "issues": dq_result['issues']
        }
        
        insight_result = insight_service.generate_insights(llm_context)
        
        assert insight_result is not None
        assert 'executive_summary' in insight_result
        assert 'key_insights' in insight_result
        assert 'recommendations' in insight_result
        assert len(insight_result['key_insights']) > 0
        
        # Step 4: Report
        report_builder = ReportBuilder()
        report_result = report_builder.build_report(
            validation_result=dq_result,
            eda_result=eda_result,
            insight_result=insight_result,
            output_dir=temp_output_dir
        )
        
        assert report_result is not None
        assert 'report_path' in report_result
        assert Path(report_result['report_path']).exists()
        
        # Verify report content
        with open(report_result['report_path'], 'r') as f:
            report_content = f.read()
            assert len(report_content) > 1000, "Report should be substantial"
            assert "Data Analysis Report" in report_content
            assert "Quality Score" in report_content
    
    def test_pipeline_with_messy_data(self, sample_csv_paths, temp_output_dir):
        """Test pipeline with low-quality messy data"""
        
        dq_service = DataQualityService()
        dq_result = dq_service.validate_and_clean(str(sample_csv_paths['messy']))
        
        assert dq_result is not None
        assert 'quality_score' in dq_result
        # Messy data should have lower quality score
        assert dq_result['quality_score'] < 80, "Messy data should score < 80"
        
        # Should still have cleaned data
        assert 'cleaned_df' in dq_result
        assert len(dq_result['cleaned_df']) > 0
        
        # Should identify issues
        assert len(dq_result['issues']) > 0, "Should detect data quality issues"
        
        # Should apply transformations
        assert len(dq_result['transformations']) > 0, "Should apply cleaning transformations"
        
        # Should remove duplicates
        assert dq_result['duplicates_removed'] > 0, "Should detect and remove duplicates"
    
    def test_data_quality_scoring(self, sample_csv_paths):
        """Test that data quality scoring is consistent and meaningful"""
        
        dq_service = DataQualityService()
        
        # Clean data should score higher than messy data
        clean_result = dq_service.validate_and_clean(str(sample_csv_paths['sales']))
        messy_result = dq_service.validate_and_clean(str(sample_csv_paths['messy']))
        
        assert clean_result['quality_score'] > messy_result['quality_score'], \
            "Clean data should score higher than messy data"
        
        # Scores should be in valid range
        assert 0 <= clean_result['quality_score'] <= 100
        assert 0 <= messy_result['quality_score'] <= 100
    
    def test_no_raw_data_leakage(self, sample_csv_paths, temp_output_dir):
        """
        CRITICAL TEST: Ensure no raw CSV data reaches the LLM
        
        This test verifies that:
        1. Only aggregated metrics are passed to LLM
        2. No individual row data is exposed
        3. No column values are sent (only column names and types)
        """
        
        # Step 1 & 2: Get metrics
        dq_service = DataQualityService()
        dq_result = dq_service.validate_and_clean(str(sample_csv_paths['sales']))
        
        eda_service = EDAService()
        eda_result = eda_service.analyze(
            df=dq_result['cleaned_df'],
            output_dir=str(Path(temp_output_dir) / "charts")
        )
        
        # Build LLM context
        llm_context = {
            "data_summary": {
                "filename": "sales_data.csv",
                "row_count": dq_result['cleaned_row_count'],
                "column_count": dq_result['column_count'],
                "columns": dq_result['schema'],
                "quality_score": dq_result['quality_score']
            },
            "metrics": eda_result['summary'],
            "data_types": eda_result.get('column_types', {}),
            "issues": dq_result['issues']
        }
        
        # Convert to JSON to check what would be sent to LLM
        llm_payload = json.dumps(llm_context)
        
        # Load original data to check for leakage
        original_df = pd.read_csv(sample_csv_paths['sales'])
        
        # Check that no individual cell values appear in LLM context
        # (except for column names and data types which are metadata)
        potential_leaks = []
        
        # Check for order IDs (specific row identifiers)
        sample_order_ids = original_df['Order ID'].head(10).tolist()
        for order_id in sample_order_ids:
            if str(order_id) in llm_payload:
                potential_leaks.append(f"Order ID leaked: {order_id}")
        
        # Check for specific product names appearing as values
        sample_products = original_df['Product Name'].head(10).tolist()
        for product in sample_products:
            # Product names in schema are OK, but not as data values
            if llm_payload.count(str(product)) > 1:  # More than once suggests data leak
                potential_leaks.append(f"Product name may be leaked: {product}")
        
        # Check that DataFrame is not in context
        assert 'cleaned_df' not in llm_context, "DataFrame should not be in LLM context"
        assert 'original_df' not in llm_context, "Original DataFrame should not be in LLM context"
        
        # Verify only aggregated metrics are present
        assert 'row_count' in llm_context['data_summary'], "Should have row count"
        assert 'column_count' in llm_context['data_summary'], "Should have column count"
        assert 'metrics' in llm_context, "Should have aggregated metrics"
        
        # Verify no pandas DataFrame serialization
        assert 'DataFrame' not in llm_payload, "Should not serialize DataFrames"
        assert 'dtype' not in llm_payload or llm_payload.count('dtype') < 5, \
            "Should not have many dtype references (suggests DataFrame dump)"
        
        # Report findings
        if potential_leaks:
            pytest.fail(f"Potential data leakage detected:\n" + "\n".join(potential_leaks))
        
        print("\n✓ No raw data leakage detected")
        print(f"  LLM context size: {len(llm_payload)} bytes")
        print(f"  Original data rows: {len(original_df)}")
        print(f"  Aggregated metrics: {len(llm_context['metrics'])}")
    
    def test_outputs_are_generated(self, sample_csv_paths, temp_output_dir):
        """Test that all expected outputs are generated"""
        
        dq_service = DataQualityService()
        dq_result = dq_service.validate_and_clean(str(sample_csv_paths['financial']))
        
        eda_service = EDAService()
        chart_dir = Path(temp_output_dir) / "charts"
        eda_result = eda_service.analyze(
            df=dq_result['cleaned_df'],
            output_dir=str(chart_dir)
        )
        
        # Check that charts were generated
        assert chart_dir.exists(), "Chart directory should be created"
        chart_files = list(chart_dir.glob("*.png"))
        assert len(chart_files) > 0, "Should generate at least one chart"
        
        # Check that visualizations are tracked
        assert len(eda_result['visualizations']) > 0
        assert len(eda_result['visualizations']) == len(chart_files)
        
        # Check that all referenced charts exist
        for viz in eda_result['visualizations']:
            viz_path = Path(viz['path'])
            assert viz_path.exists(), f"Chart should exist: {viz_path}"
    
    def test_pipeline_handles_various_data_types(self, sample_csv_paths, temp_output_dir):
        """Test that pipeline handles different data characteristics"""
        
        dq_service = DataQualityService()
        eda_service = EDAService()
        
        # Test with sales data (categorical + numeric)
        sales_dq = dq_service.validate_and_clean(str(sample_csv_paths['sales']))
        sales_eda = eda_service.analyze(
            df=sales_dq['cleaned_df'],
            output_dir=str(Path(temp_output_dir) / "sales_charts")
        )
        
        assert len(sales_eda['summary']['kpis']) > 0
        
        # Test with financial data (time series + numeric)
        financial_dq = dq_service.validate_and_clean(str(sample_csv_paths['financial']))
        financial_eda = eda_service.analyze(
            df=financial_dq['cleaned_df'],
            output_dir=str(Path(temp_output_dir) / "financial_charts")
        )
        
        assert len(financial_eda['summary']['kpis']) > 0
        
        # Both should produce insights
        assert 'numeric_columns' in sales_eda['summary']
        assert 'numeric_columns' in financial_eda['summary']
    
    def test_report_structure(self, sample_csv_paths, temp_output_dir):
        """Test that generated report has proper structure"""
        
        # Run full pipeline
        dq_service = DataQualityService()
        dq_result = dq_service.validate_and_clean(str(sample_csv_paths['sales']))
        
        eda_service = EDAService()
        eda_result = eda_service.analyze(
            df=dq_result['cleaned_df'],
            output_dir=str(Path(temp_output_dir) / "charts")
        )
        
        insight_service = InsightService()
        llm_context = {
            "data_summary": {
                "filename": "sales_data.csv",
                "row_count": dq_result['cleaned_row_count'],
                "column_count": dq_result['column_count'],
                "columns": dq_result['schema'],
                "quality_score": dq_result['quality_score']
            },
            "metrics": eda_result['summary'],
            "data_types": eda_result.get('column_types', {}),
            "issues": dq_result['issues']
        }
        insight_result = insight_service.generate_insights(llm_context)
        
        report_builder = ReportBuilder()
        report_result = report_builder.build_report(
            validation_result=dq_result,
            eda_result=eda_result,
            insight_result=insight_result,
            output_dir=temp_output_dir
        )
        
        # Read and validate report structure
        with open(report_result['report_path'], 'r') as f:
            report = f.read()
        
        # Check for required sections
        required_sections = [
            "# Data Analysis Report",
            "## Executive Summary",
            "## Data Quality Assessment",
            "## Key Insights",
            "## Recommendations",
            "## Data Overview"
        ]
        
        for section in required_sections:
            assert section in report, f"Report should contain section: {section}"
        
        # Check that quality score is mentioned
        assert str(dq_result['quality_score']) in report or \
               f"{dq_result['quality_score']:.0f}" in report, \
               "Report should include quality score"


class TestDataQualityService:
    """Focused tests for data quality service"""
    
    def test_duplicate_detection(self, tmp_path):
        """Test that duplicates are properly detected and removed"""
        
        # Create CSV with known duplicates
        csv_path = tmp_path / "test_duplicates.csv"
        df = pd.DataFrame({
            'id': [1, 2, 3, 2, 4, 3],  # 2 and 3 are duplicated
            'value': ['a', 'b', 'c', 'b', 'd', 'c']
        })
        df.to_csv(csv_path, index=False)
        
        dq_service = DataQualityService()
        result = dq_service.validate_and_clean(str(csv_path))
        
        assert result['duplicates_removed'] == 2
        assert result['cleaned_row_count'] == 4
    
    def test_column_standardization(self, tmp_path):
        """Test that column names are standardized"""
        
        csv_path = tmp_path / "test_columns.csv"
        df = pd.DataFrame({
            'Product Name': [1, 2, 3],
            'Total Revenue': [100, 200, 300],
            'customer_id': [1, 2, 3]
        })
        df.to_csv(csv_path, index=False)
        
        dq_service = DataQualityService()
        result = dq_service.validate_and_clean(str(csv_path))
        
        cleaned_columns = result['cleaned_df'].columns.tolist()
        
        # All should be snake_case
        assert 'product_name' in cleaned_columns
        assert 'total_revenue' in cleaned_columns
        assert 'customer_id' in cleaned_columns


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
