from abc import ABC, abstractmethod


class VisionProvider(ABC):
    """Base interface for AI vision providers."""

    @abstractmethod
    async def analyze_images(
        self,
        prompt: str,
        images: list[dict],
    ) -> str:
        """
        Analyze images using the vision provider.

        Args:
            prompt: Instructions for visual analysis.
            images: Images and their metadata.

        Returns:
            The provider's textual analysis.
        """
        raise NotImplementedError