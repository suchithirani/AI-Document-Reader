class TokenBudgetService:

    def __init__(
        self,
        max_characters: int = 4000,
    ):
        self.max_characters = max_characters

    def apply(
        self,
        results: list,
    ):

        selected = []

        total = 0

        for result in results:

            text = result["chunk"].text

            if (
                total + len(text)
                > self.max_characters
            ):
                break

            selected.append(result)

            total += len(text)

        return selected