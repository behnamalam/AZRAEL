from datetime import datetime


class FateEngine:

    PRIORITY_SCORE = {
        "LOW": 15,
        "NORMAL": 35,
        "HIGH": 70,
        "CRITICAL": 95
    }

    STATUS_SCORE = {
        "PENDING": 50,
        "COMPLETED": 0
    }

    @classmethod
    def calculate(
        cls,
        priority,
        risk,
        deadline,
        status
    ):
        if status == "COMPLETED":
            return 0

        priority_score = cls.PRIORITY_SCORE.get(
            priority,
            35
        )

        risk_score = max(
            0,
            min(100, int(risk))
        )

        deadline_score = cls._deadline_score(
            deadline
        )

        status_score = cls.STATUS_SCORE.get(
            status,
            50
        )

        score = (
            priority_score * 0.30
            + risk_score * 0.25
            + deadline_score * 0.30
            + status_score * 0.15
        )

        return round(score, 1)

    @staticmethod
    def _deadline_score(deadline):

        if not deadline:
            return 30

        try:
            deadline_dt = datetime.strptime(
                deadline,
                "%Y-%m-%d %H:%M:%S"
            )

            now = datetime.now()

            seconds = (
                deadline_dt - now
            ).total_seconds()

            hours = seconds / 3600

            if hours <= 0:
                return 100

            if hours <= 6:
                return 95

            if hours <= 24:
                return 85

            if hours <= 72:
                return 70

            if hours <= 168:
                return 50

            return 20

        except (ValueError, TypeError):
            return 30

    @staticmethod
    def classification(score):

        if score >= 85:
            return "TERMINAL"

        if score >= 70:
            return "CRITICAL"

        if score >= 50:
            return "WARNING"

        if score >= 30:
            return "WATCH"

        return "SAFE"

if __name__ == "__main__":

    score = FateEngine.calculate(
        priority="CRITICAL",
        risk=90,
        deadline=None,
        status="PENDING"
    )

    print("FATE SCORE:", score)
    print("FATE:", FateEngine.classification(score))