import asyncio
from collections import defaultdict

from app.services.ai.prompts.vision_prompt import (
    VISION_ANALYSIS_PROMPT,
)
from app.services.ai.service import AIService
from app.services.ai.vision.gemini import GeminiVision
from app.services.ai.vision.groq import GroqVision
from app.services.ai.vision.router import VisionRouter


class VisionService:

    MAX_IMAGES_PER_PAGE_REQUEST = 2
    MAX_VISION_PAGES = 5

    VISION_TIMEOUT_SECONDS = 15

    def __init__(
        self,
        document_image_service,
        ai_service: AIService | None = None,
    ):

        self.ai_service = (
            ai_service or AIService()
        )

        self.vision_router = VisionRouter(
            providers=[
                GeminiVision(),
                GroqVision(),
            ]
        )

        self.document_image_service = (
            document_image_service
        )

    def _build_page_prompt(
        self,
        prompt: str,
        page_number: int,
    ) -> str:

        base_prompt = (
            VISION_ANALYSIS_PROMPT.strip()
        )

        if prompt.strip() == base_prompt:

            user_request = (
                "Describe and identify the "
                "provided document image."
            )

        else:

            user_request = prompt.strip()

        return f"""
{base_prompt}

PAGE CONTEXT
Page number: {page_number}

USER REQUEST
{user_request}

PAGE IMAGE RULES
- All images in this request belong to page {page_number}.
- Analyze them together when there is more than one image.
- They may be crops or sections of the same page.
- Combine related information into ONE answer.
- Include all relevant visible information needed to answer the request.
- If the page contains both visual elements and readable text, consider both.
- Use only information actually visible in the images.
- If text is unclear, say that it is unclear.
- Do not guess missing labels, values, relationships, or structure.

FINAL OUTPUT RULE
Return ONLY the final visible answer.
Do NOT output reasoning.
Do NOT output analysis.
Do NOT output <think> or </think>.
Start directly with the requested answer.
""".strip()

    async def _prepare_images(
        self,
        images: list[dict],
    ) -> list[dict]:

        vision_images = []

        for image in images:

            image_bytes = (
                await self.document_image_service
                .load_image_bytes(image)
            )

            if not image_bytes:
                continue

            vision_images.append(
                {
                    "bytes": image_bytes,
                    "extension": image.get(
                        "extension",
                        "jpeg",
                    ),
                    "document_id": image[
                        "document_id"
                    ],
                    "page_number": image[
                        "page_number"
                    ],
                    "image_index": image[
                        "image_index"
                    ],
                }
            )

        return vision_images

    async def _analyze_page_batch(
        self,
        page_prompt: str,
        batch: list[dict],
        page_number: int,
    ) -> str:
        """
        Make ONE request to VisionRouter.

        VisionRouter is responsible for:
        Gemini 429 -> Groq fallback
        503 -> limited retry
        timeout -> limited retry

        This method intentionally does NOT retry the
        complete provider chain.
        """

        try:

            print(
                "VISION REQUEST:",
                "page=",
                page_number,
                "| images=",
                len(batch),
            )

            result = await asyncio.wait_for(
                self.vision_router.analyze_images(
                    prompt=page_prompt,
                    images=batch,
                ),
                timeout=(
                    self.VISION_TIMEOUT_SECONDS
                ),
            )

            return result or ""

        except TimeoutError:

            print(
                "Vision request timeout:",
                f"page={page_number}",
                f"timeout="
                f"{self.VISION_TIMEOUT_SECONDS}s",
            )

            return ""

        except Exception as exception:

            print(
                "Vision page analysis failed:",
                f"page={page_number}",
                f"error={exception}",
            )

            return ""

    async def analyze_images_by_page(
        self,
        images: list[dict],
        prompt: str,
    ) -> list[dict]:

        if not images:
            return []

        grouped = defaultdict(list)

        for image in images:

            key = (
                image["document_id"],
                image["page_number"],
            )

            grouped[key].append(image)

        page_groups = sorted(
            grouped.items(),
            key=lambda item: (
                item[0][0],
                item[0][1],
            ),
        )

        page_groups = page_groups[
            :self.MAX_VISION_PAGES
        ]

        results = []

        for (
            document_id,
            page_number,
        ), page_images in page_groups:

            print(
                "VISION PAGE:",
                page_number,
                "| images:",
                len(page_images),
            )

            vision_images = (
                await self._prepare_images(
                    page_images
                )
            )

            if not vision_images:
                continue

            page_results = []

            for start in range(
                0,
                len(vision_images),
                self.MAX_IMAGES_PER_PAGE_REQUEST,
            ):

                batch = vision_images[
                    start:
                    start
                    + self.MAX_IMAGES_PER_PAGE_REQUEST
                ]

                page_prompt = (
                    self._build_page_prompt(
                        prompt=prompt,
                        page_number=page_number,
                    )
                )

                result = (
                    await self._analyze_page_batch(
                        page_prompt=page_prompt,
                        batch=batch,
                        page_number=page_number,
                    )
                )

                if result:
                    page_results.append(
                        result
                    )

            if page_results:

                results.append(
                    {
                        "document_id": document_id,
                        "page_number": page_number,
                        "image_count": len(
                            vision_images
                        ),
                        "result": "\n\n".join(
                            page_results
                        ),
                    }
                )

        return results

    async def analyze_images(
        self,
        images: list[dict],
    ) -> str:

        if not images:
            return ""

        results = (
            await self.analyze_images_by_page(
                images=images,
                prompt=VISION_ANALYSIS_PROMPT,
            )
        )

        if not results:
            return ""

        output = []

        for result in results:

            if not result.get("result"):
                continue

            output.append(
                f"Page "
                f"{result['page_number']}:\n"
                f"{result['result']}"
            )

        return "\n\n".join(output)
