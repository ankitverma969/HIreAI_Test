from abc import ABC, abstractmethod


class BaseEmbeddingGenerator(ABC):
    """Abstract Base Class for text embedding generation wrappers."""

    @abstractmethod
    def generate_embedding(self, text: str) -> list[float]:
        """Generates dense vector representation for a single text.

        Args:
            text: Input string.

        Returns:
            Dense float list representing vector embeddings.
        """
        pass

    @abstractmethod
    def generate_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        """Generates embeddings for a batch of strings.

        Args:
            texts: List of strings.

        Returns:
            List of dense float lists representing vector embeddings.
        """
        pass
