
import numpy as np
from loguru import logger

from app.embeddings.interface import BaseEmbeddingGenerator


class SentenceTransformerGenerator(BaseEmbeddingGenerator):
    """Generates dense vector embeddings using SentenceTransformers."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initializes the SentenceTransformer model.

        Args:
            model_name: Name of the SentenceTransformer model to load.
        """
        logger.info(f"Initializing SentenceTransformer model: '{model_name}'")
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model_name)
            logger.info("SentenceTransformer model loaded successfully.")
        except Exception as e:
            logger.warning(
                f"Failed to load sentence-transformers model '{model_name}'. "
                f"Falling back to deterministic mock embedding generator. Error: {str(e)}"
            )
            self.model = None

    def generate_embedding(self, text: str) -> list[float]:
        """Generates dense vector representation for a single text.

        Args:
            text: Input string.

        Returns:
            Dense float list representing vector embeddings.
        """
        if not text:
            return [0.0] * 384

        if self.model is not None:
            try:
                emb = self.model.encode(text)
                return [float(val) for val in emb]
            except Exception as e:
                logger.error(f"Error generating embedding from SentenceTransformers: {str(e)}")
                # Fallback to mock

        # Deterministic mock embedding based on string contents to keep it consistent
        return self._generate_mock_embedding(text)

    def generate_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        """Generates embeddings for a batch of strings.

        Args:
            texts: List of strings.

        Returns:
            List of dense float lists representing vector embeddings.
        """
        if not texts:
            return []

        if self.model is not None:
            try:
                embs = self.model.encode(texts)
                return [[float(val) for val in emb] for emb in embs]
            except Exception as e:
                logger.error(f"Error generating batch embeddings from SentenceTransformers: {str(e)}")
                # Fallback to mock

        return [self._generate_mock_embedding(t) for t in texts]

    def _generate_mock_embedding(self, text: str) -> list[float]:
        """Helper to generate a deterministic 384-dimensional vector from text."""
        # Use simple hash seed
        val_sum = sum(ord(c) for c in text) if text else 1
        rng = np.random.default_rng(val_sum)
        vector = rng.standard_normal(384)
        # Normalize to unit length
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        return [float(val) for val in vector]
