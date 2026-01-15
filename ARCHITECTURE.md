# Architecture Documentation

## System Overview

The AI CSV Business Insight Generator is a production-grade AI analytics system that follows clean architecture principles and strict separation of concerns.

## Architectural Principles

### 1. Separation of Concerns

**Truth (Python Analytics)**:
- All numerical calculations
- Data transformations
- Statistical analysis
- Deterministic operations

**Reasoning (LLM Interpretation)**:
- Insight generation
- Pattern interpretation
- Recommendation formulation
- Natural language explanations

**Orchestration (n8n Workflow)**:
- Process control flow
- Error handling and retries
- Async job management
- Status tracking

### 2. No Raw Data to LLM

**Critical Security Constraint**:
- LLMs NEVER receive raw CSV data
- LLMs ONLY see aggregated metrics (JSON)
- All calculations done in Python
- MCP schema enforces constraints

**Why This Matters**:
- Data privacy and security
- Prevents hallucination on raw data
- Reproducible calculations
- Audit trail compliance

### 3. MCP (Model Context Protocol)

**Purpose**: Constrain LLM behavior with explicit contracts

**Components**:
```python
{
  "constraints": {
    "use_only_provided_metrics": true,
    "no_calculations": true,
    "no_speculation": true
  },
  "metrics_summary": {...},
  "instructions": [...]
}
```

**Benefits**:
- Predictable LLM behavior
- No hallucinations
- Auditable responses
- Clear responsibility boundaries

## Component Details

### Data Quality Service

**Input**: Raw CSV DataFrame  
**Output**: Cleaned DataFrame + Validation JSON  

**Operations**:
1. Column standardization (snake_case)
2. Non-value replacement (ERROR → NaN)
3. String normalization
4. Smart type casting
5. Duplicate removal
6. Schema inference
7. Quality scoring

**Quality Score Algorithm**:
```python
score = 100.0
score -= min(missing_percentage, 30)  # Completeness
score -= min(duplicate_percentage, 20)  # Uniqueness
score += min(type_casts * 2, 10)  # Type consistency
return max(0, min(100, score))
```

### EDA Service

**Input**: Cleaned DataFrame  
**Output**: Metrics JSON + Charts (base64)  

**Metrics Generated**:
- Dataset overview (shape, types, memory)
- KPIs (totals, averages, growth rates)
- Numeric metrics (distributions, trends)
- Categorical metrics (value counts, diversity)
- Temporal metrics (time series patterns)
- Correlations (significant pairs)
- Anomalies (IQR-based outliers)

**Chart Types**:
- Distribution plots (histogram + boxplot)
- Bar charts (top categories)
- Time series plots (trend lines)
- Correlation heatmaps

### Insight Service

**Input**: Metrics JSON  
**Output**: Structured Insights JSON  

**LLM Provider Abstraction**:
```python
class LLMProvider:
    def generate(prompt: str) -> (response, metadata)

class OpenAIProvider(LLMProvider):
    # OpenAI implementation

class AnthropicProvider(LLMProvider):
    # Anthropic implementation
```

**Insight Structure**:
- Executive summary (2-3 sentences)
- Key insights (3-5 with evidence)
- Risks and caveats (data quality issues)
- Actionable recommendations (prioritized)

### Report Builder

**Input**: Data quality + Metrics + Insights + Charts  
**Output**: Markdown report  

**Report Sections**:
1. Header (metadata)
2. Executive summary
3. Data quality assessment
4. Key insights
5. Dataset overview
6. KPIs
7. Visualizations
8. Detailed metrics
9. Risks and caveats
10. Recommendations
11. Footer (audit trail)

### Storage Manager

**Persistence Layer**:
- SQLite for metadata
- File system for data/reports/charts
- Audit log for all operations

**Database Models**:
- `JobMetadata`: Job tracking
- `AuditLog`: Operation history with LLM tracking

## Data Flow

```
1. CSV Upload
   ↓
2. Create Job (UUID, metadata)
   ↓
3. Data Quality Service
   - Clean and validate
   - Calculate quality score
   ↓
4. EDA Service
   - Compute metrics
   - Generate charts
   ↓
5. Insight Service
   - Build MCP context
   - Call LLM
   - Parse response
   ↓
6. Report Builder
   - Combine components
   - Generate Markdown
   ↓
7. Storage
   - Save report
   - Update job status
   - Log operations
```

## Error Handling Strategy

### Service-Level Errors

**Data Quality Service**:
- Invalid CSV format → ValidationError
- File too large → FileSizeError
- Unreadable encoding → EncodingError

**EDA Service**:
- No numeric columns → Generate limited metrics
- Chart generation failure → Continue without charts
- Insufficient data → Warning in report

**Insight Service**:
- LLM API failure → Use fallback insights
- Invalid response → Retry with adjusted prompt
- Timeout → Generate basic summary

**Report Builder**:
- Missing sections → Skip gracefully
- Chart embedding failure → Use text description

### API-Level Errors

**HTTP Status Codes**:
- 200: Success
- 400: Invalid request
- 404: Job not found
- 422: Validation error
- 500: Internal error
- 503: Service unavailable

## Scalability Considerations

### Current Architecture (Single Instance)

**Capacity**:
- ~10-20 concurrent uploads
- ~100-500 jobs per day
- < 100K rows per CSV

**Bottlenecks**:
- LLM API rate limits
- Single process for analysis
- Local file storage

### Scaling Strategies

**Horizontal Scaling**:
- Multiple API instances (load balanced)
- Distributed task queue (Celery + Redis)
- Object storage (S3/GCS)
- Managed database (PostgreSQL)

**Vertical Scaling**:
- Increase compute resources
- Add caching layer (Redis)
- Database connection pooling

**Future Architecture** (High Scale):
```
Load Balancer
    ↓
Multiple FastAPI Instances
    ↓
Message Queue (RabbitMQ/Redis)
    ↓
Worker Pool (Celery)
    ↓
Object Storage + PostgreSQL
```

## Security Architecture

### Input Validation

- File type whitelist (CSV only)
- File size limits (configurable)
- Content inspection (malware scan)
- Rate limiting per IP/user

### Data Privacy

- No raw data to LLM
- Aggregated metrics only
- PII detection and masking (future)
- Encrypted storage (future)

### API Security

- API key authentication
- CORS configuration
- Request signing (future)
- Audit logging

### LLM Security

- MCP constraints
- Response validation
- Prompt injection prevention
- Token budget limits

## Monitoring and Observability

### Metrics to Track

**System Metrics**:
- Request rate
- Error rate
- Response time (p50, p95, p99)
- Queue depth

**Business Metrics**:
- Jobs created
- Jobs completed
- Average data quality score
- LLM token usage
- Cost per analysis

**Quality Metrics**:
- Report generation success rate
- Chart generation success rate
- LLM response quality

### Logging Strategy

**Log Levels**:
- DEBUG: Detailed execution flow
- INFO: Normal operations
- WARNING: Recoverable errors
- ERROR: Failures requiring attention
- CRITICAL: System-level failures

**Structured Logging**:
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "service": "eda_service",
  "job_id": "abc-123",
  "operation": "generate_metrics",
  "execution_time_ms": 1250,
  "status": "success"
}
```

### Audit Trail

**Tracked Information**:
- All API requests
- Job lifecycle events
- LLM prompts and responses
- Error occurrences
- Performance metrics

## Deployment Architectures

### Development (Local)

```
Docker Compose:
- FastAPI container
- n8n container
- Shared volumes
```

### Production (GCP)

```
- Cloud Run (FastAPI)
- Cloud SQL (PostgreSQL)
- Cloud Storage (files)
- Cloud Tasks (job queue)
- Cloud Logging + Monitoring
```

### Production (AWS)

```
- ECS Fargate (FastAPI)
- RDS (PostgreSQL)
- S3 (files)
- SQS + Lambda (job queue)
- CloudWatch (monitoring)
```

## Testing Strategy

### Unit Tests

- Service logic
- Data transformations
- Validation rules
- MCP schema

### Integration Tests

- Complete pipeline
- API endpoints
- Storage operations
- LLM interactions (mocked)

### Critical Tests

- **No raw data leakage**: Ensures LLM safety
- Data quality scoring accuracy
- Report completeness
- Error handling

### Performance Tests

- Load testing (concurrent requests)
- Stress testing (large CSVs)
- Endurance testing (long-running)

## Future Enhancements

### Short Term (v0.2)

- [ ] Streamlit UI
- [ ] PDF export
- [ ] Email notifications
- [ ] Scheduled reports

### Medium Term (v0.3)

- [ ] Multi-file analysis
- [ ] Custom KPI definitions
- [ ] Report templates
- [ ] Data versioning

### Long Term (v1.0)

- [ ] Real-time dashboards
- [ ] Predictive analytics
- [ ] Multi-tenant SaaS
- [ ] API marketplace

## References

- [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/)
- [n8n Documentation](https://docs.n8n.io/)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [Pandas Best Practices](https://pandas.pydata.org/docs/user_guide/)
