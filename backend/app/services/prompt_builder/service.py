class PromptBuilder:

    def build(
        self,
        history: list,
        context: str,
        question: str,
        summary: str | None = None,
    ) -> str:

        sections = [
            self._system_prompt(),
            self._history(history),
            self._context(context),
            self._question(question),
            self._summary(summary),
        ]

        return "\n".join(sections)

    def _system_prompt(self) -> str:

        return """
    # ROLE

    You are an AI Document Assistant.

    # OBJECTIVE

    Answer questions ONLY using the provided document context.

    The context may come from one or more uploaded documents.

    Each context section contains:
    - Document name
    - Page number
    - Chunk number
    - Content

    # RULES

    - Use ONLY the provided document context.
    - Never use outside knowledge.
    - Use previous conversation ONLY for follow-up questions.
    - If information comes from multiple documents, combine it into one answer.
    - If documents contain conflicting information, clearly mention the conflict.
    - If the answer exists in only one document, mention which document it comes from.
    - Never invent information.
    - If the answer is unavailable, reply exactly:

    "I couldn't find this information in the uploaded documents."

    - Keep responses concise.
    - Use headings and bullet points when appropriate.
    """

    def _history(
        self,
        history: list,
    ) -> str:

        if not history:
            return ""

        conversation = []

        for message in history[-10:]:      # Keep last 10 messages only
            conversation.append(
                f"{message.role}: {message.content}"
            )

        return (
            "# CONVERSATION HISTORY\n\n"
            + "\n".join(conversation)
        )

    def _context(
        self,
        context: str,
    ) -> str:

        return (
            "# DOCUMENT CONTEXT\n\n"
            f"{context}"
        )

    def _summary(
        self,
        summary: str | None,
    ):

        if not summary:
            return ""

        return (
            "# CONVERSATION SUMMARY\n\n"
            f"{summary}"
        )

    def _question(
        self,
        question: str,
    ) -> str:

        return (
            "# USER QUESTION\n\n"
            f"{question}"
        )