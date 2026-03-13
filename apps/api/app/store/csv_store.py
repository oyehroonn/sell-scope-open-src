"""
CSV-backed in-memory store. Replaces Postgres for assets, searches, contributors,
keywords, search_results, similar_assets, asset_keywords, categories, asset_categories.
Loads all CSVs at startup; writes back on every mutation.
"""

import csv
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.config import settings

# Default data dir: under app (apps/api/data) or cwd
def _data_dir() -> Path:
    p = getattr(settings, "DATA_DIR", "data")
    if os.path.isabs(p):
        return Path(p)
    # Prefer next to app (apps/api)
    app_dir = Path(__file__).resolve().parent.parent.parent
    return (app_dir / p).resolve()


# CSV filenames and headers (order matters for DictWriter)
CSV_SPECS = {
    "searches": ["term", "total_results_available", "scraped_at", "created_at"],
    "assets": [
        "adobe_id", "title", "description", "keywords", "contributor_id", "contributor_name",
        "asset_type", "category", "category_name", "width", "height", "orientation",
        "thumbnail_url", "preview_url", "asset_url", "file_format", "creation_date",
        "is_premium", "is_editorial", "is_ai_generated", "estimated_downloads", "similar_count",
        "color_palette", "style_tags", "source", "scraped_at", "created_at", "updated_at",
    ],
    "contributors": ["adobe_id", "name", "profile_url", "portfolio_url", "scraped_at", "created_at", "updated_at"],
    "keywords": ["term", "normalized_term", "type", "search_volume_estimate", "competition_level", "category_name", "related_keywords", "last_scraped_at", "created_at", "updated_at"],
    "search_results": ["search_term", "asset_adobe_id", "position", "page", "scraped_at", "created_at"],
    "similar_assets": ["main_asset_adobe_id", "similar_asset_adobe_id", "rank", "scraped_at", "created_at"],
    "asset_keywords": ["asset_adobe_id", "keyword_term", "source", "created_at"],
    "categories": ["name", "created_at"],
    "asset_categories": ["asset_adobe_id", "category_name", "created_at"],
}

# Columns that store JSON (list or dict)
JSON_COLUMNS = {
    "assets": ["keywords", "color_palette", "style_tags"],
    "keywords": ["related_keywords"],
}


def _serialize_row(row: Dict[str, Any], table: str) -> Dict[str, Any]:
    out = {}
    for k, v in row.items():
        if k not in CSV_SPECS.get(table, []):
            continue
        if table in JSON_COLUMNS and k in JSON_COLUMNS[table]:
            out[k] = json.dumps(v) if v is not None else ""
        elif isinstance(v, datetime):
            out[k] = v.isoformat() if v else ""
        elif isinstance(v, bool):
            out[k] = "true" if v else "false"
        else:
            out[k] = "" if v is None else str(v)
    return out


def _parse_row(raw: Dict[str, str], table: str) -> Dict[str, Any]:
    out = {}
    for k, v in raw.items():
        if table in JSON_COLUMNS and k in JSON_COLUMNS[table]:
            try:
                out[k] = json.loads(v) if v else None
            except Exception:
                out[k] = None
        elif k in ("scraped_at", "created_at", "updated_at", "creation_date", "last_scraped_at"):
            try:
                out[k] = datetime.fromisoformat(v.replace("Z", "+00:00")) if v else None
            except Exception:
                out[k] = None
        elif k in ("is_premium", "is_editorial", "is_ai_generated"):
            out[k] = (v or "").lower() in ("true", "1", "yes")
        elif k in ("width", "height", "position", "page", "rank", "total_results_available", "estimated_downloads", "similar_count", "search_volume_estimate"):
            try:
                out[k] = int(v) if v else None
            except Exception:
                out[k] = None
        elif k == "competition_level":
            try:
                out[k] = float(v) if v else None
            except Exception:
                out[k] = None
        else:
            out[k] = v or None
    return out


class CSVStore:
    def __init__(self, data_dir: Optional[Path] = None):
        self._dir = data_dir or _data_dir()
        self._dir.mkdir(parents=True, exist_ok=True)
        # In-memory: list or dict per table
        self._searches: List[Dict] = []
        self._assets: Dict[str, Dict] = {}
        self._contributors: Dict[str, Dict] = {}
        self._keywords: Dict[str, Dict] = {}
        self._search_results: List[Dict] = []
        self._similar_assets: List[Dict] = []
        self._asset_keywords: List[Dict] = []
        self._categories: Dict[str, Dict] = {}
        self._asset_categories: List[Dict] = []

    def load_all(self) -> None:
        """Load all CSVs into memory. Create files with headers if missing."""
        for table, headers in CSV_SPECS.items():
            path = self._dir / f"{table}.csv"
            if not path.exists():
                with open(path, "w", newline="", encoding="utf-8") as f:
                    w = csv.DictWriter(f, fieldnames=headers)
                    w.writeheader()
                setattr(self, f"_{table}", [] if table in ("search_results", "similar_assets", "asset_keywords", "asset_categories") else {} if table in ("assets", "contributors", "keywords", "categories") else [])
                if table == "searches":
                    setattr(self, "_searches", [])
                continue
            with open(path, "r", encoding="utf-8", newline="") as f:
                r = csv.DictReader(f)
                rows = [_parse_row(dict(row), table) for row in r]
            if table == "searches":
                self._searches = rows
            elif table == "assets":
                self._assets = {r["adobe_id"]: r for r in rows if r.get("adobe_id")}
            elif table == "contributors":
                self._contributors = {r["adobe_id"]: r for r in rows if r.get("adobe_id")}
            elif table == "keywords":
                self._keywords = {r["term"]: r for r in rows if r.get("term")}
            elif table == "search_results":
                self._search_results = rows
            elif table == "similar_assets":
                self._similar_assets = rows
            elif table == "asset_keywords":
                self._asset_keywords = rows
            elif table == "categories":
                self._categories = {r["name"]: r for r in rows if r.get("name")}
            elif table == "asset_categories":
                self._asset_categories = rows

    def _save_csv(self, table: str, rows: List[Dict]) -> None:
        headers = CSV_SPECS[table]
        path = self._dir / f"{table}.csv"
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
            w.writeheader()
            for r in rows:
                w.writerow(_serialize_row(r, table))

    # ——— Searches ———
    def upsert_search(self, term: str, total_results_available: Optional[int] = None, scraped_at: Optional[datetime] = None) -> None:
        term = (term or "").strip().lower()
        if not term:
            return
        now = datetime.utcnow()
        scraped_at = scraped_at or now
        for s in self._searches:
            if s.get("term") == term:
                s["total_results_available"] = total_results_available if total_results_available is not None else s.get("total_results_available")
                s["scraped_at"] = scraped_at
                self._save_csv("searches", self._searches)
                return
        self._searches.append({
            "term": term,
            "total_results_available": total_results_available or 0,
            "scraped_at": scraped_at,
            "created_at": now,
        })
        self._save_csv("searches", self._searches)

    def get_searches(self, limit: int = 50) -> List[Dict]:
        by_time = sorted(
            [s for s in self._searches if s.get("scraped_at")],
            key=lambda s: s["scraped_at"] or datetime.min,
            reverse=True,
        )
        return by_time[:limit]

    # ——— Contributors ———
    def upsert_contributor(self, adobe_id: str, name: Optional[str] = None, profile_url: Optional[str] = None, portfolio_url: Optional[str] = None) -> None:
        if not adobe_id:
            return
        now = datetime.utcnow()
        if adobe_id in self._contributors:
            c = self._contributors[adobe_id]
            if name is not None:
                c["name"] = name
            if profile_url is not None:
                c["profile_url"] = profile_url
            if portfolio_url is not None:
                c["portfolio_url"] = portfolio_url
            c["updated_at"] = now
        else:
            self._contributors[adobe_id] = {
                "adobe_id": adobe_id,
                "name": name,
                "profile_url": profile_url,
                "portfolio_url": portfolio_url,
                "scraped_at": now,
                "created_at": now,
                "updated_at": now,
            }
        self._save_csv("contributors", list(self._contributors.values()))

    def get_contributors(self) -> List[Dict]:
        return list(self._contributors.values())

    # ——— Keywords ———
    def upsert_keyword(self, term: str, kw_type: str = "asset") -> Optional[Dict]:
        term = (term or "").strip().lower()
        if not term or len(term) > 500:
            return None
        now = datetime.utcnow()
        if term in self._keywords:
            return self._keywords[term]
        self._keywords[term] = {
            "term": term,
            "normalized_term": term,
            "type": kw_type,
            "search_volume_estimate": None,
            "competition_level": None,
            "category_name": None,
            "related_keywords": None,
            "last_scraped_at": None,
            "created_at": now,
            "updated_at": now,
        }
        self._save_csv("keywords", list(self._keywords.values()))
        return self._keywords[term]

    def get_keywords(self) -> List[Dict]:
        return list(self._keywords.values())

    # ——— Categories ———
    def upsert_category(self, name: str) -> None:
        name = (name or "").strip()
        if not name:
            return
        now = datetime.utcnow()
        if name not in self._categories:
            self._categories[name] = {"name": name, "created_at": now}
            self._save_csv("categories", list(self._categories.values()))

    def add_asset_category(self, asset_adobe_id: str, category_name: str) -> None:
        category_name = (category_name or "").strip()
        if not asset_adobe_id or not category_name:
            return
        now = datetime.utcnow()
        if any(r["asset_adobe_id"] == asset_adobe_id and r["category_name"] == category_name for r in self._asset_categories):
            return
        self._asset_categories.append({
            "asset_adobe_id": asset_adobe_id,
            "category_name": category_name,
            "created_at": now,
        })
        self._save_csv("asset_categories", self._asset_categories)

    # ——— Assets ———
    def upsert_asset(self, data: Dict[str, Any], scraped_data: Optional[Dict[str, Any]] = None) -> None:
        # scraped_data ignored for CSV (no nested column); used by PandasStore
        adobe_id = str((data.get("adobe_id") or ""))
        if not adobe_id:
            return
        now = datetime.utcnow()
        existing = self._assets.get(adobe_id)
        if existing:
            for k, v in data.items():
                if k in CSV_SPECS["assets"] and v is not None:
                    existing[k] = v
            existing["updated_at"] = now
        else:
            row = {h: None for h in CSV_SPECS["assets"]}
            row["adobe_id"] = adobe_id
            row["created_at"] = now
            row["updated_at"] = now
            for k, v in data.items():
                if k in CSV_SPECS["assets"]:
                    row[k] = v
            self._assets[adobe_id] = row
        self._save_csv("assets", list(self._assets.values()))

    def get_asset(self, adobe_id: str) -> Optional[Dict]:
        return self._assets.get(str(adobe_id))

    def get_all_assets(
        self,
        offset: int = 0,
        limit: int = 50,
        asset_type: Optional[str] = None,
        contributor_id: Optional[str] = None,
        is_premium: Optional[bool] = None,
        search: Optional[str] = None,
    ) -> tuple[List[Dict], int]:
        items = list(self._assets.values())
        if asset_type:
            items = [a for a in items if a.get("asset_type") == asset_type]
        if contributor_id:
            items = [a for a in items if a.get("contributor_id") == contributor_id]
        if is_premium is not None:
            items = [a for a in items if a.get("is_premium") is is_premium]
        if search:
            s = (search or "").lower()
            items = [a for a in items if (a.get("title") or "").lower().find(s) >= 0 or (a.get("contributor_name") or "").lower().find(s) >= 0]
        items.sort(key=lambda a: a.get("scraped_at") or datetime.min, reverse=True)
        total = len(items)
        return items[offset : offset + limit], total

    def delete_asset(self, adobe_id: str) -> bool:
        adobe_id = str(adobe_id)
        if adobe_id not in self._assets:
            return False
        del self._assets[adobe_id]
        self._search_results = [r for r in self._search_results if r.get("asset_adobe_id") != adobe_id]
        self._similar_assets = [r for r in self._similar_assets if r.get("main_asset_adobe_id") != adobe_id and r.get("similar_asset_adobe_id") != adobe_id]
        self._asset_keywords = [r for r in self._asset_keywords if r.get("asset_adobe_id") != adobe_id]
        self._asset_categories = [r for r in self._asset_categories if r.get("asset_adobe_id") != adobe_id]
        self._save_csv("assets", list(self._assets.values()))
        self._save_csv("search_results", self._search_results)
        self._save_csv("similar_assets", self._similar_assets)
        self._save_csv("asset_keywords", self._asset_keywords)
        self._save_csv("asset_categories", self._asset_categories)
        return True

    # ——— Search results ———
    def add_search_result(self, search_term: str, asset_adobe_id: str, position: int = 0, page: int = 1) -> None:
        now = datetime.utcnow()
        self._search_results.append({
            "search_term": search_term.strip().lower(),
            "asset_adobe_id": str(asset_adobe_id),
            "position": position,
            "page": page,
            "scraped_at": now,
            "created_at": now,
        })
        self._save_csv("search_results", self._search_results)

    def get_search_results(self, search_term: str) -> List[Dict]:
        term = (search_term or "").strip().lower()
        return [r for r in self._search_results if r.get("search_term") == term]

    # ——— Similar assets ———
    def add_similar(self, main_asset_adobe_id: str, similar_asset_adobe_id: str, rank: int = 0) -> None:
        if not main_asset_adobe_id or not similar_asset_adobe_id:
            return
        now = datetime.utcnow()
        self._similar_assets.append({
            "main_asset_adobe_id": str(main_asset_adobe_id),
            "similar_asset_adobe_id": str(similar_asset_adobe_id),
            "rank": rank,
            "scraped_at": now,
            "created_at": now,
        })
        self._save_csv("similar_assets", self._similar_assets)

    def get_similar(self, main_asset_adobe_id: str, limit: int = 20) -> List[Dict]:
        main = str(main_asset_adobe_id)
        pairs = [r for r in self._similar_assets if r.get("main_asset_adobe_id") == main]
        pairs.sort(key=lambda r: r.get("rank", 0))
        out = []
        for r in pairs[:limit]:
            sim = self._assets.get(r.get("similar_asset_adobe_id", ""))
            if sim:
                out.append({
                    "adobe_id": sim.get("adobe_id"),
                    "title": sim.get("title"),
                    "thumbnail_url": sim.get("thumbnail_url"),
                    "preview_url": sim.get("preview_url"),
                })
        return out

    # ——— Asset keywords ———
    def add_asset_keyword(self, asset_adobe_id: str, keyword_term: str, source: str = "meta") -> None:
        keyword_term = (keyword_term or "").strip().lower()
        if not asset_adobe_id or not keyword_term or len(keyword_term) > 500:
            return
        if any(r["asset_adobe_id"] == str(asset_adobe_id) and r["keyword_term"] == keyword_term and r.get("source") == source for r in self._asset_keywords):
            return
        now = datetime.utcnow()
        self._asset_keywords.append({
            "asset_adobe_id": str(asset_adobe_id),
            "keyword_term": keyword_term,
            "source": source,
            "created_at": now,
        })
        self._save_csv("asset_keywords", self._asset_keywords)

    def get_asset_keywords(self, asset_adobe_id: str) -> List[str]:
        aid = str(asset_adobe_id)
        return [r["keyword_term"] for r in self._asset_keywords if r.get("asset_adobe_id") == aid]

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
        from collections import Counter
        counts: Counter = Counter()
        for r in self._asset_keywords:
            t = r.get("keyword_term")
            if t:
                counts[t] += 1
        return [{"term": t, "asset_count": c} for t, c in counts.most_common(limit)]

    def get_top_contributors(self, limit: int = 50) -> List[Dict]:
        from collections import Counter
        counts: Counter = Counter()
        for a in self._assets.values():
            cid = a.get("contributor_id")
            if cid:
                counts[(cid, a.get("contributor_name"))] += 1
        return [
            {"adobe_id": cid, "name": name, "asset_count": c}
            for (cid, name), c in counts.most_common(limit)
        ]

    def get_all_asset_rows(self) -> List[Dict]:
        """All asset rows (for stats aggregation)."""
        return list(self._assets.values())


# Singleton; initialized when USE_CSV_STORE and loaded in lifespan
csv_store: Optional[CSVStore] = None


def get_store() -> CSVStore:
    global csv_store
    if csv_store is None:
        csv_store = CSVStore()
        csv_store.load_all()
    return csv_store


def init_store() -> CSVStore:
    """Call once at app startup to load CSVs."""
    return get_store()
