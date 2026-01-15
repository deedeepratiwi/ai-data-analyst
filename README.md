# AI CSV → Business Insight Generator

> **Production-grade AI analytics system that transforms CSV data into actionable business insights**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 What This System Does

Upload a CSV file → Receive an executive-ready business intelligence report with:

- ✅ **Automated Data Quality Assessment** - Column standardization, missing value analysis, duplicate detection
- 📊 **Deterministic Analytics** - Statistical summaries, trends, correlations, anomalies (pure Python)
- 🤖 **AI-Powered Insights** - LLM-generated executive summary, key findings, and recommendations
- 📈 **Visualizations** - Auto-generated charts embedded in reports
- 📝 **Markdown Reports** - Professional, PDF-ready documentation
- 🔍 **Full Audit Trail** - Complete reproducibility and observability

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        FastAPI Gateway                       │
│  POST /upload │ POST /process │ GET /job │ GET /report      │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           v
┌─────────────────────────────────────────────────────────────┐
│                     n8n Orchestration                        │
│  Workflow Control │ Error Handling │ Retry Logic            │
└──────────────────────────┬──────────────────────────────────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
           v               v               v
    ┌──────────┐    ┌──────────┐   ┌──────────┐
    │   Data   │    │   EDA    │   │ Insight  │
    │ Quality  │───▶│ Metrics  │───▶│Generator │
    │ Service  │    │ Service  │   │ (LLM)    │
    └──────────┘    └──────────┘   └──────────┘
           │               │               │
           └───────────────┼───────────────┘
                           v
                    ┌──────────┐
                    │  Report  │
                    │ Builder  │
                    └──────────┘
                           │
                           v
                    ┌──────────┐
                    │ Storage  │
                    │ Manager  │
                    └──────────┘
```

### Core Principles

**Separation of Concerns**:
- **Truth** (Python): All numerical calculations, data transformations
- **Reasoning** (LLM): Interpretation, insight generation, recommendations
- **Orchestration** (n8n): Workflow control, error handling, retries

**Security & Privacy**:
- ❌ LLMs **NEVER** see raw CSV data
- ✅ LLMs only interpret aggregated metrics (JSON)
- ✅ MCP (Model Context Protocol) constrains LLM behavior
- ✅ Full audit trail of all LLM interactions

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- OpenAI or Anthropic API key
- (Optional) n8n for workflow orchestration

### Installation

```bash
# Clone repository
git clone https://github.com/deedeepratiwi/ai-data-analyst.git
cd ai-data-analyst

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### Configuration

Create `.env` file:

```env
# LLM Provider (openai or anthropic)
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
# ANTHROPIC_API_KEY=your-key-here

# Application Settings
STORAGE_PATH=./storage/data
REPORTS_PATH=./storage/reports
CHARTS_PATH=./storage/charts
DB_PATH=./storage/metadata.db

# API Settings
API_HOST=0.0.0.0
API_PORT=8000

# LLM Settings
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=2000
LLM_MODEL=gpt-4-turbo-preview
```

### Run the API

```bash
# Start FastAPI server
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# API available at http://localhost:8000
# API docs at http://localhost:8000/docs
```

### Try the Demo

```bash
# Run end-to-end analysis
python examples/run_analysis.py examples/sales_data.csv

# Output saved to:
# - storage/data/     - Cleaned data and metrics JSON
# - storage/reports/  - Final markdown report
# - storage/charts/   - Generated visualizations
```

### Using the API

```bash
# 1. Upload CSV
curl -X POST http://localhost:8000/upload \
  -F "file=@examples/sales_data.csv" \
  > job_response.json

export JOB_ID=$(jq -r .job_id job_response.json)

# 2. Start processing
curl -X POST http://localhost:8000/process/$JOB_ID

# 3. Check status
curl http://localhost:8000/job/$JOB_ID

# 4. Get report (when completed)
curl http://localhost:8000/report/$JOB_ID
```

## 📊 System Components

### 1. Data Quality Service

**Responsibilities**:
- Column name standardization (snake_case)
- Non-value detection (ERROR, NULL, N/A → NaN)
- String normalization
- Smart type casting (auto-detect numeric, datetime)
- Duplicate removal
- Schema inference
- Data quality scoring (0-100)

**Output**: Cleaned DataFrame + validation summary JSON

### 2. EDA Service

**Responsibilities**:
- KPI computation (totals, averages, growth rates)
- Trend detection (linear regression, strength classification)
- Distribution analysis (mean, median, std, quartiles, skewness, kurtosis)
- Anomaly detection (IQR method)
- Correlation analysis
- Chart generation (distributions, bar charts, time series, heatmaps)

**Output**: Structured metrics JSON + base64-encoded charts

### 3. Insight Service (LLM)

**Responsibilities**:
- Accept **ONLY** validated metrics JSON (no raw data)
- Generate executive summary
- Identify key insights with supporting evidence
- Flag risks and caveats
- Provide actionable recommendations
- Constrained by MCP schema

**Output**: Structured insights JSON

### 4. Report Builder

**Responsibilities**:
- Combine insights + charts into Markdown
- Create executive-ready format
- Embed visualizations
- Include metadata and audit trail
- PDF-ready structure

**Output**: Markdown report

### 5. Storage Manager

**Responsibilities**:
- SQLite metadata database
- File system management
- Audit logging
- Job tracking
- Reproducibility

**Output**: Persistent storage + audit logs

## 🔒 MCP (Model Context Protocol)

The system uses **MCP** to strictly constrain LLM behavior:

```python
{
  "constraints": {
    "use_only_provided_metrics": true,
    "no_calculations": true,
    "no_raw_data_inference": true,
    "no_speculation": true,
    "cite_specific_metrics": true
  },
  "metrics_summary": {
    "dataset_overview": {...},
    "kpis": {...},
    "trends": {...},
    "anomalies": {...}
  },
  "instructions": [
    "Analyze ONLY the provided metrics",
    "Do not perform any calculations",
    "Cite specific metrics when making observations"
  ]
}
```

See `schemas/mcp.py` for full schema definition and examples.

## 🔄 n8n Workflow Orchestration

The system uses **n8n** for workflow control:

```
CSV Upload → Create Job → Start Processing → Poll Status
                                    ↓
                          ┌─────────┴─────────┐
                          │                   │
                      Completed            Failed
                          │                   │
                    Get Report        Send Error Alert
                          │
                   ┌──────┴──────┐
                   │             │
              Quality ≥ 70   Quality < 70
                   │             │
            Full Report   Limited Report
```

**Why n8n?**:
- Visual workflow editor
- Built-in error handling and retries
- Webhook triggers for async processing
- Non-technical stakeholders can modify workflows
- Easy deployment (cloud or self-hosted)

See `orchestration/n8n/README.md` for workflow details and deployment instructions.

## 📚 API Documentation

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/upload` | Upload CSV file |
| POST | `/process/{job_id}` | Start analysis pipeline |
| GET | `/job/{job_id}` | Get job status |
| GET | `/report/{job_id}` | Get final report |

### Example Responses

**POST /upload**:
```json
{
  "job_id": "abc-123-def-456",
  "status": "pending",
  "filename": "sales_data.csv",
  "file_size": 52480
}
```

**GET /job/{job_id}**:
```json
{
  "job_id": "abc-123-def-456",
  "status": "completed",
  "data_quality_score": 92.5,
  "total_rows": 524,
  "total_columns": 8,
  "report_available": true
}
```

Full API documentation available at `/docs` when server is running.

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run integration tests
pytest tests/test_integration.py -v

# Run critical security test (no data leakage)
pytest tests/test_integration.py::TestIntegrationPipeline::test_no_raw_data_leakage -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

See `tests/README.md` for detailed testing documentation.

## 📖 Examples

Three sample datasets provided in `examples/`:

1. **sales_data.csv** - Clean e-commerce data (high quality)
2. **financial_data.csv** - Time-series financial metrics
3. **messy_data.csv** - Low quality data with various issues

Run demo:
```bash
python examples/run_analysis.py examples/sales_data.csv
```

See `examples/README.md` for detailed examples and usage patterns.

## 🚢 Deployment

### Docker

```bash
# Build image
docker build -t ai-data-analyst .

# Run container
docker run -d \
  --name ai-data-analyst \
  -p 8000:8000 \
  -e OPENAI_API_KEY=your-key \
  -v $(pwd)/storage:/app/storage \
  ai-data-analyst
```

### GCP (Cloud Run)

```bash
# Build and push
gcloud builds submit --tag gcr.io/PROJECT_ID/ai-data-analyst

# Deploy
gcloud run deploy ai-data-analyst \
  --image gcr.io/PROJECT_ID/ai-data-analyst \
  --platform managed \
  --region us-central1 \
  --set-env-vars OPENAI_API_KEY=your-key
```

### AWS (ECS/Fargate)

```bash
# Build and push to ECR
aws ecr create-repository --repository-name ai-data-analyst
docker tag ai-data-analyst:latest AWS_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/ai-data-analyst:latest
docker push AWS_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/ai-data-analyst:latest

# Deploy via ECS console or CloudFormation
```

See deployment guides in `docs/deployment/` for detailed instructions.

## 🛠️ Development

### Project Structure

```
ai-data-analyst/
├── api/                    # FastAPI application
│   └── main.py
├── services/               # Business logic services
│   ├── data_quality/      # Data profiling & cleaning
│   ├── eda/               # Exploratory data analysis
│   ├── insights/          # LLM insight generation
│   └── report/            # Report building
├── schemas/                # Pydantic models & MCP
│   └── mcp.py
├── storage/                # Storage manager & models
│   ├── manager.py
│   └── models.py
├── orchestration/          # n8n workflows
│   └── n8n/
├── examples/               # Example data & scripts
├── tests/                  # Test suite
├── requirements.txt        # Dependencies
├── pyproject.toml         # Project configuration
└── README.md              # This file
```

### Code Quality

```bash
# Format code
black .

# Lint
flake8 .

# Type checking
mypy .

# Security scan
bandit -r .
```

## 📊 Performance

| Dataset Size | Processing Time | Memory Usage |
|--------------|-----------------|--------------|
| < 1K rows | 5-10 seconds | < 100 MB |
| 1K-10K rows | 10-30 seconds | 100-500 MB |
| 10K-100K rows | 30-120 seconds | 500 MB - 2 GB |

*Times include LLM API calls. Memory is peak usage.*

## 🔐 Security

- ✅ **No raw data to LLM** - Only aggregated metrics
- ✅ **Input validation** - File type and size limits
- ✅ **API authentication** - Header-based auth support
- ✅ **Audit logging** - Complete operation trail
- ✅ **Environment secrets** - No hardcoded credentials
- ✅ **Rate limiting** - Configurable request throttling

## 🎓 Use Cases

1. **Zoomcamp Capstone**: Demonstrates MLOps, LLM engineering, production architecture
2. **Portfolio Project**: Showcases full-stack AI system design
3. **Micro-SaaS MVP**: Ready for monetization and scaling
4. **Business Analytics**: Real-world data analysis automation
5. **Educational Tool**: Learn AI system architecture best practices

## 📄 License

MIT License - see LICENSE file for details

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Ensure all tests pass
5. Submit a pull request

## 📧 Support

- 📖 Documentation: [docs/](docs/)
- 🐛 Issues: [GitHub Issues](https://github.com/deedeepratiwi/ai-data-analyst/issues)
- 💬 Discussions: [GitHub Discussions](https://github.com/deedeepratiwi/ai-data-analyst/discussions)

## 🙏 Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [Pandas](https://pandas.pydata.org/) - Data manipulation
- [OpenAI](https://openai.com/) / [Anthropic](https://anthropic.com/) - LLM providers
- [n8n](https://n8n.io/) - Workflow automation
- [Matplotlib](https://matplotlib.org/) / [Seaborn](https://seaborn.pydata.org/) - Visualization

---

**Built by**: AI Data Analyst Team  
**Version**: 0.1.0  
**Status**: Production-ready 🚀
