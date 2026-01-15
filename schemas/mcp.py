"""MCP (Model Context Protocol) schema definitions for LLM interactions.

This module defines strict contracts that constrain LLM behavior to ensure:
- LLMs never see raw CSV data
- LLMs only interpret provided metrics
- LLMs do not perform calculations
- LLMs do not make unsupported inferences
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class MCPConstraints(BaseModel):
    """Explicit constraints for LLM behavior."""
    use_only_provided_metrics: bool = True
    no_calculations: bool = True
    no_raw_data_inference: bool = True
    no_speculation: bool = True
    no_assumptions_beyond_context: bool = True
    cite_specific_metrics: bool = True


class MCPBusinessContext(BaseModel):
    """Business context for the analysis."""
    domain: Optional[str] = Field(None, description="Business domain (e.g., 'sales', 'finance', 'operations')")
    analysis_purpose: Optional[str] = Field(None, description="Purpose of the analysis")
    time_period: Optional[str] = Field(None, description="Time period covered by the data")
    key_entities: Optional[List[str]] = Field(default_factory=list, description="Key entities in the data")


class MCPMetricsSummary(BaseModel):
    """Summary of provided metrics for LLM consumption."""
    dataset_overview: Dict[str, Any] = Field(..., description="Dataset size, types, quality score")
    kpis: Dict[str, Any] = Field(default_factory=dict, description="Key performance indicators")
    numeric_metrics: Dict[str, Any] = Field(default_factory=dict, description="Statistical summaries")
    categorical_metrics: Dict[str, Any] = Field(default_factory=dict, description="Category distributions")
    temporal_metrics: Dict[str, Any] = Field(default_factory=dict, description="Time-based patterns")
    correlations: List[Dict[str, Any]] = Field(default_factory=list, description="Significant correlations")
    anomalies: Dict[str, Any] = Field(default_factory=dict, description="Detected anomalies")
    trends: Dict[str, Any] = Field(default_factory=dict, description="Detected trends")


class MCPPromptContext(BaseModel):
    """Complete context for LLM prompt."""
    constraints: MCPConstraints = Field(default_factory=MCPConstraints)
    business_context: MCPBusinessContext = Field(default_factory=MCPBusinessContext)
    metrics_summary: MCPMetricsSummary
    instructions: List[str] = Field(
        default_factory=lambda: [
            "Analyze ONLY the provided metrics",
            "Do not perform any calculations",
            "Do not infer causes without evidence",
            "Cite specific metrics when making observations",
            "Acknowledge data limitations and quality issues",
            "Provide actionable recommendations based on patterns"
        ]
    )


class InsightSection(BaseModel):
    """A single insight with supporting evidence."""
    title: str = Field(..., description="Brief insight title")
    description: str = Field(..., description="Detailed explanation")
    supporting_metrics: List[str] = Field(..., description="Specific metrics that support this insight")
    confidence: str = Field(..., description="Confidence level: high, medium, low")


class RiskCaveat(BaseModel):
    """A risk or caveat about the data or analysis."""
    concern: str = Field(..., description="The specific concern")
    impact: str = Field(..., description="Potential impact on interpretation")
    recommendation: str = Field(..., description="How to address this concern")


class ActionableRecommendation(BaseModel):
    """A specific, actionable recommendation."""
    action: str = Field(..., description="The recommended action")
    rationale: str = Field(..., description="Why this action is recommended")
    priority: str = Field(..., description="Priority level: high, medium, low")
    expected_impact: str = Field(..., description="Expected impact of taking this action")


class MCPInsightOutput(BaseModel):
    """Structured output from LLM insight generation."""
    executive_summary: str = Field(..., description="High-level summary (2-3 sentences)")
    key_insights: List[InsightSection] = Field(..., description="3-5 key insights with evidence")
    risks_and_caveats: List[RiskCaveat] = Field(..., description="Data quality and interpretation caveats")
    actionable_recommendations: List[ActionableRecommendation] = Field(..., description="Specific actions")
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# Example MCP Payload for documentation
EXAMPLE_MCP_PAYLOAD = {
    "constraints": {
        "use_only_provided_metrics": True,
        "no_calculations": True,
        "no_raw_data_inference": True,
        "no_speculation": True,
        "no_assumptions_beyond_context": True,
        "cite_specific_metrics": True
    },
    "business_context": {
        "domain": "e-commerce",
        "analysis_purpose": "monthly sales performance review",
        "time_period": "January 2024",
        "key_entities": ["orders", "revenue", "customers"]
    },
    "metrics_summary": {
        "dataset_overview": {
            "total_rows": 1250,
            "total_columns": 8,
            "data_quality_score": 92.5,
            "missing_percentage": 2.1
        },
        "kpis": {
            "total_revenue": 125000.50,
            "average_order_value": 100.00,
            "total_orders": 1250,
            "unique_customers": 850
        },
        "trends": {
            "revenue": {
                "direction": "increasing",
                "strength": "strong",
                "slope": 1250.5,
                "r_squared": 0.89
            }
        },
        "anomalies": {
            "order_amount": {
                "upper_outliers": 15,
                "anomaly_percentage": 1.2
            }
        }
    }
}

# Example Expected LLM Response
EXAMPLE_LLM_RESPONSE = {
    "executive_summary": "Analysis of 1,250 orders shows strong revenue growth with 92.5% data quality. The dataset reveals positive trends and manageable outliers, with actionable opportunities for customer retention.",
    "key_insights": [
        {
            "title": "Strong Revenue Growth Trajectory",
            "description": "Revenue shows a strong increasing trend with r²=0.89, indicating consistent growth throughout the period.",
            "supporting_metrics": ["trends.revenue.direction: increasing", "trends.revenue.r_squared: 0.89"],
            "confidence": "high"
        },
        {
            "title": "Healthy Average Order Value",
            "description": "Average order value of $100 suggests effective upselling or premium product mix.",
            "supporting_metrics": ["kpis.average_order_value: 100.00"],
            "confidence": "high"
        },
        {
            "title": "High Customer Retention Potential",
            "description": "With 850 unique customers from 1,250 orders, there's evidence of repeat purchases (average 1.47 orders per customer).",
            "supporting_metrics": ["kpis.unique_customers: 850", "kpis.total_orders: 1250"],
            "confidence": "medium"
        }
    ],
    "risks_and_caveats": [
        {
            "concern": "Outlier Orders Present",
            "impact": "15 orders (1.2%) are statistical outliers, which may skew average metrics",
            "recommendation": "Review high-value orders separately for accuracy and investigate patterns"
        },
        {
            "concern": "Minor Data Incompleteness",
            "impact": "2.1% missing values may affect some calculations",
            "recommendation": "Ensure critical fields have complete data in future reporting"
        }
    ],
    "actionable_recommendations": [
        {
            "action": "Implement customer retention program targeting one-time buyers",
            "rationale": "With 1.47 orders per customer average, there's room to increase repeat purchase rate",
            "priority": "high",
            "expected_impact": "Increase customer lifetime value by 20-30%"
        },
        {
            "action": "Investigate outlier orders for fraud or data quality issues",
            "rationale": "15 outlier orders represent potential data quality or business process issues",
            "priority": "medium",
            "expected_impact": "Improve data quality and prevent revenue leakage"
        }
    ]
}


def build_mcp_context(
    metrics: Dict[str, Any],
    business_context: Optional[Dict[str, str]] = None
) -> MCPPromptContext:
    """
    Build MCP context from EDA metrics.
    
    Args:
        metrics: Output from EDAMetricsGenerator
        business_context: Optional business context
        
    Returns:
        MCPPromptContext ready for LLM
    """
    # Extract relevant metrics sections
    metrics_summary = MCPMetricsSummary(
        dataset_overview=metrics.get("dataset_overview", {}),
        kpis=metrics.get("kpis", {}),
        numeric_metrics=metrics.get("numeric_metrics", {}),
        categorical_metrics=metrics.get("categorical_metrics", {}),
        temporal_metrics=metrics.get("temporal_metrics", {}),
        correlations=metrics.get("correlations", []),
        anomalies=metrics.get("anomalies", {}),
        trends=metrics.get("trends", {})
    )
    
    # Build business context
    biz_context = MCPBusinessContext(**(business_context or {}))
    
    return MCPPromptContext(
        metrics_summary=metrics_summary,
        business_context=biz_context
    )


def format_mcp_prompt(context: MCPPromptContext) -> str:
    """
    Format MCP context into LLM prompt.
    
    Args:
        context: MCP prompt context
        
    Returns:
        Formatted prompt string
    """
    import json
    
    prompt = f"""You are a data analyst AI assistant. Your role is to interpret provided metrics and generate business insights.

STRICT CONSTRAINTS:
{json.dumps(context.constraints.model_dump(), indent=2)}

BUSINESS CONTEXT:
{json.dumps(context.business_context.model_dump(), indent=2)}

PROVIDED METRICS:
{json.dumps(context.metrics_summary.model_dump(), indent=2, default=str)}

INSTRUCTIONS:
"""
    for instruction in context.instructions:
        prompt += f"- {instruction}\n"
    
    prompt += """
OUTPUT FORMAT:
Provide your analysis as a JSON object with the following structure:
{
  "executive_summary": "2-3 sentence high-level summary",
  "key_insights": [
    {
      "title": "Insight title",
      "description": "Detailed explanation",
      "supporting_metrics": ["metric1", "metric2"],
      "confidence": "high|medium|low"
    }
  ],
  "risks_and_caveats": [
    {
      "concern": "Specific concern",
      "impact": "Impact on interpretation",
      "recommendation": "How to address"
    }
  ],
  "actionable_recommendations": [
    {
      "action": "Specific action",
      "rationale": "Why recommended",
      "priority": "high|medium|low",
      "expected_impact": "Expected outcome"
    }
  ]
}

Begin your analysis:"""
    
    return prompt
