"""EDA metrics generator for comprehensive data analysis."""
import logging
import io
import base64
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime
from scipy import stats
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns

logger = logging.getLogger(__name__)


class EDAMetricsGenerator:
    """
    Generates comprehensive EDA metrics and visualizations.
    
    Responsibilities:
    - KPI computation (totals, averages, growth rates)
    - Trend detection for numeric columns
    - Distribution summaries (mean, median, std, quartiles, skewness, kurtosis)
    - Anomaly detection using IQR method
    - Chart generation (distribution, bar, time series, correlation)
    
    CRITICAL: Only returns aggregated statistics, NO raw data.
    """
    
    def __init__(self, figsize: Tuple[int, int] = (10, 6), dpi: int = 100):
        """
        Initialize EDA metrics generator.
        
        Args:
            figsize: Default figure size for charts
            dpi: DPI for chart rendering
        """
        self.figsize = figsize
        self.dpi = dpi
        sns.set_style("whitegrid")
        sns.set_palette("husl")
    
    def generate_metrics(self, df: pd.DataFrame, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate comprehensive EDA metrics from cleaned dataframe.
        
        Args:
            df: Cleaned dataframe from data quality service
            context: Optional business context for KPI calculation
            
        Returns:
            Structured metrics dictionary with NO raw data, only aggregates
        """
        logger.info(f"Starting EDA metrics generation for dataframe with shape {df.shape}")
        
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "dataset_overview": self._generate_overview(df),
            "kpis": self._compute_kpis(df, context),
            "numeric_metrics": self._analyze_numeric_columns(df),
            "categorical_metrics": self._analyze_categorical_columns(df),
            "temporal_metrics": self._analyze_temporal_patterns(df),
            "correlations": self._compute_correlations(df),
            "anomalies": self._detect_anomalies(df),
            "charts": self._generate_charts(df)
        }
        
        logger.info(f"EDA metrics generation completed. Generated {len(metrics['charts'])} charts")
        
        return metrics
    
    def _generate_overview(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate high-level dataset overview."""
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
        datetime_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
        
        return {
            "total_rows": int(len(df)),
            "total_columns": int(len(df.columns)),
            "numeric_columns": len(numeric_cols),
            "categorical_columns": len(categorical_cols),
            "datetime_columns": len(datetime_cols),
            "memory_usage_mb": float(df.memory_usage(deep=True).sum() / 1024 / 1024),
            "column_names": df.columns.tolist(),
            "column_types": {col: str(dtype) for col, dtype in df.dtypes.items()}
        }
    
    def _compute_kpis(self, df: pd.DataFrame, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Compute key performance indicators.
        
        Automatically detects:
        - Total sums for numeric columns
        - Averages for numeric columns
        - Growth rates if datetime column exists
        - Record counts by categories
        """
        kpis = {}
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        datetime_cols = df.select_dtypes(include=['datetime64']).columns
        
        # Totals and averages for numeric columns
        for col in numeric_cols:
            col_kpis = {
                "total": float(df[col].sum()) if pd.notna(df[col].sum()) else None,
                "average": float(df[col].mean()) if pd.notna(df[col].mean()) else None,
                "max": float(df[col].max()) if pd.notna(df[col].max()) else None,
                "min": float(df[col].min()) if pd.notna(df[col].min()) else None,
                "count": int(df[col].count())
            }
            kpis[f"{col}_kpis"] = col_kpis
        
        # Growth rates if time series data
        if len(datetime_cols) > 0 and len(numeric_cols) > 0:
            datetime_col = datetime_cols[0]
            df_sorted = df.sort_values(datetime_col)
            
            for num_col in numeric_cols:
                # Calculate period-over-period growth
                first_val = df_sorted[num_col].iloc[0]
                last_val = df_sorted[num_col].iloc[-1]
                
                if pd.notna(first_val) and pd.notna(last_val) and first_val != 0:
                    growth_rate = ((last_val - first_val) / abs(first_val)) * 100
                    kpis[f"{num_col}_growth_rate_pct"] = float(growth_rate)
                
                # Calculate rolling average if enough data
                if len(df_sorted) >= 7:
                    rolling_avg = df_sorted[num_col].rolling(window=min(7, len(df_sorted))).mean().iloc[-1]
                    if pd.notna(rolling_avg):
                        kpis[f"{num_col}_rolling_avg_7"] = float(rolling_avg)
        
        return kpis
    
    def _analyze_numeric_columns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Comprehensive analysis of numeric columns.
        
        Returns distribution summaries, trends, and statistical tests.
        """
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        metrics = {}
        
        for col in numeric_cols:
            col_data = df[col].dropna()
            
            if len(col_data) == 0:
                continue
            
            # Distribution summary
            distribution = {
                "mean": float(col_data.mean()),
                "median": float(col_data.median()),
                "std": float(col_data.std()),
                "variance": float(col_data.var()),
                "min": float(col_data.min()),
                "max": float(col_data.max()),
                "q1": float(col_data.quantile(0.25)),
                "q3": float(col_data.quantile(0.75)),
                "iqr": float(col_data.quantile(0.75) - col_data.quantile(0.25)),
                "range": float(col_data.max() - col_data.min()),
                "coefficient_of_variation": float(col_data.std() / col_data.mean()) if col_data.mean() != 0 else None
            }
            
            # Shape statistics
            try:
                distribution["skewness"] = float(stats.skew(col_data))
                distribution["kurtosis"] = float(stats.kurtosis(col_data))
            except:
                distribution["skewness"] = None
                distribution["kurtosis"] = None
            
            # Distribution interpretation
            if distribution["skewness"] is not None:
                if abs(distribution["skewness"]) < 0.5:
                    distribution["skewness_interpretation"] = "approximately_symmetric"
                elif distribution["skewness"] > 0:
                    distribution["skewness_interpretation"] = "right_skewed"
                else:
                    distribution["skewness_interpretation"] = "left_skewed"
            
            # Trend detection (if data has natural order)
            trend = self._detect_trend(col_data)
            
            metrics[col] = {
                "distribution": distribution,
                "trend": trend,
                "percentiles": {
                    "p5": float(col_data.quantile(0.05)),
                    "p10": float(col_data.quantile(0.10)),
                    "p25": float(col_data.quantile(0.25)),
                    "p50": float(col_data.quantile(0.50)),
                    "p75": float(col_data.quantile(0.75)),
                    "p90": float(col_data.quantile(0.90)),
                    "p95": float(col_data.quantile(0.95))
                }
            }
        
        return metrics
    
    def _detect_trend(self, series: pd.Series) -> Dict[str, Any]:
        """
        Detect trend in numeric series using linear regression.
        
        Returns trend direction, strength, and statistical significance.
        """
        if len(series) < 3:
            return {"detected": False, "reason": "insufficient_data"}
        
        # Fit linear regression
        x = np.arange(len(series))
        y = series.values
        
        # Remove any remaining NaN values
        mask = ~np.isnan(y)
        x = x[mask]
        y = y[mask]
        
        if len(x) < 3:
            return {"detected": False, "reason": "insufficient_valid_data"}
        
        # Linear regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        
        # Determine trend direction
        if abs(slope) < std_err * 2:  # Not statistically significant
            direction = "flat"
        elif slope > 0:
            direction = "increasing"
        else:
            direction = "decreasing"
        
        return {
            "detected": True,
            "direction": direction,
            "slope": float(slope),
            "r_squared": float(r_value ** 2),
            "p_value": float(p_value),
            "is_significant": bool(p_value < 0.05),
            "strength": "strong" if abs(r_value) > 0.7 else "moderate" if abs(r_value) > 0.4 else "weak"
        }
    
    def _analyze_categorical_columns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze categorical columns.
        
        Returns value counts, diversity metrics, and top categories.
        """
        categorical_cols = df.select_dtypes(include=['object']).columns
        metrics = {}
        
        for col in categorical_cols:
            col_data = df[col].dropna()
            
            if len(col_data) == 0:
                continue
            
            value_counts = col_data.value_counts()
            total_count = len(col_data)
            
            # Top categories (limit to top 10 to avoid data leakage)
            top_categories = []
            for i, (category, count) in enumerate(value_counts.head(10).items()):
                top_categories.append({
                    "category": str(category),
                    "count": int(count),
                    "percentage": float(count / total_count * 100)
                })
            
            # Diversity metrics
            entropy = stats.entropy(value_counts)
            
            metrics[col] = {
                "unique_values": int(col_data.nunique()),
                "total_count": int(total_count),
                "diversity_ratio": float(col_data.nunique() / total_count),
                "entropy": float(entropy),
                "top_categories": top_categories,
                "is_highly_diverse": bool(col_data.nunique() / total_count > 0.5),
                "mode": str(value_counts.index[0]) if len(value_counts) > 0 else None,
                "mode_frequency": int(value_counts.iloc[0]) if len(value_counts) > 0 else None,
                "mode_percentage": float(value_counts.iloc[0] / total_count * 100) if len(value_counts) > 0 else None
            }
        
        return metrics
    
    def _analyze_temporal_patterns(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze temporal patterns if datetime columns exist.
        
        Returns time-based aggregations and patterns.
        """
        datetime_cols = df.select_dtypes(include=['datetime64']).columns
        
        if len(datetime_cols) == 0:
            return {"temporal_data_detected": False}
        
        metrics = {"temporal_data_detected": True, "patterns": {}}
        
        for datetime_col in datetime_cols:
            df_temporal = df.dropna(subset=[datetime_col]).copy()
            df_temporal = df_temporal.sort_values(datetime_col)
            
            if len(df_temporal) == 0:
                continue
            
            # Extract temporal components
            df_temporal['year'] = df_temporal[datetime_col].dt.year
            df_temporal['month'] = df_temporal[datetime_col].dt.month
            df_temporal['day_of_week'] = df_temporal[datetime_col].dt.dayofweek
            df_temporal['hour'] = df_temporal[datetime_col].dt.hour
            
            pattern = {
                "date_range": {
                    "start": str(df_temporal[datetime_col].min()),
                    "end": str(df_temporal[datetime_col].max()),
                    "span_days": int((df_temporal[datetime_col].max() - df_temporal[datetime_col].min()).days)
                },
                "records_by_year": df_temporal['year'].value_counts().to_dict(),
                "records_by_month": df_temporal['month'].value_counts().to_dict(),
                "records_by_day_of_week": df_temporal['day_of_week'].value_counts().to_dict(),
                "temporal_distribution": self._calculate_temporal_distribution(df_temporal, datetime_col)
            }
            
            # Analyze numeric columns over time
            numeric_cols = df_temporal.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) > 0:
                time_series_metrics = {}
                for num_col in numeric_cols[:5]:  # Limit to 5 to avoid excessive data
                    # Aggregate by date
                    daily_agg = df_temporal.groupby(df_temporal[datetime_col].dt.date)[num_col].agg(['mean', 'sum', 'count'])
                    
                    time_series_metrics[num_col] = {
                        "daily_average_mean": float(daily_agg['mean'].mean()) if len(daily_agg) > 0 else None,
                        "daily_average_std": float(daily_agg['mean'].std()) if len(daily_agg) > 0 else None,
                        "peak_date": str(daily_agg['sum'].idxmax()) if len(daily_agg) > 0 else None,
                        "peak_value": float(daily_agg['sum'].max()) if len(daily_agg) > 0 else None,
                        "lowest_date": str(daily_agg['sum'].idxmin()) if len(daily_agg) > 0 else None,
                        "lowest_value": float(daily_agg['sum'].min()) if len(daily_agg) > 0 else None
                    }
                
                pattern["time_series_metrics"] = time_series_metrics
            
            metrics["patterns"][datetime_col] = pattern
        
        return metrics
    
    def _calculate_temporal_distribution(self, df: pd.DataFrame, datetime_col: str) -> Dict[str, Any]:
        """Calculate how records are distributed over time."""
        total_records = len(df)
        date_counts = df[datetime_col].dt.date.value_counts()
        
        return {
            "total_unique_dates": int(len(date_counts)),
            "avg_records_per_date": float(date_counts.mean()),
            "max_records_single_date": int(date_counts.max()),
            "min_records_single_date": int(date_counts.min()),
            "dates_with_most_activity": [
                {"date": str(date), "count": int(count)} 
                for date, count in date_counts.head(5).items()
            ]
        }
    
    def _compute_correlations(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Compute correlation matrix for numeric columns.
        
        Returns correlation coefficients and significant pairs.
        """
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        if len(numeric_cols) < 2:
            return {"correlation_analysis_available": False, "reason": "insufficient_numeric_columns"}
        
        # Compute correlation matrix
        corr_matrix = df[numeric_cols].corr()
        
        # Extract significant correlations (excluding diagonal)
        significant_pairs = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i + 1, len(corr_matrix.columns)):
                col1 = corr_matrix.columns[i]
                col2 = corr_matrix.columns[j]
                corr_value = corr_matrix.iloc[i, j]
                
                if pd.notna(corr_value) and abs(corr_value) > 0.3:  # Threshold for significance
                    significant_pairs.append({
                        "column1": col1,
                        "column2": col2,
                        "correlation": float(corr_value),
                        "strength": "strong" if abs(corr_value) > 0.7 else "moderate" if abs(corr_value) > 0.5 else "weak",
                        "direction": "positive" if corr_value > 0 else "negative"
                    })
        
        # Sort by absolute correlation value
        significant_pairs.sort(key=lambda x: abs(x["correlation"]), reverse=True)
        
        return {
            "correlation_analysis_available": True,
            "total_numeric_columns": len(numeric_cols),
            "significant_correlations": significant_pairs[:20],  # Limit to top 20
            "correlation_matrix_shape": list(corr_matrix.shape)
        }
    
    def _detect_anomalies(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Detect anomalies using IQR method.
        
        Returns anomaly counts and thresholds (NO raw anomalous records).
        """
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        anomalies = {}
        
        for col in numeric_cols:
            col_data = df[col].dropna()
            
            if len(col_data) < 4:  # Need at least 4 points for IQR
                continue
            
            # IQR method
            q1 = col_data.quantile(0.25)
            q3 = col_data.quantile(0.75)
            iqr = q3 - q1
            
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            # Count anomalies
            lower_outliers = (col_data < lower_bound).sum()
            upper_outliers = (col_data > upper_bound).sum()
            total_outliers = lower_outliers + upper_outliers
            
            if total_outliers > 0:
                anomalies[col] = {
                    "total_anomalies": int(total_outliers),
                    "lower_outliers": int(lower_outliers),
                    "upper_outliers": int(upper_outliers),
                    "anomaly_percentage": float(total_outliers / len(col_data) * 100),
                    "lower_bound": float(lower_bound),
                    "upper_bound": float(upper_bound),
                    "iqr": float(iqr),
                    "extreme_anomalies": int(((col_data < q1 - 3 * iqr) | (col_data > q3 + 3 * iqr)).sum())
                }
        
        return {
            "anomalies_detected": len(anomalies) > 0,
            "columns_with_anomalies": list(anomalies.keys()),
            "details": anomalies
        }
    
    def _generate_charts(self, df: pd.DataFrame) -> Dict[str, str]:
        """
        Generate visualization charts.
        
        Returns base64-encoded PNG images.
        """
        charts = {}
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        categorical_cols = df.select_dtypes(include=['object']).columns
        datetime_cols = df.select_dtypes(include=['datetime64']).columns
        
        # Distribution plots for numeric columns (limit to first 6)
        for col in numeric_cols[:6]:
            chart = self._create_distribution_plot(df, col)
            if chart:
                charts[f"distribution_{col}"] = chart
        
        # Bar charts for categorical columns (limit to first 6)
        for col in categorical_cols[:6]:
            chart = self._create_bar_chart(df, col)
            if chart:
                charts[f"bar_{col}"] = chart
        
        # Time series plots if datetime column exists
        if len(datetime_cols) > 0 and len(numeric_cols) > 0:
            datetime_col = datetime_cols[0]
            for num_col in numeric_cols[:4]:  # Limit to 4
                chart = self._create_time_series_plot(df, datetime_col, num_col)
                if chart:
                    charts[f"timeseries_{datetime_col}_{num_col}"] = chart
        
        # Correlation heatmap if multiple numeric columns
        if len(numeric_cols) >= 2:
            chart = self._create_correlation_heatmap(df, numeric_cols)
            if chart:
                charts["correlation_heatmap"] = chart
        
        logger.info(f"Generated {len(charts)} charts")
        
        return charts
    
    def _create_distribution_plot(self, df: pd.DataFrame, column: str) -> Optional[str]:
        """Create histogram with KDE for numeric column."""
        try:
            plt.figure(figsize=self.figsize, dpi=self.dpi)
            
            data = df[column].dropna()
            if len(data) == 0:
                plt.close()
                return None
            
            # Histogram with KDE
            plt.subplot(1, 2, 1)
            plt.hist(data, bins=min(30, len(data) // 10 + 1), edgecolor='black', alpha=0.7)
            plt.xlabel(column)
            plt.ylabel('Frequency')
            plt.title(f'Distribution of {column}')
            plt.grid(axis='y', alpha=0.3)
            
            # Box plot
            plt.subplot(1, 2, 2)
            plt.boxplot(data, vert=True, whis=1.5)
            plt.ylabel(column)
            plt.title(f'Box Plot of {column}')
            plt.grid(axis='y', alpha=0.3)
            
            plt.tight_layout()
            
            # Convert to base64
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode()
            plt.close()
            
            return image_base64
        except Exception as e:
            logger.warning(f"Failed to create distribution plot for {column}: {e}")
            plt.close()
            return None
    
    def _create_bar_chart(self, df: pd.DataFrame, column: str, top_n: int = 10) -> Optional[str]:
        """Create bar chart for categorical column."""
        try:
            plt.figure(figsize=self.figsize, dpi=self.dpi)
            
            value_counts = df[column].value_counts().head(top_n)
            if len(value_counts) == 0:
                plt.close()
                return None
            
            plt.bar(range(len(value_counts)), value_counts.values, edgecolor='black')
            plt.xlabel(column)
            plt.ylabel('Count')
            plt.title(f'Top {len(value_counts)} Categories in {column}')
            plt.xticks(range(len(value_counts)), value_counts.index, rotation=45, ha='right')
            plt.grid(axis='y', alpha=0.3)
            plt.tight_layout()
            
            # Convert to base64
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode()
            plt.close()
            
            return image_base64
        except Exception as e:
            logger.warning(f"Failed to create bar chart for {column}: {e}")
            plt.close()
            return None
    
    def _create_time_series_plot(self, df: pd.DataFrame, datetime_col: str, value_col: str) -> Optional[str]:
        """Create time series plot."""
        try:
            plt.figure(figsize=self.figsize, dpi=self.dpi)
            
            df_plot = df[[datetime_col, value_col]].dropna().sort_values(datetime_col)
            if len(df_plot) == 0:
                plt.close()
                return None
            
            plt.plot(df_plot[datetime_col], df_plot[value_col], marker='o', linestyle='-', markersize=3)
            plt.xlabel(datetime_col)
            plt.ylabel(value_col)
            plt.title(f'{value_col} over {datetime_col}')
            plt.xticks(rotation=45, ha='right')
            plt.grid(alpha=0.3)
            plt.tight_layout()
            
            # Convert to base64
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode()
            plt.close()
            
            return image_base64
        except Exception as e:
            logger.warning(f"Failed to create time series plot for {datetime_col} vs {value_col}: {e}")
            plt.close()
            return None
    
    def _create_correlation_heatmap(self, df: pd.DataFrame, numeric_cols) -> Optional[str]:
        """Create correlation heatmap."""
        try:
            plt.figure(figsize=(min(12, len(numeric_cols) + 2), min(10, len(numeric_cols))))
            
            corr_matrix = df[numeric_cols].corr()
            
            sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm', 
                       center=0, square=True, linewidths=1, cbar_kws={"shrink": 0.8})
            plt.title('Correlation Heatmap')
            plt.tight_layout()
            
            # Convert to base64
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode()
            plt.close()
            
            return image_base64
        except Exception as e:
            logger.warning(f"Failed to create correlation heatmap: {e}")
            plt.close()
            return None
