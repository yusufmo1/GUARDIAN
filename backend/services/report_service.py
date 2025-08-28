"""
Report Generation Service

High-level service for generating compliance analysis reports for the GUARDIAN 
system. Handles PDF generation, HTML templates, clustering visualizations, 
and report customization for pharmaceutical standards compliance analysis.

Features:
- PDF report generation with WeasyPrint
- HTML template rendering with Jinja2
- Clustering analysis and visualization
- Multiple output formats (PDF, HTML, JSON)
- Report customization and branding
- Analysis result aggregation
"""
import os
import uuid
import time
import json
import base64
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
import io

try:
    from weasyprint import HTML, CSS
    from weasyprint.text.fonts import FontConfiguration
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False
    HTML = None
    CSS = None
    FontConfiguration = None

try:
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False
    Environment = None
    FileSystemLoader = None

try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    import numpy as np
    from sklearn.cluster import KMeans
    from sklearn.decomposition import PCA
    import pandas as pd
    VISUALIZATION_AVAILABLE = True
except ImportError:
    VISUALIZATION_AVAILABLE = False
    plt = None
    sns = None
    np = None
    KMeans = None
    PCA = None
    pd = None

from ..config.settings import settings
from ..utils import logger, ReportError, TemplateError
from ..services.analysis_service import analysis_service

@dataclass
class ReportConfig:
    """
    Configuration for report generation.
    
    Attributes:
        report_format: Output format (pdf, html, json)
        template_name: Name of template to use
        include_logo: Whether to include organization logos
        include_clustering: Whether to include clustering analysis
        include_detailed_analysis: Whether to include detailed section analysis
        custom_styling: Custom CSS styling
        branding_options: Branding configuration
        page_size: PDF page size (A4, Letter, etc.)
        orientation: Page orientation (portrait, landscape)
    """
    report_format: str = "pdf"
    template_name: str = "compliance_report"
    include_logo: bool = True
    include_clustering: bool = True
    include_detailed_analysis: bool = True
    custom_styling: Optional[str] = None
    branding_options: Optional[Dict[str, Any]] = None
    page_size: str = "A4"
    orientation: str = "portrait"

@dataclass
class ReportData:
    """
    Data structure for report generation.
    
    Attributes:
        analysis_results: List of analysis results to include
        title: Report title
        subtitle: Report subtitle  
        author: Report author
        organization: Organization name
        generated_at: When report was generated
        summary_stats: Summary statistics
        clustering_data: Clustering analysis data
        custom_sections: Additional custom sections
        metadata: Additional report metadata
    """
    analysis_results: List[Any]
    title: str = "Protocol Compliance Analysis Report"
    subtitle: str = "Pharmaceutical Standards Compliance"
    author: str = "GUARDIAN Analysis System"
    organization: str = "Queen Mary University of London"
    generated_at: Optional[datetime] = None
    summary_stats: Optional[Dict[str, Any]] = None
    clustering_data: Optional[Dict[str, Any]] = None
    custom_sections: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class ReportResult:
    """
    Result of report generation.
    
    Attributes:
        report_id: Unique identifier for the report
        file_path: Path to generated report file
        file_size: Size of generated file in bytes
        format: Report format
        generation_time: Time taken to generate report
        template_used: Template that was used
        pages: Number of pages (for PDF reports)
        metadata: Additional result metadata
        error: Error message if generation failed
    """
    report_id: str
    file_path: str
    file_size: int
    format: str
    generation_time: float
    template_used: str
    pages: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class ReportService:
    """
    Service for generating compliance analysis reports.
    
    Handles PDF generation, template rendering, clustering analysis,
    and report customization for the GUARDIAN system.
    """
    
    def __init__(self):
        """Initialize the report service."""
        self.reports_dir = Path(settings.report.storage_dir)
        self.templates_dir = Path(__file__).parent.parent / "templates"
        self.static_dir = Path(__file__).parent.parent / "static"
        
        # Create directories if they don't exist
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.static_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize Jinja2 environment
        if JINJA2_AVAILABLE:
            self.jinja_env = Environment(
                loader=FileSystemLoader(str(self.templates_dir)),
                autoescape=select_autoescape(['html', 'xml'])
            )
        else:
            self.jinja_env = None
            logger.warning("Jinja2 not available - HTML template rendering disabled")
        
        # Check dependencies
        self._check_dependencies()
        
        logger.info("Report service initialized", 
                   reports_dir=str(self.reports_dir),
                   templates_dir=str(self.templates_dir))
    
    def _check_dependencies(self) -> None:
        """Check if required dependencies are available."""
        missing_deps = []
        
        if not WEASYPRINT_AVAILABLE:
            missing_deps.append("weasyprint")
        if not JINJA2_AVAILABLE:
            missing_deps.append("jinja2")
        if not VISUALIZATION_AVAILABLE:
            missing_deps.append("matplotlib, seaborn, scikit-learn, pandas")
        
        if missing_deps:
            logger.warning(
                f"Some report dependencies are missing: {missing_deps}. "
                "Install with: pip install weasyprint jinja2 matplotlib seaborn scikit-learn pandas"
            )
    
    def generate_report(self,
                       analysis_results: List[Any],
                       config: ReportConfig = None,
                       report_data: ReportData = None) -> ReportResult:
        """
        Generate a compliance analysis report.
        
        Args:
            analysis_results: List of analysis results to include
            config: Report configuration options
            report_data: Additional report data and metadata
            
        Returns:
            ReportResult with generation details
            
        Raises:
            ReportError: If report generation fails
            TemplateError: If template is not found
        """
        start_time = time.time()
        
        # Use defaults if not provided
        if config is None:
            config = ReportConfig()
        if report_data is None:
            report_data = ReportData(analysis_results=analysis_results)
        else:
            report_data.analysis_results = analysis_results
        
        # Set generation timestamp
        if report_data.generated_at is None:
            report_data.generated_at = datetime.utcnow()
        
        logger.info(
            "Starting report generation",
            format=config.report_format,
            template=config.template_name,
            num_analyses=len(analysis_results),
            include_clustering=config.include_clustering
        )
        
        try:
            # Generate report ID
            report_id = f"report_{int(time.time() * 1000)}_{str(uuid.uuid4())[:8]}"
            
            # Prepare report data
            enriched_data = self._prepare_report_data(report_data, config)
            
            # Generate clustering analysis if requested
            if config.include_clustering and VISUALIZATION_AVAILABLE:
                clustering_data = self._generate_clustering_analysis(analysis_results)
                enriched_data['clustering_data'] = clustering_data
            
            # Generate report based on format
            if config.report_format.lower() == "pdf":
                result = self._generate_pdf_report(report_id, enriched_data, config)
            elif config.report_format.lower() == "html":
                result = self._generate_html_report(report_id, enriched_data, config)
            elif config.report_format.lower() == "json":
                result = self._generate_json_report(report_id, enriched_data, config)
            else:
                raise ReportError(f"Unsupported report format: {config.report_format}")
            
            generation_time = time.time() - start_time
            result.generation_time = generation_time
            
            logger.info(
                "Report generated successfully",
                report_id=report_id,
                format=config.report_format,
                file_size=result.file_size,
                generation_time=generation_time
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Report generation failed: {str(e)}", exception=e)
            raise ReportError(f"Failed to generate report: {str(e)}")
    
    def _prepare_report_data(self, report_data: ReportData, config: ReportConfig) -> Dict[str, Any]:
        """
        Prepare and enrich report data for template rendering.
        
        Args:
            report_data: Base report data
            config: Report configuration
            
        Returns:
            Enriched data dictionary for template rendering
        """
        # Convert dataclass to dict
        data = asdict(report_data)
        
        # Add configuration
        data['config'] = asdict(config)
        
        # Generate summary statistics
        if report_data.summary_stats is None:
            data['summary_stats'] = self._calculate_summary_stats(report_data.analysis_results)
        
        # Add branding information
        data['branding'] = self._get_branding_info(config.branding_options)
        
        # Add current timestamp
        data['current_time'] = datetime.utcnow()
        
        # Process analysis results for better template rendering
        data['processed_results'] = self._process_analysis_results(report_data.analysis_results)
        
        return data
    
    def _calculate_summary_stats(self, analysis_results: List[Any]) -> Dict[str, Any]:
        """
        Calculate summary statistics from analysis results.
        
        Args:
            analysis_results: List of analysis results
            
        Returns:
            Dictionary of summary statistics
        """
        if not analysis_results:
            return {
                'total_analyses': 0,
                'avg_compliance_score': 0.0,
                'compliance_distribution': {},
                'avg_processing_time': 0.0,
                'total_issues': 0,
                'common_issues': []
            }
        
        compliance_scores = []
        compliance_statuses = []
        processing_times = []
        all_issues = []
        
        for result in analysis_results:
            if hasattr(result, 'compliance_analysis'):
                compliance_scores.append(result.compliance_analysis.compliance_score)
                compliance_statuses.append(result.compliance_analysis.compliance_status)
                if hasattr(result.compliance_analysis, 'issues'):
                    all_issues.extend(result.compliance_analysis.issues or [])
            
            if hasattr(result, 'processing_time'):
                processing_times.append(result.processing_time)
        
        # Calculate distributions
        status_counts = {}
        for status in compliance_statuses:
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Find common issues (simplified)
        issue_counts = {}
        for issue in all_issues:
            issue_text = str(issue) if not isinstance(issue, str) else issue
            issue_counts[issue_text] = issue_counts.get(issue_text, 0) + 1
        
        common_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'total_analyses': len(analysis_results),
            'avg_compliance_score': sum(compliance_scores) / len(compliance_scores) if compliance_scores else 0.0,
            'compliance_distribution': status_counts,
            'avg_processing_time': sum(processing_times) / len(processing_times) if processing_times else 0.0,
            'total_issues': len(all_issues),
            'common_issues': [{'issue': issue, 'count': count} for issue, count in common_issues]
        }
    
    def _get_branding_info(self, branding_options: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get branding information for report generation.
        
        Args:
            branding_options: Custom branding options
            
        Returns:
            Branding information dictionary
        """
        default_branding = {
            'primary_logo': 'qmul_logo.png',
            'secondary_logo': 'ucb_logo.png',
            'primary_color': '#003f5c',
            'secondary_color': '#d62728',
            'accent_color': '#ff7f0e',
            'font_family': 'Arial, sans-serif',
            'organization_name': 'Queen Mary University of London',
            'department': 'School of Biological and Chemical Sciences'
        }
        
        if branding_options:
            default_branding.update(branding_options)
        
        return default_branding
    
    def _process_analysis_results(self, analysis_results: List[Any]) -> List[Dict[str, Any]]:
        """
        Process analysis results for better template rendering.
        
        Args:
            analysis_results: Raw analysis results
            
        Returns:
            Processed results for template rendering
        """
        processed = []
        
        for i, result in enumerate(analysis_results, 1):
            processed_result = {
                'index': i,
                'analysis_id': getattr(result, 'analysis_id', f'analysis_{i}'),
                'protocol_title': '',
                'compliance_score': 0.0,
                'compliance_status': 'unknown',
                'processing_time': 0.0,
                'num_issues': 0,
                'similar_sections_count': 0,
                'timestamp': datetime.utcnow()
            }
            
            # Extract protocol information
            if hasattr(result, 'protocol_input'):
                processed_result['protocol_title'] = getattr(result.protocol_input, 'protocol_title', '')
                processed_result['protocol_type'] = getattr(result.protocol_input, 'protocol_type', '')
            
            # Extract compliance information
            if hasattr(result, 'compliance_analysis'):
                processed_result['compliance_score'] = getattr(result.compliance_analysis, 'compliance_score', 0.0)
                processed_result['compliance_status'] = getattr(result.compliance_analysis, 'compliance_status', 'unknown')
                processed_result['num_issues'] = len(getattr(result.compliance_analysis, 'issues', []))
                processed_result['recommendations'] = getattr(result.compliance_analysis, 'recommendations', [])
            
            # Extract other metadata
            processed_result['processing_time'] = getattr(result, 'processing_time', 0.0)
            processed_result['timestamp'] = getattr(result, 'timestamp', datetime.utcnow())
            
            if hasattr(result, 'similar_sections'):
                processed_result['similar_sections_count'] = len(result.similar_sections or [])
                processed_result['similar_sections'] = result.similar_sections
            
            processed.append(processed_result)
        
        return processed
    
    def _generate_clustering_analysis(self, analysis_results: List[Any]) -> Dict[str, Any]:
        """
        Generate clustering analysis and visualization data.
        
        Args:
            analysis_results: Analysis results to cluster
            
        Returns:
            Clustering analysis data
            
        Raises:
            ReportError: If clustering analysis fails
        """
        if not VISUALIZATION_AVAILABLE:
            logger.warning("Visualization libraries not available - skipping clustering analysis")
            return {}
        
        try:
            # Extract features for clustering
            features = []
            labels = []
            
            for result in analysis_results:
                if hasattr(result, 'compliance_analysis'):
                    # Use compliance score and other metrics as features
                    feature_vector = [
                        getattr(result.compliance_analysis, 'compliance_score', 0.0),
                        getattr(result.compliance_analysis, 'confidence_score', 0.0),
                        len(getattr(result.compliance_analysis, 'issues', [])),
                        len(getattr(result.compliance_analysis, 'recommendations', [])),
                        getattr(result, 'processing_time', 0.0)
                    ]
                    features.append(feature_vector)
                    
                    protocol_title = ''
                    if hasattr(result, 'protocol_input'):
                        protocol_title = getattr(result.protocol_input, 'protocol_title', f'Protocol {len(features)}')
                    labels.append(protocol_title)
            
            if len(features) < 2:
                return {'message': 'Insufficient data for clustering analysis'}
            
            # Convert to numpy array
            X = np.array(features)
            
            # Normalize features
            from sklearn.preprocessing import StandardScaler
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # Perform K-means clustering
            n_clusters = min(3, len(features) // 2 + 1)
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(X_scaled)
            
            # Perform PCA for visualization
            pca = PCA(n_components=2)
            X_pca = pca.fit_transform(X_scaled)
            
            # Generate visualization
            viz_path = self._create_clustering_visualization(X_pca, cluster_labels, labels)
            
            # Calculate cluster statistics
            cluster_stats = []
            for i in range(n_clusters):
                cluster_mask = cluster_labels == i
                cluster_protocols = [labels[j] for j in range(len(labels)) if cluster_mask[j]]
                cluster_features = X[cluster_mask]
                
                if len(cluster_features) > 0:
                    cluster_stats.append({
                        'cluster_id': i,
                        'size': len(cluster_protocols),
                        'protocols': cluster_protocols,
                        'avg_compliance_score': float(np.mean(cluster_features[:, 0])),
                        'avg_confidence_score': float(np.mean(cluster_features[:, 1])),
                        'avg_issues': float(np.mean(cluster_features[:, 2])),
                        'characteristics': self._describe_cluster_characteristics(cluster_features)
                    })
            
            return {
                'n_clusters': n_clusters,
                'cluster_stats': cluster_stats,
                'visualization_path': viz_path,
                'pca_explained_variance': pca.explained_variance_ratio_.tolist(),
                'feature_names': ['Compliance Score', 'Confidence Score', 'Issues Count', 'Recommendations Count', 'Processing Time']
            }
            
        except Exception as e:
            logger.error(f"Clustering analysis failed: {str(e)}", exception=e)
            raise ReportError(f"Failed to generate clustering analysis: {str(e)}")
    
    def _create_clustering_visualization(self, X_pca: np.ndarray, cluster_labels: np.ndarray, labels: List[str]) -> str:
        """
        Create clustering visualization plot.
        
        Args:
            X_pca: PCA-transformed data points
            cluster_labels: Cluster assignments
            labels: Protocol labels
            
        Returns:
            Path to generated visualization image
        """
        plt.figure(figsize=(12, 8))
        
        # Set up the plot style
        plt.style.use('seaborn-v0_8')
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b']
        
        # Create scatter plot
        unique_labels = np.unique(cluster_labels)
        for i, cluster_id in enumerate(unique_labels):
            cluster_mask = cluster_labels == cluster_id
            plt.scatter(
                X_pca[cluster_mask, 0], 
                X_pca[cluster_mask, 1],
                c=colors[i % len(colors)],
                label=f'Cluster {cluster_id}',
                alpha=0.7,
                s=100
            )
        
        # Add labels for points
        for i, (x, y) in enumerate(X_pca):
            plt.annotate(
                labels[i][:20] + ('...' if len(labels[i]) > 20 else ''),
                (x, y),
                xytext=(5, 5),
                textcoords='offset points',
                fontsize=8,
                alpha=0.8
            )
        
        plt.xlabel('First Principal Component')
        plt.ylabel('Second Principal Component')
        plt.title('Protocol Clustering Analysis\nBased on Compliance Metrics')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        # Save visualization
        viz_filename = f"clustering_analysis_{int(time.time())}.png"
        viz_path = self.reports_dir / viz_filename
        plt.savefig(viz_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return str(viz_path)
    
    def _describe_cluster_characteristics(self, cluster_features: np.ndarray) -> List[str]:
        """
        Describe characteristics of a cluster based on its features.
        
        Args:
            cluster_features: Feature matrix for the cluster
            
        Returns:
            List of characteristic descriptions
        """
        characteristics = []
        
        if len(cluster_features) == 0:
            return characteristics
        
        means = np.mean(cluster_features, axis=0)
        
        # Compliance score characteristics
        if means[0] > 0.8:
            characteristics.append("High compliance scores")
        elif means[0] < 0.5:
            characteristics.append("Low compliance scores")
        else:
            characteristics.append("Moderate compliance scores")
        
        # Issues characteristics
        if means[2] > 5:
            characteristics.append("High number of issues")
        elif means[2] < 2:
            characteristics.append("Few issues identified")
        
        # Processing time characteristics
        if means[4] > 10:
            characteristics.append("Longer processing times")
        elif means[4] < 3:
            characteristics.append("Quick to analyze")
        
        return characteristics
    
    def _generate_pdf_report(self, report_id: str, data: Dict[str, Any], config: ReportConfig) -> ReportResult:
        """
        Generate PDF report using WeasyPrint.
        
        Args:
            report_id: Unique report identifier
            data: Report data
            config: Report configuration
            
        Returns:
            ReportResult for PDF generation
            
        Raises:
            ReportError: If PDF generation fails
        """
        if not WEASYPRINT_AVAILABLE:
            raise ReportError("WeasyPrint not available - cannot generate PDF reports")
        
        # First generate HTML content
        html_content = self._render_html_template(data, config)
        
        # Generate PDF filename
        pdf_filename = f"{report_id}.pdf"
        pdf_path = self.reports_dir / pdf_filename
        
        try:
            # Create WeasyPrint HTML object
            html_doc = HTML(string=html_content, base_url=str(self.templates_dir))
            
            # Load custom CSS if provided
            css_objects = []
            if config.custom_styling:
                css_objects.append(CSS(string=config.custom_styling))
            
            # Add default styling
            default_css_path = self.static_dir / "css" / "report.css"
            if default_css_path.exists():
                css_objects.append(CSS(filename=str(default_css_path)))
            
            # Generate PDF
            html_doc.write_pdf(
                str(pdf_path),
                stylesheets=css_objects,
                font_config=FontConfiguration() if FontConfiguration else None
            )
            
            # Get file info
            file_size = pdf_path.stat().st_size
            
            # Count pages (approximate)
            pages = self._estimate_pdf_pages(html_content)
            
            return ReportResult(
                report_id=report_id,
                file_path=str(pdf_path),
                file_size=file_size,
                format="pdf",
                generation_time=0.0,  # Will be set by caller
                template_used=config.template_name,
                pages=pages,
                metadata={'config': asdict(config)}
            )
            
        except Exception as e:
            logger.error(f"PDF generation failed: {str(e)}", exception=e)
            raise ReportError(f"Failed to generate PDF: {str(e)}")
    
    def _generate_html_report(self, report_id: str, data: Dict[str, Any], config: ReportConfig) -> ReportResult:
        """
        Generate HTML report.
        
        Args:
            report_id: Unique report identifier
            data: Report data
            config: Report configuration
            
        Returns:
            ReportResult for HTML generation
        """
        # Generate HTML content
        html_content = self._render_html_template(data, config)
        
        # Generate HTML filename
        html_filename = f"{report_id}.html"
        html_path = self.reports_dir / html_filename
        
        # Write HTML file
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Get file info
        file_size = html_path.stat().st_size
        
        return ReportResult(
            report_id=report_id,
            file_path=str(html_path),
            file_size=file_size,
            format="html",
            generation_time=0.0,  # Will be set by caller
            template_used=config.template_name,
            metadata={'config': asdict(config)}
        )
    
    def _generate_json_report(self, report_id: str, data: Dict[str, Any], config: ReportConfig) -> ReportResult:
        """
        Generate JSON report.
        
        Args:
            report_id: Unique report identifier
            data: Report data
            config: Report configuration
            
        Returns:
            ReportResult for JSON generation
        """
        # Generate JSON filename
        json_filename = f"{report_id}.json"
        json_path = self.reports_dir / json_filename
        
        # Prepare JSON data (remove non-serializable objects)
        json_data = self._prepare_json_data(data)
        
        # Write JSON file
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, default=str)
        
        # Get file info
        file_size = json_path.stat().st_size
        
        return ReportResult(
            report_id=report_id,
            file_path=str(json_path),
            file_size=file_size,
            format="json",
            generation_time=0.0,  # Will be set by caller
            template_used="json_export",
            metadata={'config': asdict(config)}
        )
    
    def _render_html_template(self, data: Dict[str, Any], config: ReportConfig) -> str:
        """
        Render HTML template with data.
        
        Args:
            data: Template data
            config: Report configuration
            
        Returns:
            Rendered HTML content
            
        Raises:
            TemplateError: If template is not found
        """
        if not self.jinja_env:
            # Fallback to basic HTML generation
            return self._generate_basic_html(data, config)
        
        template_name = f"{config.template_name}.html"
        
        try:
            template = self.jinja_env.get_template(template_name)
            return template.render(**data)
        except Exception as e:
            logger.warning(f"Template '{template_name}' not found or failed to render: {str(e)}")
            # Fallback to basic HTML generation
            return self._generate_basic_html(data, config)
    
    def _generate_basic_html(self, data: Dict[str, Any], config: ReportConfig) -> str:
        """
        Generate basic HTML report when templates are not available.
        
        Args:
            data: Report data
            config: Report configuration
            
        Returns:
            Basic HTML content
        """
        html_parts = [
            "<!DOCTYPE html>",
            "<html lang='en'>",
            "<head>",
            "<meta charset='UTF-8'>",
            "<meta name='viewport' content='width=device-width, initial-scale=1.0'>",
            f"<title>{data.get('title', 'Protocol Compliance Report')}</title>",
            "<style>",
            self._get_basic_css(),
            "</style>",
            "</head>",
            "<body>",
            "<div class='container'>",
            f"<h1>{data.get('title', 'Protocol Compliance Report')}</h1>",
            f"<h2>{data.get('subtitle', '')}</h2>",
            f"<p><strong>Generated:</strong> {data.get('current_time', datetime.utcnow()).strftime('%Y-%m-%d %H:%M:%S')}</p>",
            f"<p><strong>Author:</strong> {data.get('author', 'GUARDIAN System')}</p>",
            f"<p><strong>Organization:</strong> {data.get('organization', 'Queen Mary University of London')}</p>",
            "<hr>",
        ]
        
        # Add summary statistics
        if data.get('summary_stats'):
            stats = data['summary_stats']
            html_parts.extend([
                "<h3>Summary Statistics</h3>",
                "<div class='stats-grid'>",
                f"<div class='stat-card'><h4>{stats.get('total_analyses', 0)}</h4><p>Total Analyses</p></div>",
                f"<div class='stat-card'><h4>{stats.get('avg_compliance_score', 0):.2f}</h4><p>Average Compliance Score</p></div>",
                f"<div class='stat-card'><h4>{stats.get('total_issues', 0)}</h4><p>Total Issues</p></div>",
                f"<div class='stat-card'><h4>{stats.get('avg_processing_time', 0):.2f}s</h4><p>Average Processing Time</p></div>",
                "</div>",
                "<br>"
            ])
        
        # Add analysis results
        if data.get('processed_results'):
            html_parts.extend([
                "<h3>Analysis Results</h3>",
                "<div class='results-container'>"
            ])
            
            for result in data['processed_results']:
                status_class = result.get('compliance_status', '').lower().replace(' ', '-')
                html_parts.extend([
                    f"<div class='result-card {status_class}'>",
                    f"<h4>{result.get('protocol_title', 'Untitled Protocol')}</h4>",
                    f"<p><strong>Compliance Score:</strong> {result.get('compliance_score', 0):.2f}</p>",
                    f"<p><strong>Status:</strong> {result.get('compliance_status', 'Unknown')}</p>",
                    f"<p><strong>Issues:</strong> {result.get('num_issues', 0)}</p>",
                    f"<p><strong>Processing Time:</strong> {result.get('processing_time', 0):.2f}s</p>",
                    "</div>"
                ])
            
            html_parts.append("</div>")
        
        # Add clustering visualization if available
        if data.get('clustering_data') and data['clustering_data'].get('visualization_path'):
            try:
                # Convert image to base64 for embedding
                with open(data['clustering_data']['visualization_path'], 'rb') as img_file:
                    img_data = base64.b64encode(img_file.read()).decode()
                    html_parts.extend([
                        "<h3>Clustering Analysis</h3>",
                        f"<img src='data:image/png;base64,{img_data}' alt='Clustering Analysis' style='max-width: 100%; height: auto;'>",
                        "<br><br>"
                    ])
            except Exception as e:
                logger.warning(f"Failed to embed clustering visualization: {str(e)}")
        
        html_parts.extend([
            "</div>",
            "</body>",
            "</html>"
        ])
        
        return "\n".join(html_parts)
    
    def _get_basic_css(self) -> str:
        """Get basic CSS styling for HTML reports."""
        return """
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1, h2, h3, h4 {
            color: #003f5c;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .stat-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            border-left: 4px solid #003f5c;
        }
        .stat-card h4 {
            font-size: 2em;
            margin: 0;
            color: #003f5c;
        }
        .stat-card p {
            margin: 5px 0 0 0;
            color: #666;
        }
        .results-container {
            display: grid;
            gap: 20px;
            margin: 20px 0;
        }
        .result-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #28a745;
        }
        .result-card.non-compliant {
            border-left-color: #dc3545;
        }
        .result-card.partially-compliant {
            border-left-color: #ffc107;
        }
        hr {
            border: none;
            height: 1px;
            background: #ddd;
            margin: 20px 0;
        }
        """
    
    def _prepare_json_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare data for JSON serialization by removing non-serializable objects.
        
        Args:
            data: Raw data dictionary
            
        Returns:
            JSON-serializable data dictionary
        """
        json_data = {}
        
        for key, value in data.items():
            if key == 'clustering_data' and isinstance(value, dict):
                # Clean clustering data
                cleaned_clustering = {}
                for k, v in value.items():
                    if k != 'visualization_path':  # Skip file paths
                        cleaned_clustering[k] = v
                json_data[key] = cleaned_clustering
            elif isinstance(value, (str, int, float, bool, list, dict)):
                json_data[key] = value
            elif hasattr(value, '__dict__'):
                # Convert objects to dictionaries
                json_data[key] = asdict(value) if hasattr(value, '__dataclass_fields__') else str(value)
            else:
                json_data[key] = str(value)
        
        return json_data
    
    def _estimate_pdf_pages(self, html_content: str) -> int:
        """
        Estimate number of pages in PDF based on HTML content.
        
        Args:
            html_content: HTML content
            
        Returns:
            Estimated number of pages
        """
        # Very rough estimation based on content length
        # This is a simplified approach - in practice, you'd need more sophisticated analysis
        content_length = len(html_content)
        estimated_pages = max(1, content_length // 5000)  # Rough estimate
        return estimated_pages
    
    def get_report(self, report_id: str) -> Optional[ReportResult]:
        """
        Get report information by ID.
        
        Args:
            report_id: Report identifier
            
        Returns:
            ReportResult if found, None otherwise
        """
        # Look for report files with this ID
        for format_ext in ['pdf', 'html', 'json']:
            report_path = self.reports_dir / f"{report_id}.{format_ext}"
            if report_path.exists():
                file_size = report_path.stat().st_size
                return ReportResult(
                    report_id=report_id,
                    file_path=str(report_path),
                    file_size=file_size,
                    format=format_ext,
                    generation_time=0.0,
                    template_used="unknown"
                )
        
        return None
    
    def list_reports(self, limit: int = 50) -> List[ReportResult]:
        """
        List generated reports.
        
        Args:
            limit: Maximum number of reports to return
            
        Returns:
            List of ReportResult objects
        """
        reports = []
        
        # Scan reports directory
        for report_file in self.reports_dir.glob("report_*.pdf"):
            report_id = report_file.stem
            file_size = report_file.stat().st_size
            
            report_result = ReportResult(
                report_id=report_id,
                file_path=str(report_file),
                file_size=file_size,
                format="pdf",
                generation_time=0.0,
                template_used="unknown"
            )
            reports.append(report_result)
        
        # Sort by creation time (newest first)
        reports.sort(key=lambda x: Path(x.file_path).stat().st_mtime, reverse=True)
        
        return reports[:limit]
    
    def delete_report(self, report_id: str) -> bool:
        """
        Delete a report and its files.
        
        Args:
            report_id: Report identifier
            
        Returns:
            True if deleted successfully, False otherwise
        """
        deleted = False
        
        # Delete all formats of the report
        for format_ext in ['pdf', 'html', 'json']:
            report_path = self.reports_dir / f"{report_id}.{format_ext}"
            if report_path.exists():
                try:
                    report_path.unlink()
                    deleted = True
                    logger.info(f"Deleted report file: {report_path}")
                except Exception as e:
                    logger.error(f"Failed to delete report file {report_path}: {str(e)}")
        
        # Delete associated visualization files
        for viz_file in self.reports_dir.glob(f"clustering_analysis_*.png"):
            # This is a simplified approach - in production you'd need better tracking
            try:
                viz_file.unlink()
            except Exception:
                pass
        
        return deleted

# Create global instance
report_service = ReportService()