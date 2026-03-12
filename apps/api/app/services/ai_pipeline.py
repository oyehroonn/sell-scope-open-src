"""AI Pipeline Service - Embeddings, Captioning, and Keyword Generation"""

from typing import List, Dict, Any, Optional
import asyncio
from io import BytesIO
import structlog

logger = structlog.get_logger()

try:
    import torch
    from PIL import Image
    from transformers import (
        CLIPProcessor,
        CLIPModel,
        BlipProcessor,
        BlipForConditionalGeneration,
    )
    HAS_AI_DEPS = True
except ImportError:
    HAS_AI_DEPS = False
    logger.warning("AI dependencies not installed. Install torch and transformers for local AI.")


class AIProcessor:
    """Local AI processing for embeddings and captioning"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.device = "cuda" if HAS_AI_DEPS and torch.cuda.is_available() else "cpu"
        self.clip_model = None
        self.clip_processor = None
        self.blip_model = None
        self.blip_processor = None
        self._initialized = True
        
        logger.info("AI Processor initialized", device=self.device)
    
    async def load_clip(self):
        """Load CLIP model for embeddings"""
        if not HAS_AI_DEPS:
            raise RuntimeError("AI dependencies not installed")
        
        if self.clip_model is None:
            logger.info("Loading CLIP model...")
            self.clip_model = CLIPModel.from_pretrained(
                "openai/clip-vit-base-patch32"
            ).to(self.device)
            self.clip_processor = CLIPProcessor.from_pretrained(
                "openai/clip-vit-base-patch32"
            )
            logger.info("CLIP model loaded")
    
    async def load_blip(self):
        """Load BLIP model for captioning"""
        if not HAS_AI_DEPS:
            raise RuntimeError("AI dependencies not installed")
        
        if self.blip_model is None:
            logger.info("Loading BLIP model...")
            self.blip_model = BlipForConditionalGeneration.from_pretrained(
                "Salesforce/blip-image-captioning-base"
            ).to(self.device)
            self.blip_processor = BlipProcessor.from_pretrained(
                "Salesforce/blip-image-captioning-base"
            )
            logger.info("BLIP model loaded")
    
    async def get_image_embedding(self, image: Image.Image) -> List[float]:
        """Generate embedding for an image using CLIP"""
        await self.load_clip()
        
        inputs = self.clip_processor(images=image, return_tensors="pt").to(self.device)
        
        with torch.no_grad():
            image_features = self.clip_model.get_image_features(**inputs)
            embedding = image_features / image_features.norm(dim=-1, keepdim=True)
        
        return embedding.cpu().numpy().flatten().tolist()
    
    async def get_text_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using CLIP"""
        await self.load_clip()
        
        inputs = self.clip_processor(text=[text], return_tensors="pt", padding=True).to(self.device)
        
        with torch.no_grad():
            text_features = self.clip_model.get_text_features(**inputs)
            embedding = text_features / text_features.norm(dim=-1, keepdim=True)
        
        return embedding.cpu().numpy().flatten().tolist()
    
    async def generate_caption(self, image: Image.Image) -> str:
        """Generate caption for an image using BLIP"""
        await self.load_blip()
        
        inputs = self.blip_processor(images=image, return_tensors="pt").to(self.device)
        
        with torch.no_grad():
            generated_ids = self.blip_model.generate(**inputs, max_length=50)
            caption = self.blip_processor.decode(generated_ids[0], skip_special_tokens=True)
        
        return caption
    
    async def generate_keywords_from_image(self, image: Image.Image) -> List[str]:
        """Generate keywords from an image using captioning and embedding similarity"""
        caption = await self.generate_caption(image)
        
        keywords = self._extract_keywords_from_caption(caption)
        
        related_keywords = await self._find_related_keywords(caption)
        
        all_keywords = list(set(keywords + related_keywords))
        
        return all_keywords[:50]
    
    def _extract_keywords_from_caption(self, caption: str) -> List[str]:
        """Extract keywords from a caption"""
        stop_words = {
            "a", "an", "the", "is", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "must", "shall",
            "can", "to", "of", "in", "for", "on", "with", "at", "by",
            "from", "as", "into", "through", "during", "before", "after",
            "above", "below", "between", "under", "again", "further",
            "then", "once", "here", "there", "when", "where", "why",
            "how", "all", "each", "few", "more", "most", "other", "some",
            "such", "no", "nor", "not", "only", "own", "same", "so",
            "than", "too", "very", "just", "and", "but", "if", "or",
            "because", "until", "while", "this", "that", "these", "those",
        }
        
        words = caption.lower().replace(",", " ").replace(".", " ").split()
        
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        
        return keywords
    
    async def _find_related_keywords(self, text: str) -> List[str]:
        """Find semantically related keywords"""
        keyword_categories = {
            "business": ["office", "corporate", "professional", "meeting", "work", "team"],
            "technology": ["digital", "computer", "phone", "app", "software", "device"],
            "nature": ["outdoor", "landscape", "garden", "plant", "flower", "tree"],
            "lifestyle": ["home", "family", "leisure", "relaxation", "wellness"],
            "food": ["meal", "cooking", "kitchen", "restaurant", "healthy", "fresh"],
        }
        
        text_lower = text.lower()
        related = []
        
        for category, keywords in keyword_categories.items():
            for keyword in keywords:
                if keyword in text_lower:
                    related.extend(keyword_categories[category])
                    break
        
        return list(set(related))
    
    async def compute_similarity(
        self,
        embedding1: List[float],
        embedding2: List[float],
    ) -> float:
        """Compute cosine similarity between two embeddings"""
        import numpy as np
        
        e1 = np.array(embedding1)
        e2 = np.array(embedding2)
        
        similarity = np.dot(e1, e2) / (np.linalg.norm(e1) * np.linalg.norm(e2))
        
        return float(similarity)


ai_processor = AIProcessor()


async def process_image_for_embedding(image_bytes: bytes) -> Dict[str, Any]:
    """Process an image and return embedding + metadata"""
    if not HAS_AI_DEPS:
        return {
            "embedding": None,
            "caption": None,
            "keywords": [],
            "error": "AI dependencies not installed",
        }
    
    try:
        image = Image.open(BytesIO(image_bytes)).convert("RGB")
        
        embedding = await ai_processor.get_image_embedding(image)
        caption = await ai_processor.generate_caption(image)
        keywords = await ai_processor.generate_keywords_from_image(image)
        
        return {
            "embedding": embedding,
            "caption": caption,
            "keywords": keywords,
            "error": None,
        }
    except Exception as e:
        logger.error("Error processing image", error=str(e))
        return {
            "embedding": None,
            "caption": None,
            "keywords": [],
            "error": str(e),
        }


async def batch_process_images(images: List[bytes]) -> List[Dict[str, Any]]:
    """Process multiple images concurrently"""
    tasks = [process_image_for_embedding(img) for img in images]
    results = await asyncio.gather(*tasks)
    return results


async def generate_keywords_for_text(text: str) -> List[str]:
    """Generate relevant keywords for a text description"""
    if not HAS_AI_DEPS:
        return ai_processor._extract_keywords_from_caption(text)
    
    try:
        keywords = ai_processor._extract_keywords_from_caption(text)
        related = await ai_processor._find_related_keywords(text)
        return list(set(keywords + related))[:50]
    except Exception as e:
        logger.error("Error generating keywords", error=str(e))
        return ai_processor._extract_keywords_from_caption(text)
