"""Database models"""

from app.models.user import User
from app.models.keyword import Keyword, KeywordRanking
from app.models.asset import Asset, AssetEmbedding
from app.models.portfolio import Portfolio, PortfolioAsset
from app.models.opportunity import OpportunityScore, Niche
from app.models.scrape import ScrapeJob, ScrapeResult
from app.models.automation import Webhook, AutomationConfig
from app.models.contributor import Contributor
from app.models.search import Search, SearchResult
from app.models.similar import SimilarAsset
from app.models.category import Category, AssetCategory
from app.models.asset_keyword import AssetKeyword
from app.models.contributor_highlight import ContributorHighlight
from app.models.asset_metadata import AssetMetadata

__all__ = [
    "User",
    "Keyword",
    "KeywordRanking",
    "Asset",
    "AssetEmbedding",
    "Portfolio",
    "PortfolioAsset",
    "OpportunityScore",
    "Niche",
    "ScrapeJob",
    "ScrapeResult",
    "Webhook",
    "AutomationConfig",
    "Contributor",
    "Search",
    "SearchResult",
    "SimilarAsset",
    "Category",
    "AssetCategory",
    "AssetKeyword",
    "ContributorHighlight",
    "AssetMetadata",
]
