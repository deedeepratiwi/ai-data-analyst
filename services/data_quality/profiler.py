"""Data quality profiler for CSV data validation and cleaning."""
import re
import logging
from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)


class DataQualityProfiler:
    """
    Performs data quality checks and cleaning operations.
    
    Responsibilities:
    - Column standardization (snake_case)
    - Non-value detection and replacement
    - String normalization
    - Smart type casting
    - Duplicate removal
    - Schema inference
    - Missing value analysis
    """
    
    def __init__(self):
        self.non_values = {
            'ERROR', 'UNKNOWN', 'N/A', 'NA', 'NULL', 'null', 
            'None', 'none', '#N/A', '#VALUE!', '#REF!', '#DIV/0!',
            '', ' ', '  ', 'nan', 'NaN', 'NAN'
        }
    
    def profile_and_clean(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Main method to profile and clean dataframe.
        
        Args:
            df: Input dataframe
            
        Returns:
            Tuple of (cleaned_df, validation_summary)
        """
        logger.info(f"Starting data quality profiling for dataframe with shape {df.shape}")
        
        original_shape = df.shape
        validation_summary = {
            "original_shape": {"rows": original_shape[0], "columns": original_shape[1]},
            "timestamp": datetime.utcnow().isoformat(),
            "operations_performed": []
        }
        
        # Step 1: Column standardization
        df, col_mapping = self._standardize_columns(df)
        validation_summary["operations_performed"].append({
            "operation": "column_standardization",
            "column_mapping": col_mapping
        })
        
        # Step 2: Non-value detection and replacement
        df, non_value_stats = self._replace_non_values(df)
        validation_summary["operations_performed"].append({
            "operation": "non_value_replacement",
            "non_values_replaced": non_value_stats
        })
        
        # Step 3: String normalization
        df, normalized_cols = self._normalize_strings(df)
        validation_summary["operations_performed"].append({
            "operation": "string_normalization",
            "columns_normalized": normalized_cols
        })
        
        # Step 4: Smart type casting
        df, type_casting_summary = self._smart_type_casting(df)
        validation_summary["operations_performed"].append({
            "operation": "type_casting",
            "type_changes": type_casting_summary
        })
        
        # Step 5: Duplicate removal
        df, dup_info = self._remove_duplicates(df)
        validation_summary["operations_performed"].append({
            "operation": "duplicate_removal",
            "duplicates_removed": dup_info
        })
        
        # Step 6: Schema inference
        schema = self._infer_schema(df)
        validation_summary["schema"] = schema
        
        # Step 7: Missing value statistics
        missing_stats = self._analyze_missing_values(df)
        validation_summary["missing_values"] = missing_stats
        
        # Step 8: Data quality score
        quality_score = self._calculate_quality_score(df, validation_summary)
        validation_summary["data_quality_score"] = quality_score
        
        validation_summary["final_shape"] = {"rows": df.shape[0], "columns": df.shape[1]}
        
        logger.info(f"Data quality profiling completed. Quality score: {quality_score:.2f}")
        
        return df, validation_summary
    
    def _standardize_columns(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, str]]:
        """Convert column names to snake_case."""
        mapping = {}
        new_columns = []
        
        for col in df.columns:
            # Convert to snake_case
            new_col = re.sub(r'(?<!^)(?=[A-Z])', '_', str(col))  # CamelCase to snake_case
            new_col = re.sub(r'[^\w\s]', '_', new_col)  # Replace special chars with _
            new_col = re.sub(r'\s+', '_', new_col)  # Replace spaces with _
            new_col = new_col.lower()
            new_col = re.sub(r'_+', '_', new_col)  # Replace multiple _ with single
            new_col = new_col.strip('_')
            
            mapping[col] = new_col
            new_columns.append(new_col)
        
        df.columns = new_columns
        logger.info(f"Standardized {len(mapping)} column names")
        
        return df, mapping
    
    def _replace_non_values(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, int]]:
        """Replace non-values with NaN."""
        stats = {}
        
        for col in df.columns:
            count = 0
            # Check if column contains strings
            if df[col].dtype == 'object':
                # Replace non-values
                mask = df[col].isin(self.non_values) | (df[col].str.strip() == '')
                count = mask.sum()
                df.loc[mask, col] = np.nan
            
            if count > 0:
                stats[col] = count
        
        total_replaced = sum(stats.values())
        logger.info(f"Replaced {total_replaced} non-values across {len(stats)} columns")
        
        return df, stats
    
    def _normalize_strings(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
        """Normalize string values to lowercase snake_case."""
        normalized_cols = []
        
        for col in df.columns:
            if df[col].dtype == 'object':
                # Check if column looks like categorical data (not IDs or free text)
                unique_ratio = df[col].nunique() / len(df)
                avg_length = df[col].dropna().astype(str).str.len().mean()
                
                # Normalize if it looks like categorical (< 50% unique, avg length < 50)
                if unique_ratio < 0.5 and avg_length < 50:
                    df[col] = df[col].apply(lambda x: 
                        re.sub(r'[^\w\s]', '_', str(x)).lower().strip() 
                        if pd.notna(x) else x
                    )
                    normalized_cols.append(col)
        
        logger.info(f"Normalized strings in {len(normalized_cols)} columns")
        
        return df, normalized_cols
    
    def _smart_type_casting(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, str]]:
        """Auto-detect and cast numeric and datetime columns."""
        type_changes = {}
        
        for col in df.columns:
            original_type = str(df[col].dtype)
            
            # Skip if already numeric or datetime
            if df[col].dtype in ['int64', 'float64', 'datetime64[ns]']:
                continue
            
            # Try numeric conversion
            try:
                # Remove common numeric formatting
                if df[col].dtype == 'object':
                    temp_series = df[col].str.replace(',', '').str.replace('$', '').str.strip()
                    numeric_series = pd.to_numeric(temp_series, errors='coerce')
                    
                    # If most values convert successfully, use it
                    if numeric_series.notna().sum() / len(df) > 0.8:
                        df[col] = numeric_series
                        type_changes[col] = f"{original_type} -> {df[col].dtype}"
                        continue
            except:
                pass
            
            # Try datetime conversion
            try:
                if df[col].dtype == 'object':
                    datetime_series = pd.to_datetime(df[col], errors='coerce')
                    
                    # If most values convert successfully, use it
                    if datetime_series.notna().sum() / len(df) > 0.8:
                        df[col] = datetime_series
                        type_changes[col] = f"{original_type} -> datetime64[ns]"
                        continue
            except:
                pass
        
        logger.info(f"Cast {len(type_changes)} columns to appropriate types")
        
        return df, type_changes
    
    def _remove_duplicates(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, int]]:
        """Remove duplicate rows."""
        original_count = len(df)
        df = df.drop_duplicates()
        duplicates_removed = original_count - len(df)
        
        info = {
            "original_rows": original_count,
            "duplicates_removed": duplicates_removed,
            "final_rows": len(df)
        }
        
        logger.info(f"Removed {duplicates_removed} duplicate rows")
        
        return df, info
    
    def _infer_schema(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Infer schema information from dataframe."""
        schema = {}
        
        for col in df.columns:
            col_info = {
                "dtype": str(df[col].dtype),
                "nullable": bool(df[col].isna().any()),
                "unique_count": int(df[col].nunique()),
                "unique_ratio": float(df[col].nunique() / len(df))
            }
            
            # Add type-specific info
            if df[col].dtype in ['int64', 'float64']:
                col_info["min"] = float(df[col].min()) if pd.notna(df[col].min()) else None
                col_info["max"] = float(df[col].max()) if pd.notna(df[col].max()) else None
                col_info["mean"] = float(df[col].mean()) if pd.notna(df[col].mean()) else None
                col_info["median"] = float(df[col].median()) if pd.notna(df[col].median()) else None
            elif df[col].dtype == 'datetime64[ns]':
                col_info["min"] = str(df[col].min()) if pd.notna(df[col].min()) else None
                col_info["max"] = str(df[col].max()) if pd.notna(df[col].max()) else None
            elif df[col].dtype == 'object':
                col_info["max_length"] = int(df[col].astype(str).str.len().max())
                col_info["avg_length"] = float(df[col].astype(str).str.len().mean())
            
            schema[col] = col_info
        
        return schema
    
    def _analyze_missing_values(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze missing values in dataframe."""
        total_cells = df.shape[0] * df.shape[1]
        total_missing = df.isna().sum().sum()
        
        missing_by_column = {}
        for col in df.columns:
            missing_count = df[col].isna().sum()
            if missing_count > 0:
                missing_by_column[col] = {
                    "count": int(missing_count),
                    "percentage": float(missing_count / len(df) * 100)
                }
        
        return {
            "total_cells": total_cells,
            "total_missing": int(total_missing),
            "missing_percentage": float(total_missing / total_cells * 100),
            "columns_with_missing": missing_by_column
        }
    
    def _calculate_quality_score(self, df: pd.DataFrame, validation_summary: Dict) -> float:
        """
        Calculate overall data quality score (0-100).
        
        Scoring factors:
        - Completeness (missing values)
        - Duplicates
        - Type consistency
        """
        score = 100.0
        
        # Penalize for missing values
        missing_pct = validation_summary["missing_values"]["missing_percentage"]
        score -= min(missing_pct, 30)  # Max 30 point penalty
        
        # Penalize for duplicates
        dup_info = next(
            (op for op in validation_summary["operations_performed"] 
             if op["operation"] == "duplicate_removal"),
            None
        )
        if dup_info:
            dup_pct = (dup_info["duplicates_removed"] / 
                      dup_info["original_rows"] * 100)
            score -= min(dup_pct, 20)  # Max 20 point penalty
        
        # Bonus for successful type casting
        type_info = next(
            (op for op in validation_summary["operations_performed"] 
             if op["operation"] == "type_casting"),
            None
        )
        if type_info and len(type_info["type_changes"]) > 0:
            score += min(len(type_info["type_changes"]) * 2, 10)  # Max 10 point bonus
        
        return max(0.0, min(100.0, score))
