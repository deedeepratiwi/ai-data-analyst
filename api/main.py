"""FastAPI Gateway for AI CSV → Business Insight Generator.

Production-grade REST API for CSV analysis pipeline.

Endpoints:
- POST /upload: Upload CSV and create job
- POST /process/{job_id}: Trigger complete analysis pipeline
- GET /job/{job_id}: Get job status and metadata
- GET /report/{job_id}: Get final Markdown report
- GET /health: Health check endpoint
"""
import os
import io
import logging
import traceback
from datetime import datetime
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

import pandas as pd
from fastapi import FastAPI, UploadFile, File, HTTPException, status
from fastapi.responses import PlainTextResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

from storage.manager import StorageManager
from services.data_quality.profiler import DataQualityProfiler
from services.eda.metrics import EDAMetricsGenerator
from services.insights.generator import InsightGenerator
from services.report.builder import ReportBuilder


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Configuration
class Settings(BaseSettings):
    """Application settings from environment variables."""
    
    # Storage paths
    storage_path: str = "./storage/data"
    reports_path: str = "./storage/reports"
    charts_path: str = "./storage/charts"
    db_path: str = "./storage/metadata.db"
    
    # API settings
    max_file_size_mb: int = 100
    allowed_extensions: str = ".csv"
    
    # LLM settings
    llm_provider: str = "openai"
    llm_model: Optional[str] = None
    llm_temperature: float = 0.1
    llm_max_tokens: int = 2000
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    
    # CORS settings
    cors_origins: str = "*"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Initialize settings
settings = Settings()


# Global instances
storage_manager: Optional[StorageManager] = None
data_quality_profiler: Optional[DataQualityProfiler] = None
eda_generator: Optional[EDAMetricsGenerator] = None
insight_generator: Optional[InsightGenerator] = None
report_builder: Optional[ReportBuilder] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle management for FastAPI app."""
    global storage_manager, data_quality_profiler, eda_generator, insight_generator, report_builder
    
    # Startup
    logger.info("Initializing application...")
    
    try:
        # Initialize storage manager
        storage_manager = StorageManager(
            storage_path=settings.storage_path,
            reports_path=settings.reports_path,
            charts_path=settings.charts_path,
            db_path=settings.db_path
        )
        logger.info("Storage manager initialized")
        
        # Initialize services
        data_quality_profiler = DataQualityProfiler()
        logger.info("Data quality profiler initialized")
        
        eda_generator = EDAMetricsGenerator()
        logger.info("EDA metrics generator initialized")
        
        # Initialize insight generator (may fail if no API key)
        try:
            insight_generator = InsightGenerator(
                provider_name=settings.llm_provider,
                api_key=settings.openai_api_key or settings.anthropic_api_key,
                model=settings.llm_model
            )
            logger.info("Insight generator initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize insight generator: {e}")
            logger.warning("System will operate without LLM insights")
            insight_generator = None
        
        report_builder = ReportBuilder()
        logger.info("Report builder initialized")
        
        logger.info("Application startup complete")
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")


# Initialize FastAPI app
app = FastAPI(
    title="AI CSV Business Insight Generator",
    description="Production-grade API for automated CSV analysis and business insights",
    version="1.0.0",
    lifespan=lifespan
)


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Response models
class UploadResponse(BaseModel):
    """Response from upload endpoint."""
    job_id: str = Field(..., description="Unique job identifier")
    filename: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    status: str = Field(..., description="Initial job status")
    message: str = Field(..., description="Success message")


class JobStatusResponse(BaseModel):
    """Response from job status endpoint."""
    job_id: str
    filename: str
    file_size: int
    status: str
    upload_timestamp: str
    processing_started: Optional[str] = None
    processing_completed: Optional[str] = None
    error_message: Optional[str] = None
    total_rows: Optional[int] = None
    total_columns: Optional[int] = None
    data_quality_score: Optional[float] = None
    has_duplicates: Optional[int] = None
    missing_value_pct: Optional[float] = None
    report_available: bool = False


class ProcessResponse(BaseModel):
    """Response from process endpoint."""
    job_id: str
    status: str
    message: str
    data_quality_score: Optional[float] = None
    total_rows: Optional[int] = None
    total_columns: Optional[int] = None
    execution_time_ms: Optional[float] = None


class HealthResponse(BaseModel):
    """Response from health check endpoint."""
    status: str
    timestamp: str
    services: Dict[str, str]
    version: str


# Endpoints

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "AI CSV Business Insight Generator",
        "version": "1.0.0",
        "status": "operational",
        "documentation": "/docs",
        "health_check": "/health"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    
    Returns system status and service availability.
    """
    services_status = {
        "storage": "available" if storage_manager else "unavailable",
        "data_quality": "available" if data_quality_profiler else "unavailable",
        "eda": "available" if eda_generator else "unavailable",
        "insights": "available" if insight_generator else "unavailable",
        "reporting": "available" if report_builder else "unavailable"
    }
    
    # Check if critical services are available
    critical_services = ["storage", "data_quality", "eda", "reporting"]
    all_critical_available = all(
        services_status.get(svc) == "available" for svc in critical_services
    )
    
    overall_status = "healthy" if all_critical_available else "degraded"
    
    return HealthResponse(
        status=overall_status,
        timestamp=datetime.utcnow().isoformat(),
        services=services_status,
        version="1.0.0"
    )


@app.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_csv(file: UploadFile = File(...)):
    """
    Upload CSV file and create processing job.
    
    Args:
        file: CSV file to upload
        
    Returns:
        UploadResponse with job_id and status
        
    Raises:
        HTTPException: If file validation fails
    """
    logger.info(f"Upload request received: filename={file.filename}")
    
    # Validate file extension
    if not file.filename.endswith('.csv'):
        logger.warning(f"Invalid file extension: {file.filename}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only CSV files are allowed. Got: {file.filename}"
        )
    
    # Read file content
    try:
        content = await file.read()
        file_size = len(content)
        
        # Validate file size
        max_size_bytes = settings.max_file_size_mb * 1024 * 1024
        if file_size > max_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size ({file_size} bytes) exceeds maximum allowed ({max_size_bytes} bytes)"
            )
        
        # Validate CSV format
        try:
            df = pd.read_csv(io.BytesIO(content))
            if len(df) == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="CSV file is empty"
                )
            logger.info(f"CSV validated: {len(df)} rows, {len(df.columns)} columns")
        except Exception as e:
            logger.error(f"Invalid CSV format: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid CSV format: {str(e)}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to read uploaded file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process uploaded file: {str(e)}"
        )
    
    # Create job in storage
    try:
        job_id = storage_manager.create_job(
            filename=file.filename,
            file_size=file_size
        )
        
        # Save uploaded file
        file_path = storage_manager.save_uploaded_file(
            job_id=job_id,
            filename=file.filename,
            content=content
        )
        
        # Log operation
        storage_manager.log_operation(
            job_id=job_id,
            service="api",
            operation="upload",
            status="success",
            input_data={"filename": file.filename, "file_size": file_size},
            output_data={"file_path": file_path, "rows": len(df), "columns": len(df.columns)}
        )
        
        logger.info(f"Job created successfully: job_id={job_id}")
        
        return UploadResponse(
            job_id=job_id,
            filename=file.filename,
            file_size=file_size,
            status="pending",
            message=f"File uploaded successfully. Use POST /process/{job_id} to start analysis."
        )
        
    except Exception as e:
        logger.error(f"Failed to create job: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create job: {str(e)}"
        )


@app.post("/process/{job_id}", response_model=ProcessResponse)
async def process_job(job_id: str):
    """
    Trigger complete analysis pipeline for a job.
    
    Pipeline stages:
    1. Data quality profiling and cleaning
    2. EDA metrics generation
    3. Insight generation (if LLM available)
    4. Report building
    
    Args:
        job_id: Job identifier from upload
        
    Returns:
        ProcessResponse with execution summary
        
    Raises:
        HTTPException: If job not found or processing fails
    """
    logger.info(f"Process request received: job_id={job_id}")
    
    # Verify job exists
    job = storage_manager.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    
    # Check if already processing or completed
    if job.status == "processing":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Job {job_id} is already being processed"
        )
    
    if job.status == "completed":
        return ProcessResponse(
            job_id=job_id,
            status="completed",
            message="Job already completed",
            data_quality_score=job.data_quality_score,
            total_rows=job.total_rows,
            total_columns=job.total_columns
        )
    
    # Update status to processing
    storage_manager.update_job_status(
        job_id=job_id,
        status="processing",
        processing_started=datetime.utcnow()
    )
    
    start_time = datetime.utcnow()
    
    try:
        # Stage 1: Data Quality Profiling
        logger.info(f"[{job_id}] Stage 1: Data quality profiling")
        stage_start = datetime.utcnow()
        
        # Load uploaded CSV
        file_path = storage_manager.storage_path / f"{job_id}_{job.filename}"
        df = pd.read_csv(file_path)
        
        # Profile and clean
        cleaned_df, validation_summary = data_quality_profiler.profile_and_clean(df)
        
        # Save cleaned data
        cleaned_path = storage_manager.save_cleaned_data(job_id, cleaned_df)
        
        # Update job metadata
        storage_manager.update_job_status(
            job_id=job_id,
            status="processing",
            total_rows=int(cleaned_df.shape[0]),
            total_columns=int(cleaned_df.shape[1]),
            data_quality_score=validation_summary["data_quality_score"],
            has_duplicates=validation_summary["operations_performed"][4]["duplicates_removed"]["duplicates_removed"],
            missing_value_pct=validation_summary["missing_values"]["missing_percentage"],
            cleaned_data_path=cleaned_path
        )
        
        stage_time = (datetime.utcnow() - stage_start).total_seconds() * 1000
        
        # Log operation
        storage_manager.log_operation(
            job_id=job_id,
            service="data_quality",
            operation="profile_and_clean",
            status="success",
            input_data={"shape": list(df.shape)},
            output_data={
                "cleaned_shape": list(cleaned_df.shape),
                "quality_score": validation_summary["data_quality_score"]
            },
            execution_time_ms=stage_time
        )
        
        logger.info(f"[{job_id}] Stage 1 complete: quality_score={validation_summary['data_quality_score']:.2f}, time={stage_time:.2f}ms")
        
        # Stage 2: EDA Metrics Generation
        logger.info(f"[{job_id}] Stage 2: EDA metrics generation")
        stage_start = datetime.utcnow()
        
        eda_metrics = eda_generator.generate_metrics(cleaned_df)
        
        # Save metrics JSON
        metrics_path = storage_manager.save_metrics_json(job_id, eda_metrics)
        storage_manager.update_job_status(
            job_id=job_id,
            status="processing",
            metrics_json_path=metrics_path
        )
        
        # Save charts
        charts = eda_metrics.get("charts", {})
        saved_charts = {}
        for chart_name, chart_b64 in charts.items():
            import base64
            chart_bytes = base64.b64decode(chart_b64)
            chart_path = storage_manager.save_chart(job_id, chart_name, chart_bytes)
            saved_charts[chart_name] = chart_path
        
        stage_time = (datetime.utcnow() - stage_start).total_seconds() * 1000
        
        # Log operation
        storage_manager.log_operation(
            job_id=job_id,
            service="eda",
            operation="generate_metrics",
            status="success",
            input_data={"shape": list(cleaned_df.shape)},
            output_data={
                "num_kpis": len(eda_metrics.get("kpis", {})),
                "num_charts": len(charts),
                "has_temporal": eda_metrics.get("temporal_metrics", {}).get("temporal_data_detected", False)
            },
            execution_time_ms=stage_time
        )
        
        logger.info(f"[{job_id}] Stage 2 complete: {len(charts)} charts generated, time={stage_time:.2f}ms")
        
        # Stage 3: Insight Generation (if LLM available)
        insights_result = None
        if insight_generator:
            logger.info(f"[{job_id}] Stage 3: Insight generation")
            stage_start = datetime.utcnow()
            
            try:
                insights_result = insight_generator.generate_insights(eda_metrics)
                
                # Log operation with LLM details
                storage_manager.log_operation(
                    job_id=job_id,
                    service="insights",
                    operation="generate_insights",
                    status="success",
                    input_data={"metrics_summary": "EDA metrics"},
                    output_data={"insights_generated": True},
                    execution_time_ms=insights_result.get("execution_time_ms"),
                    llm_details={
                        "provider": insights_result["llm_metadata"]["provider"],
                        "model": insights_result["llm_metadata"]["model"],
                        "tokens_used": insights_result["llm_metadata"]["tokens_used"],
                        "prompt": f"MCP prompt ({insights_result['prompt_length']} chars)",
                        "response": "Insights generated"
                    }
                )
                
                logger.info(f"[{job_id}] Stage 3 complete: insights generated, time={insights_result['execution_time_ms']:.2f}ms")
                
            except Exception as e:
                logger.error(f"[{job_id}] Stage 3 failed: {str(e)}")
                # Log failure but continue to reporting
                storage_manager.log_operation(
                    job_id=job_id,
                    service="insights",
                    operation="generate_insights",
                    status="failure",
                    error_details=str(e),
                    execution_time_ms=(datetime.utcnow() - stage_start).total_seconds() * 1000
                )
                insights_result = None
        else:
            logger.warning(f"[{job_id}] Stage 3 skipped: LLM not available")
            # Create minimal insights
            insights_result = {
                "insights": {
                    "executive_summary": "Analysis completed without LLM insights. Review metrics below.",
                    "key_insights": [],
                    "risks_and_caveats": [
                        {
                            "concern": "LLM Unavailable",
                            "impact": "No automated insights generated",
                            "recommendation": "Review metrics manually or configure LLM provider"
                        }
                    ],
                    "actionable_recommendations": []
                },
                "llm_metadata": {
                    "provider": "none",
                    "model": "none",
                    "tokens_used": 0
                }
            }
        
        # Stage 4: Report Building
        logger.info(f"[{job_id}] Stage 4: Report building")
        stage_start = datetime.utcnow()
        
        report_content = report_builder.build_report(
            job_id=job_id,
            filename=job.filename,
            data_quality=validation_summary,
            eda_metrics=eda_metrics,
            insights=insights_result,
            charts=charts
        )
        
        # Save report
        report_path = storage_manager.save_report(job_id, report_content)
        storage_manager.update_job_status(
            job_id=job_id,
            status="completed",
            processing_completed=datetime.utcnow(),
            report_path=report_path
        )
        
        stage_time = (datetime.utcnow() - stage_start).total_seconds() * 1000
        
        # Log operation
        storage_manager.log_operation(
            job_id=job_id,
            service="report",
            operation="build_report",
            status="success",
            input_data={"components": ["data_quality", "eda_metrics", "insights", "charts"]},
            output_data={"report_length": len(report_content), "report_path": report_path},
            execution_time_ms=stage_time
        )
        
        logger.info(f"[{job_id}] Stage 4 complete: report saved, time={stage_time:.2f}ms")
        
        # Calculate total execution time
        total_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        logger.info(f"[{job_id}] Pipeline complete: total_time={total_time:.2f}ms")
        
        return ProcessResponse(
            job_id=job_id,
            status="completed",
            message="Analysis pipeline completed successfully",
            data_quality_score=validation_summary["data_quality_score"],
            total_rows=int(cleaned_df.shape[0]),
            total_columns=int(cleaned_df.shape[1]),
            execution_time_ms=total_time
        )
        
    except Exception as e:
        error_msg = f"Pipeline failed: {str(e)}"
        logger.error(f"[{job_id}] {error_msg}")
        logger.error(traceback.format_exc())
        
        # Update job status to failed
        storage_manager.update_job_status(
            job_id=job_id,
            status="failed",
            error_message=error_msg,
            processing_completed=datetime.utcnow()
        )
        
        # Log failure
        storage_manager.log_operation(
            job_id=job_id,
            service="api",
            operation="process_pipeline",
            status="failure",
            error_details=traceback.format_exc(),
            execution_time_ms=(datetime.utcnow() - start_time).total_seconds() * 1000
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )


@app.get("/job/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """
    Get job status and metadata.
    
    Args:
        job_id: Job identifier
        
    Returns:
        JobStatusResponse with current status and metadata
        
    Raises:
        HTTPException: If job not found
    """
    logger.info(f"Status request received: job_id={job_id}")
    
    job = storage_manager.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    
    return JobStatusResponse(
        job_id=job.job_id,
        filename=job.filename,
        file_size=job.file_size,
        status=job.status,
        upload_timestamp=job.upload_timestamp.isoformat(),
        processing_started=job.processing_started.isoformat() if job.processing_started else None,
        processing_completed=job.processing_completed.isoformat() if job.processing_completed else None,
        error_message=job.error_message,
        total_rows=job.total_rows,
        total_columns=job.total_columns,
        data_quality_score=job.data_quality_score,
        has_duplicates=job.has_duplicates,
        missing_value_pct=job.missing_value_pct,
        report_available=job.report_path is not None and job.status == "completed"
    )


@app.get("/report/{job_id}", response_class=PlainTextResponse)
async def get_report(job_id: str):
    """
    Get final Markdown report.
    
    Args:
        job_id: Job identifier
        
    Returns:
        Markdown report as plain text
        
    Raises:
        HTTPException: If job not found, not completed, or failed
    """
    logger.info(f"Report request received: job_id={job_id}")
    
    job = storage_manager.get_job(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )
    
    if job.status == "pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Job {job_id} has not been processed yet. Use POST /process/{job_id} to start."
        )
    
    if job.status == "processing":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Job {job_id} is still processing. Check status with GET /job/{job_id}"
        )
    
    if job.status == "failed":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Job {job_id} failed: {job.error_message}"
        )
    
    if not job.report_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report for job {job_id} not found"
        )
    
    # Read report
    try:
        from pathlib import Path
        report_content = Path(job.report_path).read_text()
        
        logger.info(f"Report retrieved: job_id={job_id}, size={len(report_content)} bytes")
        
        return report_content
        
    except Exception as e:
        logger.error(f"Failed to read report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read report: {str(e)}"
        )


# Error handlers

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler with logging."""
    logger.warning(f"HTTP {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.utcnow().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler for unexpected errors."""
    logger.error(f"Unexpected error: {str(exc)}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "timestamp": datetime.utcnow().isoformat()
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    
    logger.info(f"Starting server on {host}:{port}")
    
    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        reload=os.getenv("RELOAD", "false").lower() == "true",
        log_level="info"
    )
