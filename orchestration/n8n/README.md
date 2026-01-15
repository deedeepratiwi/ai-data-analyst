# n8n Orchestration for AI CSV Business Insight Generator

## Overview

This directory contains n8n workflow configurations for orchestrating the AI CSV analysis pipeline. The workflow provides:

- **Asynchronous Processing**: Handles long-running analysis jobs
- **Error Handling**: Retry logic and graceful failure recovery
- **Branching Logic**: Different paths for good vs poor data quality
- **Observability**: Status updates and logging at each stage
- **Scalability**: Can be deployed on n8n cloud or self-hosted

## Why n8n for Orchestration?

**Separation of Concerns**:
- Business logic stays in Python services
- Workflow control is visual and configurable
- Non-technical stakeholders can understand the process
- Easy to modify workflow without code changes

**Production Benefits**:
- Built-in error handling and retries
- Webhook triggers for async processing
- Monitoring and alerting capabilities
- No custom orchestration code to maintain

**Scalability**:
- Can run on n8n cloud (managed service)
- Self-hostable with Docker
- Integrates with other tools (Slack, email, etc.)

## Workflow Architecture

```
┌─────────────────┐
│  CSV Upload     │
│  (Webhook)      │
└────────┬────────┘
         │
         v
┌─────────────────┐
│ Create Job      │
│ (HTTP Request)  │
└────────┬────────┘
         │
         v
┌─────────────────┐
│ Start Process   │
│ (HTTP Request)  │
└────────┬────────┘
         │
         v
┌─────────────────┐
│ Poll Status     │
│ (Loop + Delay)  │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    v         v
┌───────┐ ┌───────┐
│Success│ │Failure│
└───┬───┘ └───┬───┘
    │         │
    v         v
┌─────────────────┐
│ Send Report or  │
│ Error Notification│
└─────────────────┘
```

## Workflow Nodes

### 1. Webhook Trigger Node
**Purpose**: Receive CSV upload events  
**Configuration**:
- Method: POST
- Path: /webhook/csv-upload
- Authentication: API Key

**Input**: 
```json
{
  "filename": "sales_data.csv",
  "file_url": "https://storage/uploads/abc123.csv",
  "callback_url": "https://api/notifications/report-ready"
}
```

### 2. Create Job Node
**Purpose**: Call API to create job entry  
**Type**: HTTP Request  
**Configuration**:
- URL: `{{$env.API_BASE_URL}}/upload`
- Method: POST
- Body: Multipart form-data with CSV file

**Output**: `{ "job_id": "abc-123", "status": "pending" }`

### 3. Start Processing Node
**Purpose**: Trigger analysis pipeline  
**Type**: HTTP Request  
**Configuration**:
- URL: `{{$env.API_BASE_URL}}/process/{{$json.job_id}}`
- Method: POST
- Retry on Failure: 3 attempts with exponential backoff

### 4. Poll Job Status Node
**Purpose**: Check processing status  
**Type**: Loop with HTTP Request  
**Configuration**:
- URL: `{{$env.API_BASE_URL}}/job/{{$json.job_id}}`
- Method: GET
- Loop until: `status === "completed" OR status === "failed"`
- Delay: 5 seconds between polls
- Max iterations: 120 (10 minutes timeout)

### 5. Quality Check Branch
**Purpose**: Route based on data quality  
**Type**: IF Node  
**Condition**: `data_quality_score >= 70`

**True Path**: Full report generation  
**False Path**: Limited report with warnings

### 6. Retry Logic Node
**Purpose**: Retry failed operations  
**Type**: Error Trigger + Switch  
**Configuration**:
- Max retries: 3
- Backoff: Exponential (2, 4, 8 seconds)
- Skip retry on: ValidationError, InvalidFileFormat

### 7. Success Notification Node
**Purpose**: Send report or webhook callback  
**Type**: HTTP Request or Email  
**Configuration**:
- POST to callback_url with report_url
- Or send email with report attached

### 8. Failure Notification Node
**Purpose**: Alert on pipeline failure  
**Type**: HTTP Request or Slack  
**Configuration**:
- Send error details
- Include job_id for debugging
- Tag appropriate team

## Data Flow

### Input to n8n:
```json
{
  "trigger": "csv_upload",
  "filename": "Q4_sales.csv",
  "file_path": "/uploads/xyz.csv",
  "user_id": "user@example.com",
  "business_context": {
    "domain": "sales",
    "analysis_purpose": "quarterly review"
  }
}
```

### Output from n8n:
```json
{
  "job_id": "abc-123",
  "status": "completed",
  "report_url": "/reports/abc-123_report.md",
  "data_quality_score": 92.5,
  "processing_time_ms": 15420,
  "generated_at": "2024-01-15T10:30:00Z"
}
```

## Error Handling Strategy

### Transient Errors (Retry)
- Network timeouts
- Service temporarily unavailable
- Rate limiting

**Action**: Exponential backoff retry (3 attempts)

### Permanent Errors (Fail Fast)
- Invalid file format
- Corrupt CSV data
- Missing API credentials

**Action**: Immediate failure with notification

### Partial Success (Continue with Warnings)
- LLM service unavailable
- Some charts failed to generate
- Low data quality score

**Action**: Generate limited report, notify user of limitations

## Workflow JSON Configuration

See `workflow.json` for the complete n8n workflow definition.

## Deployment Instructions

### Option 1: n8n Cloud
1. Sign up at https://n8n.io
2. Import `workflow.json`
3. Set environment variables:
   - `API_BASE_URL`: Your FastAPI endpoint
   - `API_KEY`: Authentication key
4. Activate workflow

### Option 2: Self-Hosted Docker
```bash
# Start n8n
docker run -d \
  --name n8n \
  -p 5678:5678 \
  -e N8N_BASIC_AUTH_ACTIVE=true \
  -e N8N_BASIC_AUTH_USER=admin \
  -e N8N_BASIC_AUTH_PASSWORD=yourpassword \
  -v ~/.n8n:/home/node/.n8n \
  n8nio/n8n

# Import workflow
# 1. Access http://localhost:5678
# 2. Import workflow.json from n8n UI
# 3. Configure credentials
# 4. Activate workflow
```

### Option 3: Kubernetes
```yaml
# See kubernetes/n8n-deployment.yaml for full configuration
apiVersion: apps/v1
kind: Deployment
metadata:
  name: n8n
spec:
  replicas: 2
  selector:
    matchLabels:
      app: n8n
  template:
    spec:
      containers:
      - name: n8n
        image: n8nio/n8n:latest
        env:
        - name: N8N_ENCRYPTION_KEY
          valueFrom:
            secretKeyRef:
              name: n8n-secrets
              key: encryption-key
```

## Monitoring and Observability

### Metrics to Track
- **Processing Time**: Time from upload to report generation
- **Success Rate**: % of successful completions
- **Retry Count**: Number of retries per job
- **Queue Depth**: Pending jobs waiting for processing
- **Error Rate**: Failed jobs by error type

### Logging
All workflow executions are logged in n8n with:
- Execution ID
- Input/Output of each node
- Errors and stack traces
- Execution time per node

### Alerts
Configure alerts for:
- Pipeline failures (> 5% error rate)
- Long processing times (> 5 minutes)
- High queue depth (> 50 pending jobs)

## Integration with FastAPI

The n8n workflow calls these FastAPI endpoints:

1. `POST /upload` - Create job and upload CSV
2. `POST /process/{job_id}` - Start processing
3. `GET /job/{job_id}` - Check status
4. `GET /report/{job_id}` - Retrieve report

The FastAPI service doesn't need to know about n8n - it's a pure HTTP API.

## Alternative: Airflow Comparison

| Feature | n8n | Airflow |
|---------|-----|---------|
| Visual UI | ✅ Better | ⚠️ Limited |
| Learning Curve | ✅ Low | ❌ High |
| Code-based | ⚠️ Limited | ✅ Full Python |
| Webhooks | ✅ Native | ⚠️ Requires plugins |
| Error Handling | ✅ Built-in | ⚠️ Manual |
| Hosting | ✅ Cloud + Self | ⚠️ Self only |

**Verdict**: n8n is better for this use case because:
- Non-technical stakeholders can modify workflow
- Built-in webhook triggers
- Easier deployment
- Our business logic is already in Python services

## Testing the Workflow

### Manual Test
```bash
# 1. Start FastAPI
cd /home/runner/work/ai-data-analyst/ai-data-analyst
python -m uvicorn api.main:app --reload

# 2. Start n8n (Docker)
docker run -it --rm \
  --name n8n \
  -p 5678:5678 \
  -e WEBHOOK_URL=http://localhost:5678/ \
  n8nio/n8n

# 3. Trigger webhook
curl -X POST http://localhost:5678/webhook/csv-upload \
  -F "file=@sample_data.csv" \
  -F "business_context={\"domain\":\"sales\"}"
```

### Automated Test
See `tests/test_n8n_workflow.py` for integration tests.

## Production Checklist

- [ ] Set up n8n on production infrastructure
- [ ] Configure SSL/TLS for webhook endpoints
- [ ] Set up monitoring and alerting
- [ ] Configure backup and recovery
- [ ] Load test with concurrent uploads
- [ ] Document runbooks for common failures
- [ ] Set up log aggregation (e.g., ELK stack)

## Future Enhancements

1. **Parallel Processing**: Process multiple CSVs concurrently
2. **Scheduled Reports**: Trigger analysis on schedule
3. **Report Distribution**: Auto-email reports to stakeholders
4. **Quality Gates**: Block low-quality data from processing
5. **Cost Optimization**: Cache LLM results for similar analyses
