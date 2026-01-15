"""Report builder for combining insights and charts into Markdown reports."""
import base64
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class ReportBuilder:
    """
    Builds comprehensive Markdown reports from insights and charts.
    
    Responsibilities:
    - Combine LLM insights with EDA metrics
    - Embed charts as images
    - Create PDF-ready Markdown structure
    - Include metadata and audit trail
    """
    
    def __init__(self):
        logger.info("ReportBuilder initialized")
    
    def build_report(
        self,
        job_id: str,
        filename: str,
        data_quality: Dict[str, Any],
        eda_metrics: Dict[str, Any],
        insights: Dict[str, Any],
        charts: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Build comprehensive Markdown report.
        
        Args:
            job_id: Job identifier
            filename: Original filename
            data_quality: Data quality validation results
            eda_metrics: EDA metrics
            insights: LLM-generated insights
            charts: Dict of chart_name -> base64_image
            
        Returns:
            Markdown report string
        """
        logger.info(f"Building report for job {job_id}")
        
        report_parts = []
        
        # Header
        report_parts.append(self._build_header(job_id, filename))
        
        # Executive Summary
        report_parts.append(self._build_executive_summary(insights))
        
        # Data Quality Section
        report_parts.append(self._build_data_quality_section(data_quality))
        
        # Key Insights
        report_parts.append(self._build_key_insights_section(insights))
        
        # Dataset Overview
        report_parts.append(self._build_dataset_overview(eda_metrics))
        
        # KPIs
        if "kpis" in eda_metrics and eda_metrics["kpis"]:
            report_parts.append(self._build_kpis_section(eda_metrics["kpis"]))
        
        # Visualizations
        if charts:
            report_parts.append(self._build_visualizations_section(charts))
        
        # Detailed Metrics
        report_parts.append(self._build_detailed_metrics_section(eda_metrics))
        
        # Risks and Caveats
        report_parts.append(self._build_risks_section(insights))
        
        # Recommendations
        report_parts.append(self._build_recommendations_section(insights))
        
        # Footer
        report_parts.append(self._build_footer(data_quality, eda_metrics, insights))
        
        report = "\n\n".join(report_parts)
        
        logger.info(f"Report built successfully ({len(report)} characters)")
        
        return report
    
    def _build_header(self, job_id: str, filename: str) -> str:
        """Build report header."""
        return f"""# Data Analysis Report

**File**: {filename}  
**Job ID**: `{job_id}`  
**Generated**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC  

---
"""
    
    def _build_executive_summary(self, insights: Dict[str, Any]) -> str:
        """Build executive summary section."""
        summary = insights.get("insights", {}).get("executive_summary", "No executive summary available.")
        
        return f"""## Executive Summary

{summary}
"""
    
    def _build_data_quality_section(self, data_quality: Dict[str, Any]) -> str:
        """Build data quality section."""
        score = data_quality.get("data_quality_score", 0)
        original_shape = data_quality.get("original_shape", {})
        final_shape = data_quality.get("final_shape", {})
        missing = data_quality.get("missing_values", {})
        
        # Score interpretation
        if score >= 90:
            quality_label = "Excellent"
            quality_emoji = "🟢"
        elif score >= 75:
            quality_label = "Good"
            quality_emoji = "🟡"
        elif score >= 60:
            quality_label = "Fair"
            quality_emoji = "🟠"
        else:
            quality_label = "Poor"
            quality_emoji = "🔴"
        
        section = f"""## Data Quality Assessment

**Overall Score**: {score:.1f}/100 {quality_emoji} ({quality_label})

### Dataset Transformation
- **Original**: {original_shape.get('rows', 0):,} rows × {original_shape.get('columns', 0)} columns
- **Final**: {final_shape.get('rows', 0):,} rows × {final_shape.get('columns', 0)} columns
- **Missing Values**: {missing.get('missing_percentage', 0):.2f}%
"""
        
        # Operations performed
        operations = data_quality.get("operations_performed", [])
        if operations:
            section += "\n### Cleaning Operations\n"
            for op in operations:
                op_name = op.get("operation", "Unknown")
                if op_name == "column_standardization":
                    count = len(op.get("column_mapping", {}))
                    section += f"- ✓ Standardized {count} column names to snake_case\n"
                elif op_name == "non_value_replacement":
                    count = sum(op.get("non_values_replaced", {}).values())
                    section += f"- ✓ Replaced {count} non-values with NaN\n"
                elif op_name == "duplicate_removal":
                    count = op.get("duplicates_removed", {}).get("duplicates_removed", 0)
                    section += f"- ✓ Removed {count} duplicate rows\n"
                elif op_name == "type_casting":
                    count = len(op.get("type_changes", {}))
                    section += f"- ✓ Cast {count} columns to appropriate types\n"
        
        return section
    
    def _build_key_insights_section(self, insights: Dict[str, Any]) -> str:
        """Build key insights section."""
        key_insights = insights.get("insights", {}).get("key_insights", [])
        
        if not key_insights:
            return "## Key Insights\n\nNo insights generated."
        
        section = "## Key Insights\n"
        
        for i, insight in enumerate(key_insights, 1):
            title = insight.get("title", f"Insight {i}")
            description = insight.get("description", "")
            confidence = insight.get("confidence", "medium")
            supporting = insight.get("supporting_metrics", [])
            
            # Confidence emoji
            conf_emoji = {"high": "🔵", "medium": "🟡", "low": "⚪"}.get(confidence, "⚪")
            
            section += f"\n### {i}. {title} {conf_emoji}\n\n"
            section += f"{description}\n\n"
            
            if supporting:
                section += "**Supporting Metrics:**\n"
                for metric in supporting:
                    section += f"- `{metric}`\n"
        
        return section
    
    def _build_dataset_overview(self, eda_metrics: Dict[str, Any]) -> str:
        """Build dataset overview section."""
        overview = eda_metrics.get("dataset_overview", {})
        
        return f"""## Dataset Overview

| Metric | Value |
|--------|-------|
| Total Rows | {overview.get('total_rows', 0):,} |
| Total Columns | {overview.get('total_columns', 0)} |
| Numeric Columns | {overview.get('numeric_columns', 0)} |
| Categorical Columns | {overview.get('categorical_columns', 0)} |
| Datetime Columns | {overview.get('datetime_columns', 0)} |
| Memory Usage | {overview.get('memory_usage_mb', 0):.2f} MB |
"""
    
    def _build_kpis_section(self, kpis: Dict[str, Any]) -> str:
        """Build KPIs section."""
        section = "## Key Performance Indicators\n\n"
        
        # Group KPIs by category
        totals = {k: v for k, v in kpis.items() if k.startswith("total_")}
        averages = {k: v for k, v in kpis.items() if k.startswith("avg_") or k.startswith("average_")}
        growth = {k: v for k, v in kpis.items() if "growth" in k.lower() or "rate" in k.lower()}
        other = {k: v for k, v in kpis.items() if k not in totals and k not in averages and k not in growth}
        
        if totals:
            section += "### Totals\n"
            for key, value in totals.items():
                label = key.replace("total_", "").replace("_", " ").title()
                section += f"- **{label}**: {self._format_value(value)}\n"
            section += "\n"
        
        if averages:
            section += "### Averages\n"
            for key, value in averages.items():
                label = key.replace("avg_", "").replace("average_", "").replace("_", " ").title()
                section += f"- **{label}**: {self._format_value(value)}\n"
            section += "\n"
        
        if growth:
            section += "### Growth Metrics\n"
            for key, value in growth.items():
                label = key.replace("_", " ").title()
                section += f"- **{label}**: {self._format_value(value)}\n"
            section += "\n"
        
        if other:
            section += "### Other Metrics\n"
            for key, value in other.items():
                label = key.replace("_", " ").title()
                section += f"- **{label}**: {self._format_value(value)}\n"
        
        return section
    
    def _build_visualizations_section(self, charts: Dict[str, str]) -> str:
        """Build visualizations section."""
        section = "## Visualizations\n\n"
        
        for chart_name, chart_b64 in charts.items():
            chart_title = chart_name.replace("_", " ").title()
            section += f"### {chart_title}\n\n"
            section += f"![{chart_title}](data:image/png;base64,{chart_b64})\n\n"
        
        return section
    
    def _build_detailed_metrics_section(self, eda_metrics: Dict[str, Any]) -> str:
        """Build detailed metrics section."""
        section = "## Detailed Metrics\n\n"
        
        # Trends
        trends = eda_metrics.get("trends", {})
        if trends:
            section += "### Trends\n\n"
            for col, trend in trends.items():
                direction = trend.get("direction", "unknown")
                strength = trend.get("strength", "unknown")
                r_squared = trend.get("r_squared", 0)
                
                emoji = {"increasing": "📈", "decreasing": "📉", "flat": "➡️"}.get(direction, "❓")
                
                section += f"**{col}** {emoji}\n"
                section += f"- Direction: {direction.capitalize()}\n"
                section += f"- Strength: {strength.capitalize()}\n"
                section += f"- R²: {r_squared:.3f}\n\n"
        
        # Anomalies
        anomalies = eda_metrics.get("anomalies", {})
        if anomalies:
            section += "### Anomalies Detected\n\n"
            for col, anom in anomalies.items():
                upper = anom.get("upper_outliers", 0)
                lower = anom.get("lower_outliers", 0)
                pct = anom.get("anomaly_percentage", 0)
                
                if upper + lower > 0:
                    section += f"**{col}**: {upper + lower} outliers ({pct:.2f}%)\n"
                    if upper > 0:
                        section += f"  - Upper: {upper}\n"
                    if lower > 0:
                        section += f"  - Lower: {lower}\n"
            section += "\n"
        
        # Correlations
        correlations = eda_metrics.get("correlations", [])
        if correlations:
            section += "### Significant Correlations\n\n"
            for corr in correlations[:10]:  # Top 10
                col1 = corr.get("column1", "")
                col2 = corr.get("column2", "")
                value = corr.get("correlation", 0)
                strength = corr.get("strength", "")
                
                section += f"- **{col1}** ↔ **{col2}**: {value:.3f} ({strength})\n"
            section += "\n"
        
        return section
    
    def _build_risks_section(self, insights: Dict[str, Any]) -> str:
        """Build risks and caveats section."""
        risks = insights.get("insights", {}).get("risks_and_caveats", [])
        
        if not risks:
            return "## Risks and Caveats\n\nNo significant risks identified."
        
        section = "## Risks and Caveats\n\n"
        
        for i, risk in enumerate(risks, 1):
            concern = risk.get("concern", "")
            impact = risk.get("impact", "")
            recommendation = risk.get("recommendation", "")
            
            section += f"### {i}. {concern}\n\n"
            section += f"**Impact**: {impact}\n\n"
            section += f"**Recommendation**: {recommendation}\n\n"
        
        return section
    
    def _build_recommendations_section(self, insights: Dict[str, Any]) -> str:
        """Build recommendations section."""
        recommendations = insights.get("insights", {}).get("actionable_recommendations", [])
        
        if not recommendations:
            return "## Recommendations\n\nNo recommendations available."
        
        section = "## Actionable Recommendations\n\n"
        
        # Sort by priority
        priority_order = {"high": 1, "medium": 2, "low": 3}
        sorted_recs = sorted(
            recommendations,
            key=lambda x: priority_order.get(x.get("priority", "medium"), 2)
        )
        
        for i, rec in enumerate(sorted_recs, 1):
            action = rec.get("action", "")
            rationale = rec.get("rationale", "")
            priority = rec.get("priority", "medium")
            impact = rec.get("expected_impact", "")
            
            # Priority emoji
            priority_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(priority, "🟡")
            
            section += f"### {i}. {action} {priority_emoji}\n\n"
            section += f"**Priority**: {priority.upper()}\n\n"
            section += f"**Rationale**: {rationale}\n\n"
            section += f"**Expected Impact**: {impact}\n\n"
        
        return section
    
    def _build_footer(
        self,
        data_quality: Dict[str, Any],
        eda_metrics: Dict[str, Any],
        insights: Dict[str, Any]
    ) -> str:
        """Build report footer with metadata."""
        llm_meta = insights.get("llm_metadata", {})
        
        return f"""---

## Report Metadata

**Generation Details:**
- Data Quality Score: {data_quality.get('data_quality_score', 0):.1f}/100
- Metrics Timestamp: {eda_metrics.get('timestamp', 'N/A')}
- Insights Generated: {insights.get('generated_at', 'N/A')}
- LLM Provider: {llm_meta.get('provider', 'N/A')}
- LLM Model: {llm_meta.get('model', 'N/A')}
- Tokens Used: {llm_meta.get('tokens_used', 'N/A')}

**System:**
- AI CSV → Business Insight Generator
- Production-grade AI analytics system
- MCP-constrained LLM interpretation

---

*This report was generated automatically using deterministic Python analytics combined with LLM-powered interpretation. All numerical calculations are performed by Python; the LLM only interprets provided metrics.*
"""
    
    def _format_value(self, value: Any) -> str:
        """Format a value for display."""
        if isinstance(value, float):
            if abs(value) >= 1000:
                return f"{value:,.2f}"
            else:
                return f"{value:.2f}"
        elif isinstance(value, int):
            return f"{value:,}"
        else:
            return str(value)
