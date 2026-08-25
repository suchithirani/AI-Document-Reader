import time


class PerformanceLogger:

    def __init__(self):

        self._timers = {}

    def start(
        self,
        name: str,
    ):

        self._timers[name] = {
            "start": time.perf_counter(),
        }

    def stop(
        self,
        name: str,
    ):

        if name not in self._timers:
            return

        self._timers[name]["elapsed"] = (
            time.perf_counter()
            - self._timers[name]["start"]
        ) * 1000

    def print(self):

        print("\n========== RAG Pipeline ==========")

        total = 0

        for name, value in self._timers.items():

            elapsed = value.get(
                "elapsed",
                0,
            )

            total += elapsed

            print(
                f"{name:<20}: "
                f"{elapsed:.2f} ms"
            )

        print("-" * 34)

        print(
            f"{'Total':<20}: "
            f"{total:.2f} ms"
        )

        print("=" * 34)
