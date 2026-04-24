class ScorerService:

    CATEGORY_MAX = {
        "correctness": 4000,
        "security": 2000,
        "maintainability": 2000,
        "test_coverage": 1000,
        "documentation": 1000,
    }

    SEVERITY_MULTIPLIER = {
        "critical": 1.0,
        "major": 0.4,
        "minor": 0.13,
        "info": 0.0,
    }

    # Baseline simulates vanilla Claude: no category awareness,
    # flat deductions, no severity granularity beyond critical/other
    BASELINE_SEVERITY_DEDUCTION = {
        "critical": 1500,
        "major": 500,
        "minor": 100,
        "info": 0,
    }

    @staticmethod
    def calculate_total_score(issues: list[dict]) -> int:
        """
        Category-weighted scoring. Each category has a max pool.
        Issues deduct from their category pool — a single category
        cannot tank the entire score.
        """
        # Track remaining points per category
        category_remaining = dict(ScorerService.CATEGORY_MAX)

        for issue in issues:
            severity = issue.get("severity", "info").lower()
            category = issue.get("category", "maintainability").lower()

            multiplier = ScorerService.SEVERITY_MULTIPLIER.get(severity, 0.0)
            max_points = ScorerService.CATEGORY_MAX.get(category, 0)
            deduction = max_points * multiplier

            # Deduct from category pool, floor at 0
            category_remaining[category] = max(
                0, category_remaining.get(category, 0) - deduction
            )

        return max(0, int(sum(category_remaining.values())))

    @staticmethod
    def calculate_baseline_score(issues: list[dict]) -> int:
        """
        Simulates vanilla Cursor/Claude: flat deductions with no
        category awareness. Used for benchmark comparison.
        """
        score = 10000
        for issue in issues:
            severity = issue.get("severity", "info").lower()
            score -= ScorerService.BASELINE_SEVERITY_DEDUCTION.get(severity, 0)
        return max(0, score)