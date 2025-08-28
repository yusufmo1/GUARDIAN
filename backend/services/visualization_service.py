"""
Visualization Service

Advanced visualization and clustering analysis service for the GUARDIAN system.
Provides statistical analysis, clustering, dimensionality reduction, and 
interactive visualizations for protocol compliance analysis.

Features:
- K-means clustering analysis
- Principal Component Analysis (PCA) 
- t-SNE dimensionality reduction
- Statistical distribution analysis
- Interactive plotting with Plotly
- Matplotlib static visualizations
- Protocol similarity networks
- Compliance trend analysis
"""
import os
import time
import json
import uuid
from typing import Dict, List, Any, Optional, Tuple, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import io
import base64

try:
    import numpy as np
    import pandas as pd
    from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
    from sklearn.decomposition import PCA
    from sklearn.manifold import TSNE
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import silhouette_score, calinski_harabasz_score
    from sklearn.neighbors import NearestNeighbors
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    np = None
    pd = None
    KMeans = None
    DBSCAN = None
    AgglomerativeClustering = None
    PCA = None
    TSNE = None
    StandardScaler = None

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    import seaborn as sns
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    plt = None
    sns = None

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    import plotly.offline as pyo
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    go = None
    px = None
    make_subplots = None
    pyo = None

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False
    nx = None

from ..config.settings import settings
from ..utils import logger, ReportError

@dataclass
class ClusteringConfig:
    """
    Configuration for clustering analysis.
    
    Attributes:
        algorithm: Clustering algorithm ('kmeans', 'dbscan', 'hierarchical')
        n_clusters: Number of clusters (for k-means and hierarchical)
        min_samples: Minimum samples per cluster (for DBSCAN)
        eps: Epsilon parameter for DBSCAN
        random_state: Random state for reproducibility
        normalize_features: Whether to normalize features
        feature_weights: Weights for different features
    """
    algorithm: str = "kmeans"
    n_clusters: Optional[int] = None
    min_samples: int = 5
    eps: float = 0.5
    random_state: int = 42
    normalize_features: bool = True
    feature_weights: Optional[Dict[str, float]] = None

@dataclass
class VisualizationConfig:
    """
    Configuration for visualization generation.
    
    Attributes:
        plot_type: Type of visualization ('scatter', 'heatmap', 'network', 'trends')
        color_scheme: Color scheme to use
        figure_size: Figure size (width, height)
        dpi: Resolution for static plots
        interactive: Whether to create interactive plots
        save_format: Format to save plots ('png', 'svg', 'html', 'json')
        theme: Visual theme ('light', 'dark', 'academic')
    """
    plot_type: str = "scatter"
    color_scheme: str = "viridis"
    figure_size: Tuple[int, int] = (12, 8)
    dpi: int = 300
    interactive: bool = False
    save_format: str = "png"
    theme: str = "light"

@dataclass
class ClusteringResult:
    """
    Result of clustering analysis.
    
    Attributes:
        cluster_labels: Array of cluster assignments
        cluster_centers: Cluster centers (if applicable)
        n_clusters: Number of clusters found
        silhouette_score: Silhouette score for clustering quality
        inertia: Within-cluster sum of squares (for k-means)
        algorithm_params: Parameters used for clustering
        feature_importance: Importance of each feature
        cluster_stats: Statistics for each cluster
        outliers: Indices of outlier data points
    """
    cluster_labels: List[int]
    cluster_centers: Optional[List[List[float]]] = None
    n_clusters: int = 0
    silhouette_score: float = 0.0
    inertia: float = 0.0
    algorithm_params: Optional[Dict[str, Any]] = None
    feature_importance: Optional[Dict[str, float]] = None
    cluster_stats: Optional[List[Dict[str, Any]]] = None
    outliers: Optional[List[int]] = None

@dataclass
class VisualizationResult:
    """
    Result of visualization generation.
    
    Attributes:
        visualization_id: Unique identifier
        file_path: Path to generated visualization
        file_size: Size of generated file
        format: File format
        plot_type: Type of visualization
        interactive: Whether plot is interactive
        generation_time: Time taken to generate
        metadata: Additional metadata
    """
    visualization_id: str
    file_path: str
    file_size: int
    format: str
    plot_type: str
    interactive: bool
    generation_time: float
    metadata: Optional[Dict[str, Any]] = None

class VisualizationService:
    """
    Service for advanced visualization and clustering analysis.
    
    Provides statistical analysis, clustering, and visualization capabilities
    for protocol compliance analysis in the GUARDIAN system.
    """
    
    def __init__(self):
        """Initialize the visualization service."""
        self.visualizations_dir = Path(settings.report.storage_dir) / "visualizations"
        self.visualizations_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up plotting styles
        self._setup_plotting_styles()
        
        # Check dependencies
        self._check_dependencies()
        
        logger.info("Visualization service initialized", 
                   visualizations_dir=str(self.visualizations_dir))
    
    def _check_dependencies(self) -> None:
        """Check if required dependencies are available."""
        missing_deps = []
        
        if not SKLEARN_AVAILABLE:
            missing_deps.append("scikit-learn")
        if not MATPLOTLIB_AVAILABLE:
            missing_deps.append("matplotlib, seaborn")
        if not PLOTLY_AVAILABLE:
            missing_deps.append("plotly")
        if not NETWORKX_AVAILABLE:
            missing_deps.append("networkx")
        
        if missing_deps:
            logger.warning(
                f"Some visualization dependencies are missing: {missing_deps}. "
                f"Install with: pip install scikit-learn matplotlib seaborn plotly networkx"
            )
    
    def _setup_plotting_styles(self) -> None:
        """Set up default plotting styles."""
        if MATPLOTLIB_AVAILABLE:
            # Set seaborn style if available
            try:
                sns.set_style("whitegrid")
                sns.set_palette("husl")
            except:
                pass
            
            # Set matplotlib defaults
            plt.rcParams.update({
                'figure.figsize': (12, 8),
                'figure.dpi': 100,
                'savefig.dpi': 300,
                'font.size': 12,
                'axes.titlesize': 14,
                'axes.labelsize': 12,
                'xtick.labelsize': 10,
                'ytick.labelsize': 10,
                'legend.fontsize': 10,
                'figure.titlesize': 16
            })
    
    def analyze_clusters(self,
                        analysis_results: List[Any],
                        config: ClusteringConfig = None) -> ClusteringResult:
        """
        Perform clustering analysis on protocol analysis results.
        
        Args:
            analysis_results: List of analysis results to cluster
            config: Clustering configuration
            
        Returns:
            ClusteringResult with clustering information
            
        Raises:
            ReportError: If clustering analysis fails
            ReportError: If insufficient data for clustering
        """
        if not SKLEARN_AVAILABLE:
            raise ReportError("scikit-learn not available - clustering analysis disabled")
        
        if config is None:
            config = ClusteringConfig()
        
        logger.info(
            "Starting clustering analysis",
            algorithm=config.algorithm,
            n_samples=len(analysis_results),
            normalize=config.normalize_features
        )
        
        try:
            # Extract features for clustering
            features, labels, feature_names = self._extract_clustering_features(analysis_results)
            
            if len(features) < 2:
                raise ReportError("Insufficient data for clustering analysis")
            
            # Convert to numpy array
            X = np.array(features)
            
            # Apply feature weights if provided
            if config.feature_weights:
                weights = [config.feature_weights.get(name, 1.0) for name in feature_names]
                X = X * np.array(weights)
            
            # Normalize features if requested
            scaler = None
            if config.normalize_features:
                scaler = StandardScaler()
                X = scaler.fit_transform(X)
            
            # Determine optimal number of clusters if not specified
            if config.algorithm in ['kmeans', 'hierarchical'] and config.n_clusters is None:
                config.n_clusters = self._determine_optimal_clusters(X)
            
            # Perform clustering
            clustering_result = self._perform_clustering(X, config)
            
            # Calculate cluster statistics
            cluster_stats = self._calculate_cluster_statistics(
                X, clustering_result.cluster_labels, labels, feature_names
            )
            clustering_result.cluster_stats = cluster_stats
            
            # Calculate feature importance
            if len(feature_names) > 1:
                feature_importance = self._calculate_feature_importance(X, clustering_result.cluster_labels, feature_names)
                clustering_result.feature_importance = feature_importance
            
            # Store algorithm parameters
            clustering_result.algorithm_params = asdict(config)
            
            logger.info(
                "Clustering analysis completed",
                algorithm=config.algorithm,
                n_clusters=clustering_result.n_clusters,
                silhouette_score=clustering_result.silhouette_score
            )
            
            return clustering_result
            
        except Exception as e:
            logger.error(f"Clustering analysis failed: {str(e)}", exception=e)
            raise ReportError(f"Failed to perform clustering analysis: {str(e)}")
    
    def _extract_clustering_features(self, analysis_results: List[Any]) -> Tuple[List[List[float]], List[str], List[str]]:
        """
        Extract numerical features for clustering from analysis results.
        
        Args:
            analysis_results: List of analysis results
            
        Returns:
            Tuple of (features, labels, feature_names)
        """
        features = []
        labels = []
        feature_names = [
            'compliance_score',
            'confidence_score',
            'issues_count',
            'recommendations_count',
            'processing_time',
            'similar_sections_count',
            'text_length'
        ]
        
        for i, result in enumerate(analysis_results):
            try:
                # Extract compliance metrics
                compliance_score = 0.0
                confidence_score = 0.0
                issues_count = 0
                recommendations_count = 0
                
                if hasattr(result, 'compliance_analysis'):
                    compliance_score = getattr(result.compliance_analysis, 'compliance_score', 0.0)
                    confidence_score = getattr(result.compliance_analysis, 'confidence_score', 0.0)
                    issues_count = len(getattr(result.compliance_analysis, 'issues', []))
                    recommendations_count = len(getattr(result.compliance_analysis, 'recommendations', []))
                
                # Extract processing metrics
                processing_time = getattr(result, 'processing_time', 0.0)
                similar_sections_count = len(getattr(result, 'similar_sections', []))
                
                # Extract text length
                text_length = 0
                if hasattr(result, 'protocol_input') and hasattr(result.protocol_input, 'protocol_text'):
                    text_length = len(result.protocol_input.protocol_text)
                
                # Create feature vector
                feature_vector = [
                    compliance_score,
                    confidence_score,
                    issues_count,
                    recommendations_count,
                    processing_time,
                    similar_sections_count,
                    text_length / 1000.0  # Normalize text length
                ]
                
                features.append(feature_vector)
                
                # Create label
                protocol_title = f'Protocol {i+1}'
                if hasattr(result, 'protocol_input') and hasattr(result.protocol_input, 'protocol_title'):
                    protocol_title = result.protocol_input.protocol_title or protocol_title
                
                labels.append(protocol_title)
                
            except Exception as e:
                logger.warning(f"Failed to extract features from result {i}: {str(e)}")
                continue
        
        return features, labels, feature_names
    
    def _determine_optimal_clusters(self, X: np.ndarray) -> int:
        """
        Determine optimal number of clusters using elbow method and silhouette analysis.
        
        Args:
            X: Feature matrix
            
        Returns:
            Optimal number of clusters
        """
        if len(X) < 4:
            return 2
        
        max_clusters = min(8, len(X) // 2)
        silhouette_scores = []
        inertias = []
        
        for k in range(2, max_clusters + 1):
            try:
                kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
                cluster_labels = kmeans.fit_predict(X)
                
                # Calculate silhouette score
                if len(np.unique(cluster_labels)) > 1:
                    silhouette_avg = silhouette_score(X, cluster_labels)
                    silhouette_scores.append(silhouette_avg)
                    inertias.append(kmeans.inertia_)
                else:
                    silhouette_scores.append(-1)
                    inertias.append(float('inf'))
                    
            except Exception:
                silhouette_scores.append(-1)
                inertias.append(float('inf'))
        
        # Find optimal k using silhouette score
        if silhouette_scores:
            best_k = np.argmax(silhouette_scores) + 2
            return best_k
        
        return 3  # Default fallback
    
    def _perform_clustering(self, X: np.ndarray, config: ClusteringConfig) -> ClusteringResult:
        """
        Perform clustering using specified algorithm.
        
        Args:
            X: Feature matrix
            config: Clustering configuration
            
        Returns:
            ClusteringResult with clustering information
        """
        if config.algorithm == 'kmeans':
            clusterer = KMeans(
                n_clusters=config.n_clusters,
                random_state=config.random_state,
                n_init=10
            )
            cluster_labels = clusterer.fit_predict(X)
            cluster_centers = clusterer.cluster_centers_.tolist()
            inertia = clusterer.inertia_
            
        elif config.algorithm == 'dbscan':
            clusterer = DBSCAN(eps=config.eps, min_samples=config.min_samples)
            cluster_labels = clusterer.fit_predict(X)
            cluster_centers = None
            inertia = 0.0
            
        elif config.algorithm == 'hierarchical':
            clusterer = AgglomerativeClustering(n_clusters=config.n_clusters)
            cluster_labels = clusterer.fit_predict(X)
            cluster_centers = None
            inertia = 0.0
            
        else:
            raise ReportError(f"Unsupported clustering algorithm: {config.algorithm}")
        
        # Calculate clustering quality metrics
        n_clusters = len(np.unique(cluster_labels))
        if n_clusters > 1 and -1 not in cluster_labels:  # Valid clustering
            silhouette_avg = silhouette_score(X, cluster_labels)
        else:
            silhouette_avg = 0.0
        
        # Identify outliers (for DBSCAN)
        outliers = None
        if config.algorithm == 'dbscan':
            outliers = [i for i, label in enumerate(cluster_labels) if label == -1]
        
        return ClusteringResult(
            cluster_labels=cluster_labels.tolist(),
            cluster_centers=cluster_centers,
            n_clusters=n_clusters,
            silhouette_score=silhouette_avg,
            inertia=inertia,
            outliers=outliers
        )
    
    def _calculate_cluster_statistics(self,
                                    X: np.ndarray,
                                    cluster_labels: List[int],
                                    point_labels: List[str],
                                    feature_names: List[str]) -> List[Dict[str, Any]]:
        """
        Calculate statistics for each cluster.
        
        Args:
            X: Feature matrix
            cluster_labels: Cluster assignments
            point_labels: Labels for data points
            feature_names: Names of features
            
        Returns:
            List of cluster statistics
        """
        cluster_stats = []
        unique_clusters = np.unique(cluster_labels)
        
        for cluster_id in unique_clusters:
            if cluster_id == -1:  # Skip outliers
                continue
                
            cluster_mask = np.array(cluster_labels) == cluster_id
            cluster_data = X[cluster_mask]
            cluster_points = [point_labels[i] for i in range(len(point_labels)) if cluster_mask[i]]
            
            if len(cluster_data) == 0:
                continue
            
            # Calculate statistics
            stats = {
                'cluster_id': int(cluster_id),
                'size': len(cluster_data),
                'protocols': cluster_points[:10],  # Limit to first 10
                'feature_means': np.mean(cluster_data, axis=0).tolist(),
                'feature_stds': np.std(cluster_data, axis=0).tolist(),
                'feature_stats': {}
            }
            
            # Add named feature statistics
            for i, feature_name in enumerate(feature_names):
                stats['feature_stats'][feature_name] = {
                    'mean': float(np.mean(cluster_data[:, i])),
                    'std': float(np.std(cluster_data[:, i])),
                    'min': float(np.min(cluster_data[:, i])),
                    'max': float(np.max(cluster_data[:, i]))
                }
            
            # Add cluster characteristics
            stats['characteristics'] = self._describe_cluster_characteristics(cluster_data, feature_names)
            
            cluster_stats.append(stats)
        
        return cluster_stats
    
    def _describe_cluster_characteristics(self, cluster_data: np.ndarray, feature_names: List[str]) -> List[str]:
        """
        Describe characteristics of a cluster based on its features.
        
        Args:
            cluster_data: Feature data for the cluster
            feature_names: Names of features
            
        Returns:
            List of characteristic descriptions
        """
        characteristics = []
        
        if len(cluster_data) == 0:
            return characteristics
        
        means = np.mean(cluster_data, axis=0)
        
        # Compliance score characteristics
        if 'compliance_score' in feature_names:
            compliance_idx = feature_names.index('compliance_score')
            if means[compliance_idx] > 0.8:
                characteristics.append("High compliance scores")
            elif means[compliance_idx] < 0.5:
                characteristics.append("Low compliance scores")
            else:
                characteristics.append("Moderate compliance scores")
        
        # Issues characteristics
        if 'issues_count' in feature_names:
            issues_idx = feature_names.index('issues_count')
            if means[issues_idx] > 5:
                characteristics.append("High number of issues")
            elif means[issues_idx] < 2:
                characteristics.append("Few issues identified")
        
        # Processing time characteristics
        if 'processing_time' in feature_names:
            time_idx = feature_names.index('processing_time')
            if means[time_idx] > 10:
                characteristics.append("Longer processing times")
            elif means[time_idx] < 3:
                characteristics.append("Quick to analyze")
        
        # Text length characteristics
        if 'text_length' in feature_names:
            length_idx = feature_names.index('text_length')
            if means[length_idx] > 5:  # Remember it's normalized by 1000
                characteristics.append("Long protocols")
            elif means[length_idx] < 1:
                characteristics.append("Short protocols")
        
        return characteristics
    
    def _calculate_feature_importance(self,
                                    X: np.ndarray,
                                    cluster_labels: List[int],
                                    feature_names: List[str]) -> Dict[str, float]:
        """
        Calculate feature importance for clustering.
        
        Args:
            X: Feature matrix
            cluster_labels: Cluster assignments
            feature_names: Names of features
            
        Returns:
            Dictionary of feature importance scores
        """
        try:
            from sklearn.ensemble import RandomForestClassifier
            
            # Use random forest to estimate feature importance
            rf = RandomForestClassifier(n_estimators=100, random_state=42)
            rf.fit(X, cluster_labels)
            
            importance_scores = rf.feature_importances_
            
            return {
                feature_names[i]: float(importance_scores[i])
                for i in range(len(feature_names))
            }
            
        except Exception:
            # Fallback to variance-based importance
            variances = np.var(X, axis=0)
            total_variance = np.sum(variances)
            
            if total_variance > 0:
                return {
                    feature_names[i]: float(variances[i] / total_variance)
                    for i in range(len(feature_names))
                }
            else:
                return {name: 1.0 / len(feature_names) for name in feature_names}
    
    def create_clustering_visualization(self,
                                      analysis_results: List[Any],
                                      clustering_result: ClusteringResult,
                                      config: VisualizationConfig = None) -> VisualizationResult:
        """
        Create visualization for clustering results.
        
        Args:
            analysis_results: Original analysis results
            clustering_result: Results from clustering analysis
            config: Visualization configuration
            
        Returns:
            VisualizationResult with visualization details
            
        Raises:
            ReportError: If visualization creation fails
        """
        if config is None:
            config = VisualizationConfig()
        
        start_time = time.time()
        
        logger.info(
            "Creating clustering visualization",
            plot_type=config.plot_type,
            interactive=config.interactive,
            format=config.save_format
        )
        
        try:
            # Extract features for visualization
            features, labels, feature_names = self._extract_clustering_features(analysis_results)
            X = np.array(features)
            
            # Normalize features for visualization
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # Perform PCA for 2D visualization
            pca = PCA(n_components=2)
            X_pca = pca.fit_transform(X_scaled)
            
            # Generate visualization
            if config.interactive and PLOTLY_AVAILABLE:
                viz_result = self._create_interactive_clustering_plot(
                    X_pca, clustering_result.cluster_labels, labels, config
                )
            elif MATPLOTLIB_AVAILABLE:
                viz_result = self._create_static_clustering_plot(
                    X_pca, clustering_result.cluster_labels, labels, config
                )
            else:
                raise ReportError("No visualization libraries available")
            
            generation_time = time.time() - start_time
            viz_result.generation_time = generation_time
            
            # Add metadata
            viz_result.metadata = {
                'n_samples': len(features),
                'n_clusters': clustering_result.n_clusters,
                'silhouette_score': clustering_result.silhouette_score,
                'pca_explained_variance': pca.explained_variance_ratio_.tolist(),
                'feature_names': feature_names
            }
            
            logger.info(
                "Clustering visualization created",
                visualization_id=viz_result.visualization_id,
                file_size=viz_result.file_size,
                generation_time=generation_time
            )
            
            return viz_result
            
        except Exception as e:
            logger.error(f"Clustering visualization failed: {str(e)}", exception=e)
            raise ReportError(f"Failed to create clustering visualization: {str(e)}")
    
    def _create_interactive_clustering_plot(self,
                                          X_pca: np.ndarray,
                                          cluster_labels: List[int],
                                          point_labels: List[str],
                                          config: VisualizationConfig) -> VisualizationResult:
        """
        Create interactive clustering plot using Plotly.
        
        Args:
            X_pca: PCA-transformed data
            cluster_labels: Cluster assignments
            point_labels: Labels for data points
            config: Visualization configuration
            
        Returns:
            VisualizationResult
        """
        # Create DataFrame for plotting
        df = pd.DataFrame({
            'PC1': X_pca[:, 0],
            'PC2': X_pca[:, 1],
            'Cluster': [f'Cluster {label}' if label != -1 else 'Outlier' for label in cluster_labels],
            'Protocol': point_labels,
            'Cluster_ID': cluster_labels
        })
        
        # Create scatter plot
        fig = px.scatter(
            df, 
            x='PC1', 
            y='PC2',
            color='Cluster',
            hover_data=['Protocol'],
            title='Protocol Clustering Analysis',
            labels={
                'PC1': 'First Principal Component',
                'PC2': 'Second Principal Component'
            }
        )
        
        # Update layout
        fig.update_layout(
            width=config.figure_size[0] * 50,  # Convert to pixels
            height=config.figure_size[1] * 50,
            template='plotly_white' if config.theme == 'light' else 'plotly_dark'
        )
        
        # Save interactive plot
        viz_id = f"clustering_{int(time.time() * 1000)}_{str(uuid.uuid4())[:8]}"
        
        if config.save_format == 'html':
            file_path = self.visualizations_dir / f"{viz_id}.html"
            fig.write_html(str(file_path))
        else:
            # Save as JSON for later rendering
            file_path = self.visualizations_dir / f"{viz_id}.json"
            with open(file_path, 'w') as f:
                json.dump(fig.to_dict(), f)
        
        file_size = file_path.stat().st_size
        
        return VisualizationResult(
            visualization_id=viz_id,
            file_path=str(file_path),
            file_size=file_size,
            format=config.save_format,
            plot_type="interactive_clustering",
            interactive=True,
            generation_time=0.0
        )
    
    def _create_static_clustering_plot(self,
                                     X_pca: np.ndarray,
                                     cluster_labels: List[int],
                                     point_labels: List[str],
                                     config: VisualizationConfig) -> VisualizationResult:
        """
        Create static clustering plot using Matplotlib.
        
        Args:
            X_pca: PCA-transformed data
            cluster_labels: Cluster assignments
            point_labels: Labels for data points
            config: Visualization configuration
            
        Returns:
            VisualizationResult
        """
        plt.figure(figsize=config.figure_size)
        
        # Set style based on theme
        if config.theme == 'dark':
            plt.style.use('dark_background')
        
        # Create scatter plot
        unique_labels = np.unique(cluster_labels)
        colors = plt.cm.get_cmap(config.color_scheme)(np.linspace(0, 1, len(unique_labels)))
        
        for i, cluster_id in enumerate(unique_labels):
            cluster_mask = np.array(cluster_labels) == cluster_id
            
            if cluster_id == -1:
                # Outliers
                plt.scatter(
                    X_pca[cluster_mask, 0], 
                    X_pca[cluster_mask, 1],
                    c='black',
                    marker='x',
                    s=100,
                    label='Outliers',
                    alpha=0.7
                )
            else:
                plt.scatter(
                    X_pca[cluster_mask, 0], 
                    X_pca[cluster_mask, 1],
                    c=[colors[i]],
                    label=f'Cluster {cluster_id}',
                    alpha=0.7,
                    s=100
                )
        
        # Add labels for points
        for i, (x, y) in enumerate(X_pca):
            label = point_labels[i][:15] + ('...' if len(point_labels[i]) > 15 else '')
            plt.annotate(
                label,
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
        
        # Save plot
        viz_id = f"clustering_{int(time.time() * 1000)}_{str(uuid.uuid4())[:8]}"
        file_path = self.visualizations_dir / f"{viz_id}.{config.save_format}"
        
        plt.savefig(str(file_path), dpi=config.dpi, bbox_inches='tight')
        plt.close()
        
        file_size = file_path.stat().st_size
        
        return VisualizationResult(
            visualization_id=viz_id,
            file_path=str(file_path),
            file_size=file_size,
            format=config.save_format,
            plot_type="static_clustering",
            interactive=False,
            generation_time=0.0
        )
    
    def create_compliance_trends(self,
                               analysis_results: List[Any],
                               config: VisualizationConfig = None) -> VisualizationResult:
        """
        Create compliance trends visualization.
        
        Args:
            analysis_results: List of analysis results
            config: Visualization configuration
            
        Returns:
            VisualizationResult with trends visualization
        """
        if config is None:
            config = VisualizationConfig(plot_type="trends")
        
        if not MATPLOTLIB_AVAILABLE:
            raise ReportError("Matplotlib not available for trends visualization")
        
        start_time = time.time()
        
        try:
            # Extract compliance data over time
            compliance_data = []
            for result in analysis_results:
                if hasattr(result, 'compliance_analysis') and hasattr(result, 'timestamp'):
                    compliance_data.append({
                        'timestamp': result.timestamp,
                        'compliance_score': getattr(result.compliance_analysis, 'compliance_score', 0.0),
                        'issues_count': len(getattr(result.compliance_analysis, 'issues', [])),
                        'status': getattr(result.compliance_analysis, 'compliance_status', 'unknown')
                    })
            
            if not compliance_data:
                raise ReportError("No compliance data available for trends analysis")
            
            # Sort by timestamp
            compliance_data.sort(key=lambda x: x['timestamp'])
            
            # Create trends plot
            fig, axes = plt.subplots(2, 2, figsize=config.figure_size)
            fig.suptitle('Protocol Compliance Trends Analysis', fontsize=16)
            
            # Compliance scores over time
            timestamps = [d['timestamp'] for d in compliance_data]
            scores = [d['compliance_score'] for d in compliance_data]
            
            axes[0, 0].plot(timestamps, scores, marker='o', linewidth=2, markersize=6)
            axes[0, 0].set_title('Compliance Scores Over Time')
            axes[0, 0].set_ylabel('Compliance Score')
            axes[0, 0].grid(True, alpha=0.3)
            
            # Issues count over time
            issues = [d['issues_count'] for d in compliance_data]
            axes[0, 1].plot(timestamps, issues, marker='s', color='red', linewidth=2, markersize=6)
            axes[0, 1].set_title('Issues Count Over Time')
            axes[0, 1].set_ylabel('Number of Issues')
            axes[0, 1].grid(True, alpha=0.3)
            
            # Compliance status distribution
            status_counts = {}
            for d in compliance_data:
                status = d['status']
                status_counts[status] = status_counts.get(status, 0) + 1
            
            if status_counts:
                statuses = list(status_counts.keys())
                counts = list(status_counts.values())
                colors = ['green', 'orange', 'red'][:len(statuses)]
                
                axes[1, 0].pie(counts, labels=statuses, colors=colors, autopct='%1.1f%%')
                axes[1, 0].set_title('Compliance Status Distribution')
            
            # Compliance score distribution
            axes[1, 1].hist(scores, bins=10, alpha=0.7, color='blue')
            axes[1, 1].set_title('Compliance Score Distribution')
            axes[1, 1].set_xlabel('Compliance Score')
            axes[1, 1].set_ylabel('Frequency')
            axes[1, 1].grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # Save plot
            viz_id = f"trends_{int(time.time() * 1000)}_{str(uuid.uuid4())[:8]}"
            file_path = self.visualizations_dir / f"{viz_id}.{config.save_format}"
            
            plt.savefig(str(file_path), dpi=config.dpi, bbox_inches='tight')
            plt.close()
            
            file_size = file_path.stat().st_size
            generation_time = time.time() - start_time
            
            return VisualizationResult(
                visualization_id=viz_id,
                file_path=str(file_path),
                file_size=file_size,
                format=config.save_format,
                plot_type="compliance_trends",
                interactive=False,
                generation_time=generation_time,
                metadata={
                    'n_samples': len(compliance_data),
                    'avg_compliance_score': np.mean(scores),
                    'status_distribution': status_counts
                }
            )
            
        except Exception as e:
            logger.error(f"Trends visualization failed: {str(e)}", exception=e)
            raise ReportError(f"Failed to create trends visualization: {str(e)}")
    
    def get_visualization(self, visualization_id: str) -> Optional[VisualizationResult]:
        """
        Get visualization by ID.
        
        Args:
            visualization_id: Visualization identifier
            
        Returns:
            VisualizationResult if found, None otherwise
        """
        # Look for visualization files with this ID
        for format_ext in ['png', 'svg', 'html', 'json']:
            viz_path = self.visualizations_dir / f"{visualization_id}.{format_ext}"
            if viz_path.exists():
                file_size = viz_path.stat().st_size
                return VisualizationResult(
                    visualization_id=visualization_id,
                    file_path=str(viz_path),
                    file_size=file_size,
                    format=format_ext,
                    plot_type="unknown",
                    interactive=format_ext in ['html', 'json'],
                    generation_time=0.0
                )
        
        return None
    
    def list_visualizations(self, limit: int = 50) -> List[VisualizationResult]:
        """
        List generated visualizations.
        
        Args:
            limit: Maximum number of visualizations to return
            
        Returns:
            List of VisualizationResult objects
        """
        visualizations = []
        
        # Scan visualizations directory
        for viz_file in self.visualizations_dir.glob("*.png"):
            viz_id = viz_file.stem
            file_size = viz_file.stat().st_size
            
            viz_result = VisualizationResult(
                visualization_id=viz_id,
                file_path=str(viz_file),
                file_size=file_size,
                format="png",
                plot_type="unknown",
                interactive=False,
                generation_time=0.0
            )
            visualizations.append(viz_result)
        
        # Sort by creation time (newest first)
        visualizations.sort(key=lambda x: Path(x.file_path).stat().st_mtime, reverse=True)
        
        return visualizations[:limit]
    
    def delete_visualization(self, visualization_id: str) -> bool:
        """
        Delete a visualization and its files.
        
        Args:
            visualization_id: Visualization identifier
            
        Returns:
            True if deleted successfully, False otherwise
        """
        deleted = False
        
        # Delete all formats of the visualization
        for format_ext in ['png', 'svg', 'html', 'json']:
            viz_path = self.visualizations_dir / f"{visualization_id}.{format_ext}"
            if viz_path.exists():
                try:
                    viz_path.unlink()
                    deleted = True
                    logger.info(f"Deleted visualization file: {viz_path}")
                except Exception as e:
                    logger.error(f"Failed to delete visualization file {viz_path}: {str(e)}")
        
        return deleted

# Create global instance
visualization_service = VisualizationService()