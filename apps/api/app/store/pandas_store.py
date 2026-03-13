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
        }
        with open(self._path, "wb") as f:
            pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)

    @staticmethod
    def _row_to_dict(row: pd.Series) -> Dict[str, Any]:
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

    # ——— Pandas-specific: raw DataFrames for analysis ———
    def get_assets_df(self) -> pd.DataFrame:
        """Return the full assets DataFrame (read-only view; copy to modify)."""
        return self._assets.copy()

    def get_searches_df(self) -> pd.DataFrame:
        return self._searches.copy()
