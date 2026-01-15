#!/usr/bin/env python3
"""
End-to-End Analysis Example

This script demonstrates the complete pipeline without using the API.
It shows how all components work together to analyze a CSV file.

Usage:
    python examples/run_analysis.py examples/sales_data.csv
    python examples/run_analysis.py examples/financial_data.csv
    python examples/run_analysis.py examples/messy_data.csv
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.data_quality.validator import DataQualityService
from services.eda.analyzer import EDAService
from services.insight.generator import InsightService
from services.report.builder import ReportBuilder


def print_section(title: str):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def run_pipeline(csv_path: str, output_dir: str = None):
    """
    Run the complete analysis pipeline
    
    Args:
        csv_path: Path to input CSV file
        output_dir: Directory to save outputs (default: storage/jobs/<timestamp>)
    """
    
    # Setup output directory
    if output_dir is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = project_root / "storage" / "jobs" / timestamp
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    csv_path = Path(csv_path)
    if not csv_path.exists():
        print(f"❌ Error: File not found: {csv_path}")
        sys.exit(1)
    
    print_section(f"Starting Analysis: {csv_path.name}")
    print(f"📁 Output directory: {output_dir}")
    
    # ========================================================================
    # STEP 1: Data Quality Validation
    # ========================================================================
    print_section("STEP 1: Data Quality Validation")
    
    dq_service = DataQualityService()
    print(f"📊 Loading and validating: {csv_path}")
    
    dq_result = dq_service.validate_and_clean(str(csv_path))
    
    print(f"\n✓ Data Quality Score: {dq_result['quality_score']:.1f}/100")
    print(f"  - Original rows: {dq_result['row_count']}")
    print(f"  - Columns: {dq_result['column_count']}")
    print(f"  - Cleaned rows: {dq_result['cleaned_row_count']}")
    print(f"  - Removed duplicates: {dq_result['duplicates_removed']}")
    
    if dq_result['transformations']:
        print(f"\n  Transformations applied:")
        for transform in dq_result['transformations']:
            print(f"    • {transform}")
    
    if dq_result['issues']:
        print(f"\n  ⚠️  Issues found:")
        for issue in dq_result['issues']:
            print(f"    • {issue}")
    
    # Save cleaned data and validation report
    cleaned_csv = output_dir / "cleaned_data.csv"
    dq_result['cleaned_df'].to_csv(cleaned_csv, index=False)
    print(f"\n💾 Saved cleaned data: {cleaned_csv}")
    
    validation_json = output_dir / "01_validation.json"
    with open(validation_json, 'w') as f:
        json.dump({
            k: v for k, v in dq_result.items() 
            if k not in ['cleaned_df', 'original_df']
        }, f, indent=2)
    print(f"💾 Saved validation report: {validation_json}")
    
    # Check if we should proceed with analysis
    if dq_result['quality_score'] < 30:
        print("\n⚠️  WARNING: Data quality is very poor (score < 30)")
        print("   Analysis may produce unreliable results.")
        response = input("   Continue anyway? (y/N): ")
        if response.lower() != 'y':
            print("❌ Analysis cancelled.")
            return None
    
    # ========================================================================
    # STEP 2: Exploratory Data Analysis
    # ========================================================================
    print_section("STEP 2: Exploratory Data Analysis")
    
    eda_service = EDAService()
    print(f"📈 Analyzing cleaned data...")
    
    eda_result = eda_service.analyze(
        df=dq_result['cleaned_df'],
        output_dir=str(output_dir / "charts")
    )
    
    print(f"\n✓ EDA Complete")
    print(f"  - KPIs computed: {len(eda_result['summary']['kpis'])}")
    print(f"  - Charts generated: {len(eda_result['visualizations'])}")
    
    # Show key metrics
    if eda_result['summary']['kpis']:
        print(f"\n  Key Performance Indicators:")
        for kpi_name, kpi_value in list(eda_result['summary']['kpis'].items())[:5]:
            print(f"    • {kpi_name}: {kpi_value}")
        if len(eda_result['summary']['kpis']) > 5:
            print(f"    ... and {len(eda_result['summary']['kpis']) - 5} more")
    
    # Save EDA report
    eda_json = output_dir / "02_eda_metrics.json"
    with open(eda_json, 'w') as f:
        # Remove df from result before saving
        eda_output = {k: v for k, v in eda_result.items() if k != 'df'}
        json.dump(eda_output, f, indent=2)
    print(f"\n💾 Saved EDA metrics: {eda_json}")
    print(f"💾 Saved charts: {output_dir / 'charts'}/")
    
    # ========================================================================
    # STEP 3: LLM Insight Generation
    # ========================================================================
    print_section("STEP 3: LLM Insight Generation")
    
    insight_service = InsightService()
    print(f"🤖 Generating business insights...")
    print(f"   (This uses LLM - may take 10-30 seconds)")
    
    # Prepare structured context for LLM (NO RAW DATA)
    llm_context = {
        "data_summary": {
            "filename": csv_path.name,
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
    
    print(f"\n✓ Insights Generated")
    print(f"\n  Executive Summary:")
    summary_lines = insight_result['executive_summary'].split('\n')
    for line in summary_lines[:3]:
        if line.strip():
            print(f"    {line.strip()}")
    
    print(f"\n  Key Insights: {len(insight_result['key_insights'])}")
    for i, insight in enumerate(insight_result['key_insights'][:3], 1):
        print(f"    {i}. {insight[:80]}..." if len(insight) > 80 else f"    {i}. {insight}")
    
    print(f"\n  Recommendations: {len(insight_result['recommendations'])}")
    
    # Save insights
    insights_json = output_dir / "03_insights.json"
    with open(insights_json, 'w') as f:
        json.dump(insight_result, f, indent=2)
    print(f"\n💾 Saved insights: {insights_json}")
    
    # ========================================================================
    # STEP 4: Report Generation
    # ========================================================================
    print_section("STEP 4: Report Generation")
    
    report_builder = ReportBuilder()
    print(f"📄 Building final report...")
    
    report_result = report_builder.build_report(
        validation_result=dq_result,
        eda_result=eda_result,
        insight_result=insight_result,
        output_dir=str(output_dir)
    )
    
    print(f"\n✓ Report Generated")
    print(f"  - Format: Markdown")
    print(f"  - Location: {report_result['report_path']}")
    print(f"  - Size: {Path(report_result['report_path']).stat().st_size / 1024:.1f} KB")
    
    # ========================================================================
    # Summary
    # ========================================================================
    print_section("✅ Pipeline Complete!")
    
    print(f"All outputs saved to: {output_dir}\n")
    print("Generated files:")
    print(f"  1. {cleaned_csv.name} - Cleaned data")
    print(f"  2. {validation_json.name} - Data quality report")
    print(f"  3. {eda_json.name} - EDA metrics")
    print(f"  4. {insights_json.name} - LLM insights")
    print(f"  5. {Path(report_result['report_path']).name} - Final report")
    print(f"  6. charts/ - Visualizations")
    
    print(f"\n📊 Quality Score: {dq_result['quality_score']:.1f}/100")
    print(f"📈 KPIs Analyzed: {len(eda_result['summary']['kpis'])}")
    print(f"💡 Insights: {len(insight_result['key_insights'])}")
    print(f"⚡ Recommendations: {len(insight_result['recommendations'])}")
    
    print(f"\n📖 View the report:")
    print(f"   cat {report_result['report_path']}")
    
    return {
        'output_dir': str(output_dir),
        'quality_score': dq_result['quality_score'],
        'report_path': report_result['report_path'],
        'metrics': eda_result['summary'],
        'insights': insight_result
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python examples/run_analysis.py <csv_file>")
        print("\nExample files:")
        print("  python examples/run_analysis.py examples/sales_data.csv")
        print("  python examples/run_analysis.py examples/financial_data.csv")
        print("  python examples/run_analysis.py examples/messy_data.csv")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        result = run_pipeline(csv_file, output_dir)
        if result:
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
