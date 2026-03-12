"""Visual Whitespace Analyzer - Find visual gaps in niches"""

from typing import List, Dict, Any, Optional
import numpy as np
from collections import defaultdict
import structlog

logger = structlog.get_logger()

try:
    import hdbscan
    from sklearn.manifold import TSNE
    from sklearn.cluster import KMeans
    HAS_CLUSTERING = True
except ImportError:
    HAS_CLUSTERING = False
    logger.warning("Clustering dependencies not installed")


class VisualWhitespaceAnalyzer:
    """Analyze visual whitespace and gaps in niches"""
    
    def __init__(self):
        self.min_cluster_size = 5
    
    async def analyze_niche(
        self,
        embeddings: List[List[float]],
        metadata: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Analyze visual whitespace in a niche based on image embeddings.
        
        Returns:
            - dominant_clusters: Main visual styles in the niche
            - sparse_regions: Underrepresented visual areas (opportunities)
            - style_distribution: Distribution of styles
            - gap_score: Overall opportunity score for this niche
        """
        if not embeddings:
            return {
                "dominant_clusters": [],
                "sparse_regions": [],
                "style_distribution": {},
                "gap_score": 50.0,
                "error": "No embeddings provided",
            }
        
        if len(embeddings) < self.min_cluster_size:
            return {
                "dominant_clusters": [],
                "sparse_regions": [],
                "style_distribution": {},
                "gap_score": 80.0,
                "error": "Too few samples - high opportunity",
            }
        
        embeddings_array = np.array(embeddings)
        
        clusters = await self._cluster_embeddings(embeddings_array)
        
        dominant = self._find_dominant_clusters(clusters, metadata)
        
        sparse = self._find_sparse_regions(embeddings_array, clusters)
        
        distribution = self._calculate_style_distribution(clusters, metadata)
        
        gap_score = self._calculate_gap_score(clusters, sparse)
        
        return {
            "dominant_clusters": dominant,
            "sparse_regions": sparse,
            "style_distribution": distribution,
            "gap_score": gap_score,
            "total_samples": len(embeddings),
            "num_clusters": len(set(clusters)) - (1 if -1 in clusters else 0),
        }
    
    async def _cluster_embeddings(self, embeddings: np.ndarray) -> np.ndarray:
        """Cluster embeddings using HDBSCAN or KMeans"""
        if not HAS_CLUSTERING:
            n_clusters = min(5, len(embeddings) // 10 + 1)
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            return kmeans.fit_predict(embeddings)
        
        try:
            clusterer = hdbscan.HDBSCAN(
                min_cluster_size=self.min_cluster_size,
                min_samples=3,
                metric="cosine",
            )
            clusters = clusterer.fit_predict(embeddings)
            
            if len(set(clusters)) <= 1:
                n_clusters = min(5, len(embeddings) // 10 + 1)
                kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
                clusters = kmeans.fit_predict(embeddings)
            
            return clusters
        except Exception as e:
            logger.error("Clustering error", error=str(e))
            return np.zeros(len(embeddings), dtype=int)
    
    def _find_dominant_clusters(
        self,
        clusters: np.ndarray,
        metadata: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """Find and characterize dominant clusters"""
        cluster_counts = defaultdict(int)
        for c in clusters:
            if c >= 0:
                cluster_counts[c] += 1
        
        sorted_clusters = sorted(
            cluster_counts.items(),
            key=lambda x: x[1],
            reverse=True,
        )
        
        dominant = []
        for cluster_id, count in sorted_clusters[:5]:
            cluster_info = {
                "cluster_id": int(cluster_id),
                "size": count,
                "percentage": count / len(clusters) * 100,
            }
            
            if metadata:
                cluster_metadata = [
                    m for i, m in enumerate(metadata)
                    if clusters[i] == cluster_id
                ]
                cluster_info["sample_titles"] = [
                    m.get("title", "") for m in cluster_metadata[:3]
                ]
                
                all_keywords = []
                for m in cluster_metadata:
                    all_keywords.extend(m.get("keywords", [])[:5])
                
                keyword_counts = defaultdict(int)
                for kw in all_keywords:
                    keyword_counts[kw] += 1
                
                cluster_info["top_keywords"] = sorted(
                    keyword_counts.keys(),
                    key=lambda x: keyword_counts[x],
                    reverse=True,
                )[:10]
            
            dominant.append(cluster_info)
        
        return dominant
    
    def _find_sparse_regions(
        self,
        embeddings: np.ndarray,
        clusters: np.ndarray,
    ) -> List[Dict[str, Any]]:
        """Find sparse regions (potential opportunities)"""
        sparse_regions = []
        
        noise_count = sum(1 for c in clusters if c == -1)
        if noise_count > 0:
            noise_indices = [i for i, c in enumerate(clusters) if c == -1]
            sparse_regions.append({
                "type": "noise_points",
                "count": noise_count,
                "indices": noise_indices[:10],
                "description": "Images that don't fit any dominant style - unique opportunities",
            })
        
        cluster_counts = defaultdict(int)
        for c in clusters:
            if c >= 0:
                cluster_counts[c] += 1
        
        avg_size = np.mean(list(cluster_counts.values())) if cluster_counts else 0
        
        for cluster_id, count in cluster_counts.items():
            if count < avg_size * 0.3:
                sparse_regions.append({
                    "type": "small_cluster",
                    "cluster_id": int(cluster_id),
                    "count": count,
                    "description": f"Underrepresented style with only {count} samples",
                })
        
        return sparse_regions
    
    def _calculate_style_distribution(
        self,
        clusters: np.ndarray,
        metadata: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Calculate the distribution of styles"""
        total = len(clusters)
        cluster_counts = defaultdict(int)
        
        for c in clusters:
            cluster_counts[c] += 1
        
        distribution = {
            "total_samples": total,
            "num_clusters": len([c for c in cluster_counts if c >= 0]),
            "noise_percentage": cluster_counts.get(-1, 0) / total * 100 if total > 0 else 0,
            "cluster_sizes": {
                str(k): v for k, v in cluster_counts.items() if k >= 0
            },
        }
        
        sizes = [v for k, v in cluster_counts.items() if k >= 0]
        if sizes:
            distribution["largest_cluster_pct"] = max(sizes) / total * 100
            distribution["concentration_index"] = max(sizes) / (total / len(sizes)) if len(sizes) > 0 else 1
        
        return distribution
    
    def _calculate_gap_score(
        self,
        clusters: np.ndarray,
        sparse_regions: List[Dict[str, Any]],
    ) -> float:
        """Calculate overall gap/opportunity score"""
        score = 50.0
        
        unique_clusters = len(set(c for c in clusters if c >= 0))
        if unique_clusters <= 2:
            score += 20
        elif unique_clusters <= 5:
            score += 10
        elif unique_clusters > 10:
            score -= 10
        
        noise_pct = sum(1 for c in clusters if c == -1) / len(clusters) * 100 if len(clusters) > 0 else 0
        if noise_pct > 30:
            score += 15
        elif noise_pct > 15:
            score += 10
        
        score += len(sparse_regions) * 5
        
        return min(100, max(0, score))


async def analyze_visual_whitespace(
    embeddings: List[List[float]],
    metadata: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Main entry point for visual whitespace analysis"""
    analyzer = VisualWhitespaceAnalyzer()
    return await analyzer.analyze_niche(embeddings, metadata)


async def find_visual_gaps(
    niche_embeddings: List[List[float]],
    reference_embedding: List[float],
) -> Dict[str, Any]:
    """Find how a reference image relates to existing niche"""
    if not niche_embeddings:
        return {
            "similarity_scores": [],
            "is_unique": True,
            "uniqueness_score": 100,
        }
    
    niche_array = np.array(niche_embeddings)
    ref_array = np.array(reference_embedding)
    
    similarities = np.dot(niche_array, ref_array) / (
        np.linalg.norm(niche_array, axis=1) * np.linalg.norm(ref_array)
    )
    
    max_similarity = float(np.max(similarities))
    avg_similarity = float(np.mean(similarities))
    
    is_unique = max_similarity < 0.85
    uniqueness_score = (1 - max_similarity) * 100
    
    return {
        "max_similarity": max_similarity,
        "avg_similarity": avg_similarity,
        "is_unique": is_unique,
        "uniqueness_score": uniqueness_score,
        "closest_matches": np.argsort(similarities)[-5:][::-1].tolist(),
    }
