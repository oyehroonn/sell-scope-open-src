"""
Pandas-backed in-memory store. One nested "database" = dict of DataFrames.
Stores full scraped payload per asset in a scraped_data column (read/write).
Persists to disk via pickle so nested dicts are preserved.
"""

import os
import pickle
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from app.core.config import settings


def _data_dir() -> Path:
    p = getattr(settings, "DATA_DIR", "data")
    if os.path.isabs(p):
        return Path(p)
    app_dir = Path(__file__).resolve().parent.parent.parent
    return (app_dir / p).resolve()


# All asset columns including new fields from enhanced scraper + scraped_data for full payload
ASSET_COLUMNS = [
    # Core identifiers
    "adobe_id", "title", "description", "asset_type", "source",
    # Contributor
    "contributor_id", "contributor_name", "contributor_url",
    # Licensing
    "is_premium", "is_editorial", "is_ai_generated", "license_type",
    "has_model_release", "has_property_release",
    # Dimensions
    "width", "height", "orientation", "aspect_ratio", "megapixels",
    # Keywords and categories
    "keywords", "keywords_list", "keyword_count", "category", "categories",
    # Similar assets
    "similar_count", "similar_asset_ids",
    # File info
    "file_format", "file_size", "dpi",
    # Pricing
    "price", "credits",
    # Colors and dates
    "color_palette", "upload_date", "creation_date",
    # Video-specific
    "video_duration_seconds", "video_fps",
    # URLs
    "asset_url", "thumbnail_url", "preview_url",
    # Search context
    "search_query", "search_page", "position",
    # Timestamps
    "scraped_at", "created_at", "updated_at",
    # Library status
    "in_library", "added_to_library_at",
    # Full nested payload from scraper
    "scraped_data",
]


class PandasStore:
    """
    Main database as a set of pandas DataFrames. Assets store all scraped fields
    in a scraped_data column (nested dict). Read/write via DataFrame ops; persist with pickle.
    """

    def __init__(self, data_dir: Optional[Path] = None):
        self._dir = Path(data_dir or _data_dir()) / "pandas"
        self._dir.mkdir(parents=True, exist_ok=True)
        self._path = self._dir / "store.pkl"
        # DataFrames (keyed by table name)
        self._assets: pd.DataFrame = pd.DataFrame(columns=ASSET_COLUMNS)
        self._searches: pd.DataFrame = pd.DataFrame(columns=["term", "total_results_available", "scraped_at", "created_at"])
        self._contributors: pd.DataFrame = pd.DataFrame(columns=["adobe_id", "name", "profile_url", "portfolio_url", "scraped_at", "created_at", "updated_at"])
        self._keywords: pd.DataFrame = pd.DataFrame(columns=["term", "normalized_term", "type", "search_volume_estimate", "competition_level", "category_name", "related_keywords", "last_scraped_at", "created_at", "updated_at"])
        self._search_results: pd.DataFrame = pd.DataFrame(columns=["search_term", "asset_adobe_id", "position", "page", "scraped_at", "created_at"])
        self._similar_assets: pd.DataFrame = pd.DataFrame(columns=["main_asset_adobe_id", "similar_asset_adobe_id", "rank", "scraped_at", "created_at"])
        self._asset_keywords: pd.DataFrame = pd.DataFrame(columns=["asset_adobe_id", "keyword_term", "source", "created_at"])
        self._categories: pd.DataFrame = pd.DataFrame(columns=["name", "created_at"])
        self._asset_categories: pd.DataFrame = pd.DataFrame(columns=["asset_adobe_id", "category_name", "created_at"])
        # Keyword metrics for opportunity scoring
        self._keyword_metrics: pd.DataFrame = pd.DataFrame(columns=[
            "keyword", "nb_results", "unique_contributors", "demand_score", "competition_score",
            "gap_score", "freshness_score", "opportunity_score", "trend", "urgency",
            "related_searches", "categories", "scraped_at", "created_at", "updated_at"
        ])
        # Niche/category scores for heatmap (enhanced with more metrics)
        self._niche_scores: pd.DataFrame = pd.DataFrame(columns=[
            "name", "slug", "total_assets", "total_keywords", "avg_opportunity_score",
            "avg_demand_score", "avg_competition_score", "top_keywords", "trend",
            "unique_contributors", "premium_ratio", "avg_price", "estimated_results",
            "price_analysis", "category", "source_keywords",
            "scraped_at", "created_at", "updated_at"
        ])
        # Contributor profiles for competitor analysis
        self._contributor_profiles: pd.DataFrame = pd.DataFrame(columns=[
            "adobe_id", "name", "profile_url", "portfolio_url",
            "total_assets", "total_photos", "total_vectors", "total_videos", "total_templates", "total_3d",
            "premium_count", "premium_ratio", "top_categories", "top_keywords",
            "category_distribution", "estimated_join_date", "upload_frequency_monthly",
            "avg_asset_dimensions", "quality_indicators", "niches", "competition_level",
            "sample_assets", "scraped_at", "created_at", "updated_at"
        ])
        # Deep market analysis cache
        self._market_analysis: pd.DataFrame = pd.DataFrame(columns=[
            "keyword", "analysis_depth", "nb_results", "sample_size",
            "unique_contributors", "premium_ratio", "editorial_ratio", "ai_generated_ratio",
            "price_analysis", "dimension_analysis", "upload_date_analysis",
            "keyword_frequency", "contributor_concentration", "format_distribution",
            "top_assets", "contributor_profiles", "similar_assets",
            "scoring", "visualizations", "errors",
            "scraped_at", "expires_at", "created_at", "updated_at"
        ])
        # Saved keyword researches (user-saved with full deep analysis)
        self._saved_researches: pd.DataFrame = pd.DataFrame(columns=[
            "keyword", "analysis_depth", "is_opportunity", "saved_at",
            "nb_results", "unique_contributors",
            "demand_score", "competition_score", "gap_score", "freshness_score", "opportunity_score",
            "trend", "urgency", "related_searches", "categories",
            "deep_analysis",  # Full deep analysis data as JSON/dict
            "created_at", "updated_at"
        ])

    def load_all(self) -> None:
        """Load the full nested database from disk (pickle)."""
        if not self._path.exists():
            return
        try:
            with open(self._path, "rb") as f:
                data = pickle.load(f)
            self._assets = data.get("assets", self._assets)
            self._searches = data.get("searches", self._searches)
            self._contributors = data.get("contributors", self._contributors)
            self._keywords = data.get("keywords", self._keywords)
            self._search_results = data.get("search_results", self._search_results)
            self._similar_assets = data.get("similar_assets", self._similar_assets)
            self._asset_keywords = data.get("asset_keywords", self._asset_keywords)
            self._categories = data.get("categories", self._categories)
            self._asset_categories = data.get("asset_categories", self._asset_categories)
            self._keyword_metrics = data.get("keyword_metrics", self._keyword_metrics)
            self._niche_scores = data.get("niche_scores", self._niche_scores)
            self._contributor_profiles = data.get("contributor_profiles", self._contributor_profiles)
            self._market_analysis = data.get("market_analysis", self._market_analysis)
            self._saved_researches = data.get("saved_researches", self._saved_researches)
            # Ensure columns exist
            for col in ASSET_COLUMNS:
                if col not in self._assets.columns:
                    self._assets[col] = None
        except Exception:
            pass

    def _save(self) -> None:
        """Persist all DataFrames to disk (pickle)."""
        data = {
            "assets": self._assets,
            "searches": self._searches,
            "contributors": self._contributors,
            "keywords": self._keywords,
            "search_results": self._search_results,
            "similar_assets": self._similar_assets,
            "asset_keywords": self._asset_keywords,
            "categories": self._categories,
            "asset_categories": self._asset_categories,
            "keyword_metrics": self._keyword_metrics,
            "niche_scores": self._niche_scores,
            "contributor_profiles": self._contributor_profiles,
            "market_analysis": self._market_analysis,
            "saved_researches": self._saved_researches,
        }
        with open(self._path, "wb") as f:
            pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)

    @staticmethod
    def _row_to_dict(row: pd.Series) -> Dict[str, Any]:
        import ast
        d = row.to_dict()
        # Convert pandas/numpy types for JSON/API; keep dict/list (e.g. scraped_data) as-is
        for k, v in list(d.items()):
            # Skip dict/list types (e.g. scraped_data, keywords_list)
            if isinstance(v, (dict, list)):
                continue
            # Handle None/NaN - check scalar first to avoid array ambiguity
            try:
                if v is None or (hasattr(v, '__len__') is False and pd.isna(v)):
                    d[k] = None
                    continue
            except (ValueError, TypeError):
                pass
            # Convert numpy scalars
            if hasattr(v, "item"):
                try:
                    d[k] = v.item()
                except (ValueError, AttributeError):
                    pass
            # Parse string representations of lists/dicts
            if isinstance(v, str) and v.startswith('[') or (isinstance(v, str) and v.startswith('{')):
                try:
                    parsed = ast.literal_eval(v)
                    if isinstance(parsed, (list, dict)):
                        d[k] = parsed
                except:
                    pass
        return d

    # ——— Searches ———
    def upsert_search(self, term: str, total_results_available: Optional[int] = None, scraped_at: Optional[datetime] = None) -> None:
        term = (term or "").strip().lower()
        if not term:
            return
        now = datetime.utcnow()
        scraped_at = scraped_at or now
        mask = self._searches["term"] == term
        if mask.any():
            idx = self._searches.loc[mask].index[0]
            self._searches.at[idx, "total_results_available"] = total_results_available if total_results_available is not None else self._searches.at[idx, "total_results_available"]
            self._searches.at[idx, "scraped_at"] = scraped_at
        else:
            self._searches = pd.concat([
                self._searches,
                pd.DataFrame([{"term": term, "total_results_available": total_results_available or 0, "scraped_at": scraped_at, "created_at": now}]),
            ], ignore_index=True)
        self._save()

    def get_searches(self, limit: int = 50) -> List[Dict]:
        df = self._searches.dropna(subset=["scraped_at"]).sort_values("scraped_at", ascending=False).head(limit)
        return [self._row_to_dict(row) for _, row in df.iterrows()]

    # ——— Contributors ———
    def upsert_contributor(self, adobe_id: str, name: Optional[str] = None, profile_url: Optional[str] = None, portfolio_url: Optional[str] = None) -> None:
        if not adobe_id:
            return
        now = datetime.utcnow()
        mask = self._contributors["adobe_id"] == adobe_id
        if mask.any():
            idx = self._contributors.loc[mask].index[0]
            if name is not None:
                self._contributors.at[idx, "name"] = name
            if profile_url is not None:
                self._contributors.at[idx, "profile_url"] = profile_url
            if portfolio_url is not None:
                self._contributors.at[idx, "portfolio_url"] = portfolio_url
            self._contributors.at[idx, "updated_at"] = now
        else:
            self._contributors = pd.concat([
                self._contributors,
                pd.DataFrame([{"adobe_id": adobe_id, "name": name, "profile_url": profile_url, "portfolio_url": portfolio_url, "scraped_at": now, "created_at": now, "updated_at": now}]),
            ], ignore_index=True)
        self._save()

    def get_contributors(self) -> List[Dict]:
        return [self._row_to_dict(row) for _, row in self._contributors.iterrows()]

    # ——— Keywords ———
    def upsert_keyword(self, term: str, kw_type: str = "asset") -> Optional[Dict]:
        term = (term or "").strip().lower()
        if not term or len(term) > 500:
            return None
        now = datetime.utcnow()
        mask = self._keywords["term"] == term
        if mask.any():
            return self._row_to_dict(self._keywords.loc[mask].iloc[0])
        new_row = pd.DataFrame([{"term": term, "normalized_term": term, "type": kw_type, "created_at": now, "updated_at": now}])
        self._keywords = pd.concat([self._keywords, new_row], ignore_index=True)
        self._save()
        return self._row_to_dict(self._keywords.iloc[-1])

    def get_keywords(self) -> List[Dict]:
        return [self._row_to_dict(row) for _, row in self._keywords.iterrows()]

    # ——— Categories ———
    def upsert_category(self, name: str) -> None:
        name = (name or "").strip()
        if not name:
            return
        now = datetime.utcnow()
        if name not in self._categories["name"].values:
            self._categories = pd.concat([
                self._categories,
                pd.DataFrame([{"name": name, "created_at": now}]),
            ], ignore_index=True)
            self._save()

    def add_asset_category(self, asset_adobe_id: str, category_name: str) -> None:
        category_name = (category_name or "").strip()
        if not asset_adobe_id or not category_name:
            return
        now = datetime.utcnow()
        exists = ((self._asset_categories["asset_adobe_id"] == asset_adobe_id) & (self._asset_categories["category_name"] == category_name)).any()
        if not exists:
            self._asset_categories = pd.concat([
                self._asset_categories,
                pd.DataFrame([{"asset_adobe_id": asset_adobe_id, "category_name": category_name, "created_at": now}]),
            ], ignore_index=True)
            self._save()

    # ——— Assets (with full scraped_data) ———
    def upsert_asset(self, data: Dict[str, Any], scraped_data: Optional[Dict[str, Any]] = None) -> None:
        adobe_id = str((data.get("adobe_id") or ""))
        if not adobe_id:
            return
        now = datetime.utcnow()
        payload = scraped_data or data
        mask = self._assets["adobe_id"] == adobe_id
        row = {c: None for c in ASSET_COLUMNS}
        row["adobe_id"] = adobe_id
        row["created_at"] = now
        row["updated_at"] = now
        for k, v in data.items():
            if k in ASSET_COLUMNS and v is not None:
                row[k] = v
        row["scraped_data"] = payload if isinstance(payload, dict) else None
        if mask.any():
            idx = self._assets.loc[mask].index[0]
            for k, v in row.items():
                self._assets.at[idx, k] = v
            self._assets.at[idx, "updated_at"] = now
        else:
            new_row = pd.DataFrame([row], columns=ASSET_COLUMNS)
            if self._assets.empty:
                self._assets = new_row.copy()
            else:
                self._assets = pd.concat([self._assets, new_row], ignore_index=True)
        self._save()

    def get_asset(self, adobe_id: str) -> Optional[Dict]:
        mask = self._assets["adobe_id"] == str(adobe_id)
        if not mask.any():
            return None
        return self._row_to_dict(self._assets.loc[mask].iloc[0])

    def get_asset_full_scraped(self, adobe_id: str) -> Optional[Dict]:
        """Return the full scraped payload for an asset (scraped_data column)."""
        row = self.get_asset(adobe_id)
        if not row:
            return None
        return row.get("scraped_data") or row

    def get_all_assets(
        self,
        offset: int = 0,
        limit: int = 50,
        asset_type: Optional[str] = None,
        contributor_id: Optional[str] = None,
        is_premium: Optional[bool] = None,
        search: Optional[str] = None,
        in_library: Optional[bool] = None,
    ) -> tuple[List[Dict], int]:
        df = self._assets
        if asset_type:
            df = df[df["asset_type"] == asset_type]
        if contributor_id:
            df = df[df["contributor_id"] == contributor_id]
        if is_premium is not None:
            df = df[df["is_premium"] == is_premium]
        if in_library is not None:
            df = df[df["in_library"] == in_library]
        if search:
            s = (search or "").lower()
            df = df[df.apply(lambda r: (str(r.get("title") or "").lower().find(s) >= 0 or str(r.get("contributor_name") or "").lower().find(s) >= 0), axis=1)]
        df = df.sort_values("scraped_at", ascending=False, na_position="last")
        total = len(df)
        slice_df = df.iloc[offset : offset + limit]
        return [self._row_to_dict(row) for _, row in slice_df.iterrows()], total
    
    def add_to_library(self, adobe_id: str) -> bool:
        """Mark an asset as added to the user's library."""
        adobe_id = str(adobe_id)
        mask = self._assets["adobe_id"] == adobe_id
        if not mask.any():
            return False
        idx = self._assets.loc[mask].index[0]
        self._assets.at[idx, "in_library"] = True
        self._assets.at[idx, "added_to_library_at"] = datetime.utcnow()
        self._save()
        return True
    
    def remove_from_library(self, adobe_id: str) -> bool:
        """Remove an asset from the user's library."""
        adobe_id = str(adobe_id)
        mask = self._assets["adobe_id"] == adobe_id
        if not mask.any():
            return False
        idx = self._assets.loc[mask].index[0]
        self._assets.at[idx, "in_library"] = False
        self._assets.at[idx, "added_to_library_at"] = None
        self._save()
        return True
    
    def is_in_library(self, adobe_id: str) -> bool:
        """Check if an asset is in the library."""
        adobe_id = str(adobe_id)
        mask = self._assets["adobe_id"] == adobe_id
        if not mask.any():
            return False
        return bool(self._assets.loc[mask, "in_library"].iloc[0])

    def delete_asset(self, adobe_id: str) -> bool:
        adobe_id = str(adobe_id)
        if adobe_id not in self._assets["adobe_id"].values:
            return False
        self._assets = self._assets[self._assets["adobe_id"] != adobe_id]
        self._search_results = self._search_results[self._search_results["asset_adobe_id"] != adobe_id]
        self._similar_assets = self._similar_assets[
            (self._similar_assets["main_asset_adobe_id"] != adobe_id) & (self._similar_assets["similar_asset_adobe_id"] != adobe_id)
        ]
        self._asset_keywords = self._asset_keywords[self._asset_keywords["asset_adobe_id"] != adobe_id]
        self._asset_categories = self._asset_categories[self._asset_categories["asset_adobe_id"] != adobe_id]
        self._save()
        return True

    # ——— Search results ———
    def add_search_result(self, search_term: str, asset_adobe_id: str, position: int = 0, page: int = 1) -> None:
        now = datetime.utcnow()
        self._search_results = pd.concat([
            self._search_results,
            pd.DataFrame([{"search_term": search_term.strip().lower(), "asset_adobe_id": str(asset_adobe_id), "position": position, "page": page, "scraped_at": now, "created_at": now}]),
        ], ignore_index=True)
        self._save()

    def get_search_results(self, search_term: str) -> List[Dict]:
        df = self._search_results[self._search_results["search_term"] == (search_term or "").strip().lower()]
        return [self._row_to_dict(row) for _, row in df.iterrows()]

    # ——— Similar assets ———
    def add_similar(self, main_asset_adobe_id: str, similar_asset_adobe_id: str, rank: int = 0) -> None:
        if not main_asset_adobe_id or not similar_asset_adobe_id:
            return
        now = datetime.utcnow()
        self._similar_assets = pd.concat([
            self._similar_assets,
            pd.DataFrame([{"main_asset_adobe_id": str(main_asset_adobe_id), "similar_asset_adobe_id": str(similar_asset_adobe_id), "rank": rank, "scraped_at": now, "created_at": now}]),
        ], ignore_index=True)
        self._save()

    def get_similar(self, main_asset_adobe_id: str, limit: int = 20) -> List[Dict]:
        df = self._similar_assets[self._similar_assets["main_asset_adobe_id"] == str(main_asset_adobe_id)].sort_values("rank").head(limit)
        out = []
        for _, r in df.iterrows():
            sim = self.get_asset(r["similar_asset_adobe_id"])
            if sim:
                out.append({"adobe_id": sim.get("adobe_id"), "title": sim.get("title"), "thumbnail_url": sim.get("thumbnail_url"), "preview_url": sim.get("preview_url")})
        return out

    # ——— Asset keywords ———
    def add_asset_keyword(self, asset_adobe_id: str, keyword_term: str, source: str = "meta") -> None:
        keyword_term = (keyword_term or "").strip().lower()
        if not asset_adobe_id or not keyword_term or len(keyword_term) > 500:
            return
        exists = ((self._asset_keywords["asset_adobe_id"] == str(asset_adobe_id)) & (self._asset_keywords["keyword_term"] == keyword_term) & (self._asset_keywords["source"] == source)).any()
        if not exists:
            now = datetime.utcnow()
            self._asset_keywords = pd.concat([
                self._asset_keywords,
                pd.DataFrame([{"asset_adobe_id": str(asset_adobe_id), "keyword_term": keyword_term, "source": source, "created_at": now}]),
            ], ignore_index=True)
            self._save()

    def get_asset_keywords(self, asset_adobe_id: str) -> List[str]:
        df = self._asset_keywords[self._asset_keywords["asset_adobe_id"] == str(asset_adobe_id)]
        return df["keyword_term"].tolist()

    # ——— Insights ———
    def get_insights_summary(self) -> Dict[str, int]:
        return {
            "total_assets": len(self._assets),
            "total_searches": len(self._searches),
            "total_contributors": len(self._contributors),
            "total_keywords": len(self._keywords),
            "total_similar_links": len(self._similar_assets),
        }

    def get_top_keywords(self, limit: int = 50) -> List[Dict]:
        c = self._asset_keywords["keyword_term"].value_counts()
        return [{"term": t, "asset_count": int(c)} for t, c in c.head(limit).items()]

    def get_top_contributors(self, limit: int = 50) -> List[Dict]:
        df = self._assets[self._assets["contributor_id"].notna()]
        if df.empty:
            return []
        c = df.groupby(["contributor_id", "contributor_name"], dropna=False).size().sort_values(ascending=False).head(limit)
        out = []
        for (cid, name), n in c.items():
            out.append({"adobe_id": cid if pd.notna(cid) else "", "name": name if pd.notna(name) else None, "asset_count": int(n)})
        return out

    def get_all_asset_rows(self) -> List[Dict]:
        return [self._row_to_dict(row) for _, row in self._assets.iterrows()]

    # ——— Keyword Metrics ———
    def upsert_keyword_metrics(self, data: Dict[str, Any]) -> None:
        """Insert or update keyword metrics for opportunity scoring."""
        keyword = (data.get("keyword") or "").strip().lower()
        if not keyword:
            return
        now = datetime.utcnow()
        
        mask = self._keyword_metrics["keyword"] == keyword
        row = {
            "keyword": keyword,
            "nb_results": data.get("nb_results", 0),
            "unique_contributors": data.get("unique_contributors", 0),
            "demand_score": data.get("demand_score", 0),
            "competition_score": data.get("competition_score", 0),
            "gap_score": data.get("gap_score", 50),
            "freshness_score": data.get("freshness_score", 50),
            "opportunity_score": data.get("opportunity_score", 0),
            "trend": data.get("trend", "stable"),
            "urgency": data.get("urgency", "medium"),
            "related_searches": data.get("related_searches", []),
            "categories": data.get("categories", []),
            "scraped_at": data.get("scraped_at") or now,
            "updated_at": now,
        }
        
        if mask.any():
            idx = self._keyword_metrics.loc[mask].index[0]
            for k, v in row.items():
                self._keyword_metrics.at[idx, k] = v
        else:
            row["created_at"] = now
            new_row = pd.DataFrame([row])
            if self._keyword_metrics.empty:
                self._keyword_metrics = new_row.copy()
            else:
                self._keyword_metrics = pd.concat([self._keyword_metrics, new_row], ignore_index=True)
        self._save()
    
    def get_keyword_metrics(self, keyword: str) -> Optional[Dict]:
        """Get metrics for a specific keyword."""
        keyword = (keyword or "").strip().lower()
        mask = self._keyword_metrics["keyword"] == keyword
        if not mask.any():
            return None
        return self._row_to_dict(self._keyword_metrics.loc[mask].iloc[0])
    
    def get_all_keyword_metrics(self, limit: int = 100) -> List[Dict]:
        """Get all keyword metrics sorted by opportunity score."""
        df = self._keyword_metrics.sort_values("opportunity_score", ascending=False).head(limit)
        return [self._row_to_dict(row) for _, row in df.iterrows()]
    
    def get_trending_keywords(self, limit: int = 20) -> List[Dict]:
        """Get trending keywords (high demand + high opportunity)."""
        df = self._keyword_metrics[self._keyword_metrics["trend"] == "up"]
        if df.empty:
            df = self._keyword_metrics
        df = df.sort_values("opportunity_score", ascending=False).head(limit)
        return [self._row_to_dict(row) for _, row in df.iterrows()]
    
    def get_top_opportunities(self, limit: int = 20, min_score: float = 0) -> List[Dict]:
        """Get top opportunity keywords."""
        df = self._keyword_metrics[self._keyword_metrics["opportunity_score"] >= min_score]
        df = df.sort_values("opportunity_score", ascending=False).head(limit)
        return [self._row_to_dict(row) for _, row in df.iterrows()]
    
    def search_keyword_metrics(self, query: str, limit: int = 20) -> List[Dict]:
        """Search keyword metrics by term."""
        query = (query or "").strip().lower()
        if not query:
            return []
        df = self._keyword_metrics[self._keyword_metrics["keyword"].str.contains(query, case=False, na=False)]
        df = df.sort_values("opportunity_score", ascending=False).head(limit)
        return [self._row_to_dict(row) for _, row in df.iterrows()]
    
    # ——— Niche Scores ———
    def upsert_niche_score(self, data: Dict[str, Any]) -> None:
        """Insert or update niche/category score with aggregation support."""
        name = (data.get("name") or "").strip()
        if not name:
            return
        now = datetime.utcnow()
        slug = data.get("slug") or name.lower().replace(" ", "-").replace("&", "and")
        
        mask = self._niche_scores["slug"] == slug
        
        # Get existing data for aggregation
        existing = None
        if mask.any():
            existing = self._row_to_dict(self._niche_scores.loc[mask].iloc[0])
        
        # Aggregate keywords from multiple sources
        new_keywords = data.get("top_keywords", [])
        existing_keywords = existing.get("top_keywords", []) if existing else []
        if isinstance(existing_keywords, str):
            try:
                existing_keywords = eval(existing_keywords)
            except:
                existing_keywords = []
        
        # Merge and deduplicate keywords
        all_keywords = list(dict.fromkeys(new_keywords + existing_keywords))[:20]
        
        # Track source keywords for aggregation
        source_keyword = data.get("source_keyword", "")
        existing_sources = existing.get("source_keywords", []) if existing else []
        if isinstance(existing_sources, str):
            try:
                existing_sources = eval(existing_sources)
            except:
                existing_sources = []
        if source_keyword and source_keyword not in existing_sources:
            existing_sources.append(source_keyword)
        
        # For existing entries, use weighted average for scores
        if existing:
            old_weight = existing.get("total_assets", 1) or 1
            new_weight = data.get("total_assets", 1) or 1
            total_weight = old_weight + new_weight
            
            # Weighted average of scores
            avg_opp = (existing.get("avg_opportunity_score", 0) * old_weight + 
                      data.get("avg_opportunity_score", 0) * new_weight) / total_weight
            avg_demand = (existing.get("avg_demand_score", 0) * old_weight + 
                         data.get("avg_demand_score", 0) * new_weight) / total_weight
            avg_comp = (existing.get("avg_competition_score", 0) * old_weight + 
                       data.get("avg_competition_score", 0) * new_weight) / total_weight
            
            # Accumulate totals
            total_assets = existing.get("total_assets", 0) + data.get("total_assets", 0)
            total_keywords = len(all_keywords)
            unique_contributors = max(
                existing.get("unique_contributors", 0),
                data.get("unique_contributors", 0)
            )
            estimated_results = max(
                existing.get("estimated_results", 0),
                data.get("estimated_results", 0)
            )
        else:
            avg_opp = data.get("avg_opportunity_score", 0)
            avg_demand = data.get("avg_demand_score", 0)
            avg_comp = data.get("avg_competition_score", 0)
            total_assets = data.get("total_assets", 0)
            total_keywords = data.get("total_keywords", 0)
            unique_contributors = data.get("unique_contributors", 0)
            estimated_results = data.get("estimated_results", 0)
        
        row = {
            "name": name,
            "slug": slug,
            "total_assets": total_assets,
            "total_keywords": total_keywords,
            "avg_opportunity_score": round(avg_opp, 2),
            "avg_demand_score": round(avg_demand, 2),
            "avg_competition_score": round(avg_comp, 2),
            "top_keywords": all_keywords,
            "trend": data.get("trend", "stable"),
            "unique_contributors": unique_contributors,
            "premium_ratio": data.get("premium_ratio", 0),
            "avg_price": data.get("avg_price"),
            "estimated_results": estimated_results,
            "price_analysis": data.get("price_analysis", {}),
            "category": data.get("category", ""),
            "source_keywords": existing_sources,
            "scraped_at": data.get("scraped_at") or now,
            "updated_at": now,
        }
        
        if mask.any():
            idx = self._niche_scores.loc[mask].index[0]
            for k, v in row.items():
                self._niche_scores.at[idx, k] = v
        else:
            row["created_at"] = now
            new_row = pd.DataFrame([row])
            if self._niche_scores.empty:
                self._niche_scores = new_row.copy()
            else:
                self._niche_scores = pd.concat([self._niche_scores, new_row], ignore_index=True)
        self._save()
    
    def get_niche_score(self, slug: str) -> Optional[Dict]:
        """Get score for a specific niche."""
        mask = self._niche_scores["slug"] == slug
        if not mask.any():
            return None
        return self._row_to_dict(self._niche_scores.loc[mask].iloc[0])
    
    def get_all_niche_scores(self, limit: int = 50) -> List[Dict]:
        """Get all niche scores sorted by opportunity."""
        df = self._niche_scores.sort_values("avg_opportunity_score", ascending=False).head(limit)
        return [self._row_to_dict(row) for _, row in df.iterrows()]
    
    def get_niche_heatmap(self) -> List[Dict]:
        """Get niche data formatted for heatmap visualization with full metrics."""
        df = self._niche_scores.sort_values("avg_opportunity_score", ascending=False)
        results = []
        for _, row in df.iterrows():
            # Parse top_keywords if stored as string
            top_keywords = row.get("top_keywords", [])
            if isinstance(top_keywords, str):
                try:
                    top_keywords = eval(top_keywords)
                except:
                    top_keywords = []
            
            results.append({
                "name": row.get("name"),
                "slug": row.get("slug"),
                "score": row.get("avg_opportunity_score", 0),
                "demand": row.get("avg_demand_score", 0),
                "competition": row.get("avg_competition_score", 0),
                "assets": row.get("total_assets", 0),
                "keywords": row.get("total_keywords", 0),
                "top_keywords": top_keywords[:5] if top_keywords else [],
                "unique_contributors": row.get("unique_contributors", 0),
                "premium_ratio": row.get("premium_ratio", 0),
                "estimated_results": row.get("estimated_results", 0),
                "trend": row.get("trend", "stable"),
            })
        return results
    
    def calculate_niche_scores_from_keywords(self) -> None:
        """Recalculate niche scores by aggregating keyword metrics by category."""
        if self._keyword_metrics.empty:
            return
        
        # Get all categories from keyword metrics
        category_data = {}
        for _, row in self._keyword_metrics.iterrows():
            categories = row.get("categories") or []
            if isinstance(categories, str):
                try:
                    categories = eval(categories)
                except:
                    categories = []
            
            keyword = row.get("keyword", "")
            opp_score = row.get("opportunity_score", 0)
            demand_score = row.get("demand_score", 0)
            comp_score = row.get("competition_score", 0)
            
            for cat in categories:
                cat_name = cat.get("name") if isinstance(cat, dict) else str(cat)
                if not cat_name:
                    continue
                
                if cat_name not in category_data:
                    category_data[cat_name] = {
                        "keywords": [],
                        "opp_scores": [],
                        "demand_scores": [],
                        "comp_scores": [],
                    }
                
                category_data[cat_name]["keywords"].append(keyword)
                category_data[cat_name]["opp_scores"].append(opp_score)
                category_data[cat_name]["demand_scores"].append(demand_score)
                category_data[cat_name]["comp_scores"].append(comp_score)
        
        # Also aggregate from asset categories
        for _, row in self._asset_categories.iterrows():
            cat_name = row.get("category_name")
            if cat_name and cat_name not in category_data:
                category_data[cat_name] = {
                    "keywords": [],
                    "opp_scores": [50],
                    "demand_scores": [50],
                    "comp_scores": [50],
                }
        
        # Calculate niche scores
        for cat_name, data in category_data.items():
            if not data["opp_scores"]:
                continue
            
            avg_opp = sum(data["opp_scores"]) / len(data["opp_scores"])
            avg_demand = sum(data["demand_scores"]) / len(data["demand_scores"]) if data["demand_scores"] else 50
            avg_comp = sum(data["comp_scores"]) / len(data["comp_scores"]) if data["comp_scores"] else 50
            
            # Count assets in this category
            cat_assets = self._asset_categories[self._asset_categories["category_name"] == cat_name]
            total_assets = len(cat_assets["asset_adobe_id"].unique()) if not cat_assets.empty else 0
            
            # Determine trend
            if avg_demand >= 70:
                trend = "up"
            elif avg_demand >= 40:
                trend = "stable"
            else:
                trend = "down"
            
            self.upsert_niche_score({
                "name": cat_name,
                "total_assets": total_assets,
                "total_keywords": len(data["keywords"]),
                "avg_opportunity_score": round(avg_opp, 2),
                "avg_demand_score": round(avg_demand, 2),
                "avg_competition_score": round(avg_comp, 2),
                "top_keywords": data["keywords"][:10],
                "trend": trend,
            })
    
    # ——— Contributor Profiles ———
    def upsert_contributor_profile(self, data: Dict[str, Any]) -> None:
        """Insert or update a contributor profile."""
        adobe_id = str(data.get("adobe_id", "")).strip()
        if not adobe_id:
            return
        now = datetime.utcnow()
        
        mask = self._contributor_profiles["adobe_id"] == adobe_id
        row = {
            "adobe_id": adobe_id,
            "name": data.get("name"),
            "profile_url": data.get("profile_url"),
            "portfolio_url": data.get("portfolio_url"),
            "total_assets": data.get("total_assets", 0),
            "total_photos": data.get("total_photos", 0),
            "total_vectors": data.get("total_vectors", 0),
            "total_videos": data.get("total_videos", 0),
            "total_templates": data.get("total_templates", 0),
            "total_3d": data.get("total_3d", 0),
            "premium_count": data.get("premium_count", 0),
            "premium_ratio": data.get("premium_ratio", 0.0),
            "top_categories": data.get("top_categories", []),
            "top_keywords": data.get("top_keywords", []),
            "category_distribution": data.get("category_distribution", {}),
            "estimated_join_date": data.get("estimated_join_date"),
            "upload_frequency_monthly": data.get("upload_frequency_monthly", 0.0),
            "avg_asset_dimensions": data.get("avg_asset_dimensions"),
            "quality_indicators": data.get("quality_indicators", {}),
            "niches": data.get("niches", []),
            "competition_level": data.get("competition_level"),
            "sample_assets": data.get("sample_assets", []),
            "scraped_at": data.get("scraped_at") or now,
            "updated_at": now,
        }
        
        if mask.any():
            idx = self._contributor_profiles.loc[mask].index[0]
            for k, v in row.items():
                self._contributor_profiles.at[idx, k] = v
        else:
            row["created_at"] = now
            new_row = pd.DataFrame([row])
            if self._contributor_profiles.empty:
                self._contributor_profiles = new_row.copy()
            else:
                self._contributor_profiles = pd.concat([self._contributor_profiles, new_row], ignore_index=True)
        self._save()
    
    def get_contributor_profile(self, adobe_id: str) -> Optional[Dict]:
        """Get profile for a specific contributor."""
        mask = self._contributor_profiles["adobe_id"] == str(adobe_id)
        if not mask.any():
            return None
        return self._row_to_dict(self._contributor_profiles.loc[mask].iloc[0])
    
    def get_all_contributor_profiles(self, limit: int = 100) -> List[Dict]:
        """Get all contributor profiles sorted by portfolio size."""
        df = self._contributor_profiles.sort_values("total_assets", ascending=False).head(limit)
        return [self._row_to_dict(row) for _, row in df.iterrows()]
    
    def get_top_contributors_for_keyword(self, keyword: str, limit: int = 10) -> List[Dict]:
        """Get top contributors for a specific keyword based on their activity."""
        profiles = []
        for _, row in self._contributor_profiles.iterrows():
            top_keywords = row.get("top_keywords", [])
            if isinstance(top_keywords, str):
                try:
                    import ast
                    top_keywords = ast.literal_eval(top_keywords)
                except:
                    top_keywords = []
            
            keyword_lower = keyword.lower()
            if any(keyword_lower in kw.lower() for kw in top_keywords):
                profiles.append(self._row_to_dict(row))
        
        profiles.sort(key=lambda x: x.get("total_assets", 0), reverse=True)
        return profiles[:limit]
    
    def search_contributor_profiles(self, query: str, limit: int = 20) -> List[Dict]:
        """Search contributor profiles by name or niche."""
        query_lower = query.lower()
        results = []
        
        for _, row in self._contributor_profiles.iterrows():
            name = (row.get("name") or "").lower()
            niches = row.get("niches", [])
            if isinstance(niches, str):
                try:
                    import ast
                    niches = ast.literal_eval(niches)
                except:
                    niches = []
            
            if query_lower in name or any(query_lower in n.lower() for n in niches):
                results.append(self._row_to_dict(row))
        
        results.sort(key=lambda x: x.get("total_assets", 0), reverse=True)
        return results[:limit]
    
    # ——— Deep Market Analysis Cache ———
    def upsert_market_analysis(self, data: Dict[str, Any]) -> None:
        """Insert or update market analysis cache."""
        keyword = (data.get("keyword") or "").strip().lower()
        depth = data.get("analysis_depth") or data.get("depth") or "medium"
        if not keyword:
            return
        now = datetime.utcnow()
        
        mask = (self._market_analysis["keyword"] == keyword) & (self._market_analysis["analysis_depth"] == depth)
        
        # Set expiry (24 hours for deep, 12 hours for medium, 6 hours for simple)
        hours = {"deep": 24, "medium": 12, "simple": 6}.get(depth, 12)
        from datetime import timedelta
        expires_at = now + timedelta(hours=hours)
        
        row = {
            "keyword": keyword,
            "analysis_depth": depth,
            "nb_results": data.get("nb_results") or data.get("search_results", {}).get("nb_results", 0),
            "sample_size": data.get("sample_size") or len(data.get("assets", [])),
            "unique_contributors": data.get("unique_contributors") or data.get("market_analysis", {}).get("unique_contributors", 0),
            "premium_ratio": data.get("premium_ratio") or data.get("market_analysis", {}).get("premium_ratio", 0),
            "editorial_ratio": data.get("editorial_ratio") or data.get("market_analysis", {}).get("editorial_ratio", 0),
            "ai_generated_ratio": data.get("ai_generated_ratio") or data.get("market_analysis", {}).get("ai_generated_ratio", 0),
            "price_analysis": data.get("price_analysis") or data.get("market_analysis", {}).get("price_analysis", {}),
            "dimension_analysis": data.get("dimension_analysis") or data.get("market_analysis", {}).get("dimension_analysis", {}),
            "upload_date_analysis": data.get("upload_date_analysis") or data.get("market_analysis", {}).get("upload_date_analysis", {}),
            "keyword_frequency": data.get("keyword_frequency") or data.get("market_analysis", {}).get("keyword_frequency", {}),
            "contributor_concentration": data.get("contributor_concentration") or data.get("market_analysis", {}).get("contributor_concentration", 0),
            "format_distribution": data.get("format_distribution") or data.get("market_analysis", {}).get("format_distribution", {}),
            "top_assets": data.get("top_assets") or data.get("assets", [])[:20],
            "contributor_profiles": data.get("contributor_profiles", []),
            "similar_assets": data.get("similar_assets", []),
            "scoring": data.get("scoring", {}),
            "visualizations": data.get("visualizations", {}),
            "errors": data.get("errors", []),
            "scraped_at": data.get("scraped_at") or now,
            "expires_at": expires_at,
            "updated_at": now,
        }
        
        if mask.any():
            idx = self._market_analysis.loc[mask].index[0]
            for k, v in row.items():
                self._market_analysis.at[idx, k] = v
        else:
            row["created_at"] = now
            new_row = pd.DataFrame([row])
            if self._market_analysis.empty:
                self._market_analysis = new_row.copy()
            else:
                self._market_analysis = pd.concat([self._market_analysis, new_row], ignore_index=True)
        self._save()
    
    def get_market_analysis(self, keyword: str, depth: str = "medium") -> Optional[Dict]:
        """Get cached market analysis for a keyword if not expired."""
        keyword_lower = keyword.lower()
        mask = (self._market_analysis["keyword"] == keyword_lower) & (self._market_analysis["analysis_depth"] == depth)
        
        if not mask.any():
            return None
        
        row = self._market_analysis.loc[mask].iloc[0]
        result = self._row_to_dict(row)
        
        # Check if expired
        expires_at = result.get("expires_at")
        if expires_at:
            from datetime import datetime as dt
            if isinstance(expires_at, str):
                try:
                    expires_at = dt.fromisoformat(expires_at.replace("Z", ""))
                except:
                    expires_at = None
            if expires_at and dt.utcnow() > expires_at:
                return None
        
        return result
    
    def get_all_market_analyses(self, limit: int = 50) -> List[Dict]:
        """Get all cached market analyses."""
        df = self._market_analysis.sort_values("scraped_at", ascending=False).head(limit)
        return [self._row_to_dict(row) for _, row in df.iterrows()]
    
    def clean_expired_market_analyses(self) -> int:
        """Remove expired market analysis entries."""
        now = datetime.utcnow()
        initial_count = len(self._market_analysis)
        
        # Convert expires_at to datetime for comparison
        valid_mask = []
        for _, row in self._market_analysis.iterrows():
            expires_at = row.get("expires_at")
            if expires_at is None:
                valid_mask.append(True)
                continue
            if isinstance(expires_at, str):
                try:
                    from datetime import datetime as dt
                    expires_at = dt.fromisoformat(expires_at.replace("Z", ""))
                except:
                    valid_mask.append(True)
                    continue
            valid_mask.append(expires_at > now)
        
        self._market_analysis = self._market_analysis[valid_mask].reset_index(drop=True)
        self._save()
        
        return initial_count - len(self._market_analysis)
    
    # ——— Pandas-specific: raw DataFrames for analysis ———
    def get_assets_df(self) -> pd.DataFrame:
        """Return the full assets DataFrame (read-only view; copy to modify)."""
        return self._assets.copy()

    def get_searches_df(self) -> pd.DataFrame:
        return self._searches.copy()
    
    def get_keyword_metrics_df(self) -> pd.DataFrame:
        return self._keyword_metrics.copy()
    
    def get_niche_scores_df(self) -> pd.DataFrame:
        return self._niche_scores.copy()
    
    def get_contributor_profiles_df(self) -> pd.DataFrame:
        return self._contributor_profiles.copy()
    
    def get_market_analysis_df(self) -> pd.DataFrame:
        return self._market_analysis.copy()
    
    def get_saved_researches_df(self) -> pd.DataFrame:
        return self._saved_researches.copy()
    
    # ——— Saved Research Methods ———
    def save_keyword_research(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Save a keyword research with full deep analysis."""
        keyword = (data.get("keyword") or "").strip().lower()
        if not keyword:
            return {"error": "Keyword required"}
        
        now = datetime.utcnow()
        
        # Check if already saved
        mask = self._saved_researches["keyword"] == keyword
        
        row = {
            "keyword": keyword,
            "analysis_depth": data.get("analysis_depth") or data.get("source", "simple").replace("deep-", "") or "simple",
            "is_opportunity": data.get("is_opportunity", False),
            "saved_at": data.get("saved_at") or now.isoformat(),
            "nb_results": data.get("nb_results", 0),
            "unique_contributors": data.get("unique_contributors", 0),
            "demand_score": data.get("demand_score", 0),
            "competition_score": data.get("competition_score", 0),
            "gap_score": data.get("gap_score", 50),
            "freshness_score": data.get("freshness_score", 50),
            "opportunity_score": data.get("opportunity_score", 0),
            "trend": data.get("trend", "stable"),
            "urgency": data.get("urgency", "medium"),
            "related_searches": data.get("related_searches", []),
            "categories": data.get("categories", []),
            "deep_analysis": data.get("deep_analysis"),  # Full deep analysis data
            "updated_at": now,
        }
        
        if mask.any():
            idx = self._saved_researches.loc[mask].index[0]
            for k, v in row.items():
                self._saved_researches.at[idx, k] = v
        else:
            row["created_at"] = now
            new_row = pd.DataFrame([row])
            if self._saved_researches.empty:
                self._saved_researches = new_row.copy()
            else:
                self._saved_researches = pd.concat([self._saved_researches, new_row], ignore_index=True)
        
        self._save()
        return self._row_to_dict(self._saved_researches.loc[self._saved_researches["keyword"] == keyword].iloc[0])
    
    def get_saved_research(self, keyword: str) -> Optional[Dict]:
        """Get a saved keyword research by keyword."""
        keyword_lower = keyword.lower()
        mask = self._saved_researches["keyword"] == keyword_lower
        
        if not mask.any():
            return None
        
        return self._row_to_dict(self._saved_researches.loc[mask].iloc[0])
    
    def get_all_saved_researches(self, limit: int = 100) -> List[Dict]:
        """Get all saved keyword researches."""
        df = self._saved_researches.sort_values("saved_at", ascending=False).head(limit)
        return [self._row_to_dict(row) for _, row in df.iterrows()]
    
    def get_opportunity_researches(self, limit: int = 50) -> List[Dict]:
        """Get all researches marked as opportunities."""
        mask = self._saved_researches["is_opportunity"] == True
        df = self._saved_researches[mask].sort_values("opportunity_score", ascending=False).head(limit)
        return [self._row_to_dict(row) for _, row in df.iterrows()]
    
    def update_research_opportunity(self, keyword: str, is_opportunity: bool) -> bool:
        """Toggle the opportunity status of a saved research."""
        keyword_lower = keyword.lower()
        mask = self._saved_researches["keyword"] == keyword_lower
        
        if not mask.any():
            return False
        
        idx = self._saved_researches.loc[mask].index[0]
        self._saved_researches.at[idx, "is_opportunity"] = is_opportunity
        self._saved_researches.at[idx, "updated_at"] = datetime.utcnow()
        self._save()
        return True
    
    def delete_saved_research(self, keyword: str) -> bool:
        """Delete a saved keyword research."""
        keyword_lower = keyword.lower()
        mask = self._saved_researches["keyword"] == keyword_lower
        
        if not mask.any():
            return False
        
        self._saved_researches = self._saved_researches[~mask].reset_index(drop=True)
        self._save()
        return True
