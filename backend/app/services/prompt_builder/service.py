class PromptBuilder:

    def build(
        self,
        history: list,
        context: str,
        question: str,
    ) -> str:

        return (
            self._system_prompt()
            + self._history(history)
            + self._context(context)
            + self._question(question)
        )

    def _system_prompt(
        self,
    ) -> str:

        return """
# ROLE

You are an AI Document Assistant.

# INSTRUCTIONS

- Answer ONLY using the provided document context.
- Use previous conversation only for follow-up questions.
- Never use outside knowledge.
- Never hallucinate.
- If the answer is unavailable, reply exactly:
"I couldn't find this information in the uploaded document."
- Be clear, concise, and accurate.
- Use bullet points when appropriate.

"""

    def _history(
        self,
        history: list,
    ) -> str:

        conversation = ""

        for message in history:

            conversation += (
                f"{message.role}: "
                f"{message.content}\n"
            )

        return (
            "# PREVIOUS CONVERSATION\n\n"
            f"{conversation}\n"
        )

    def _context(
        self,
        context: str,
    ) -> str:

        return (
            "# DOCUMENT CONTEXT\n\n"
            f"{context}\n"
        )

    def _question(
        self,
        question: str,
    ) -> str:

        return (
            "# CURRENT QUESTION\n\n"
            f"{question}\n"
        )