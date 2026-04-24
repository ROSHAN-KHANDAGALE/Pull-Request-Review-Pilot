# BENCHMARK.md — ReviewPilot Scoring Methodology & Comparison

This document explains how ReviewPilot's scoring system works, how it was designed, why this problem was chosen, and how it compares against a vanilla Claude/Cursor baseline.

---

## Why This Problem?

Code review is one of the most universal bottlenecks in software development. Every team does it. It is slow, inconsistent, and often skipped under deadline pressure. The core problem is not that developers lack knowledge — it is that manual review is inherently variable. Two reviewers looking at the same diff will find different issues, use different language, and produce different levels of detail.

LLMs can review code, but vanilla Claude or Cursor in its default form has a critical limitation: it produces **freeform prose**. There is no structure, no severity tagging, no scoring, no repeatability. You cannot compare two reviews. You cannot track improvement over time. You cannot quantify risk.

ReviewPilot was built to solve exactly this. The agent enforces a structured output schema on every single review — same rubric, same categories, same severity scale — making reviews **comparable, trackable, and measurable**.

This was the number one priority because it sits at the intersection of:
- A problem every developer team faces daily
- A clear gap in what vanilla LLMs currently provide
- A domain where structured output provides immediate, demonstrable value

---

## Scoring System Design

### Score Range: 0 — 10,000

A score of **10,000** means the diff has zero issues across all categories. Every issue found deducts points from its category pool. The score cannot go below 0.

### Category Pools

The 10,000 points are distributed across five categories weighted by their impact on production software:

| Category | Max Points | Rationale |
|---|---|---|
| Correctness | 4,000 | Logic bugs and wrong behavior are the most expensive issues in production — they cause outages, data loss, and incorrect results |
| Security | 2,000 | Security vulnerabilities can compromise entire systems; weighted high even though they appear less frequently |
| Maintainability | 2,000 | Poor readability and high complexity create long-term technical debt that compounds over time |
| Test Coverage | 1,000 | Untested code paths are a risk multiplier — they allow other issues to go undetected |
| Documentation | 1,000 | Missing or misleading documentation slows teams down and causes misuse of APIs |

### Severity Multipliers

Each issue deducts a percentage of its category's max pool:

| Severity | Multiplier | Points Deducted (example: Correctness) |
|---|---|---|
| Critical | 100% | 4,000 pts |
| Major | 40% | 1,600 pts |
| Minor | 13% | 520 pts |
| Info | 0% | 0 pts |

### Category Capping

Each category pool floors at 0 independently. This is the most important design decision:

**Without capping:** one category with multiple critical issues could drive the total score deeply negative, making the score meaningless.

**With capping:** a catastrophically insecure diff still gets partial credit for clean, well-documented, well-tested code. The score accurately reflects the multi-dimensional quality of the diff rather than being dominated by a single axis.

### Score Calculation (Python)

```python
CATEGORY_MAX = {
    "correctness":     4000,
    "security":        2000,
    "maintainability": 2000,
    "test_coverage":   1000,
    "documentation":   1000,
}

SEVERITY_MULTIPLIER = {
    "critical": 1.0,
    "major":    0.4,
    "minor":    0.13,
    "info":     0.0,
}

def calculate_total_score(issues: list[dict]) -> int:
    category_remaining = dict(CATEGORY_MAX)

    for issue in issues:
        severity = issue.get("severity", "info").lower()
        category = issue.get("category", "maintainability").lower()
        multiplier = SEVERITY_MULTIPLIER.get(severity, 0.0)
        max_points = CATEGORY_MAX.get(category, 0)
        deduction = max_points * multiplier
        category_remaining[category] = max(0, category_remaining[category] - deduction)

    return max(0, int(sum(category_remaining.values())))
```

---

## Baseline (Vanilla Claude) Scoring

The baseline simulates how a vanilla Claude or Cursor response would score under the same rubric. It uses **flat severity deductions with no category awareness**:

| Severity | Flat Deduction |
|---|---|
| Critical | 1,500 pts |
| Major | 500 pts |
| Minor | 100 pts |
| Info | 0 pts |

```python
BASELINE_SEVERITY_DEDUCTION = {
    "critical": 1500,
    "major":    500,
    "minor":    100,
    "info":     0,
}

def calculate_baseline_score(issues: list[dict]) -> int:
    score = 10000
    for issue in issues:
        severity = issue.get("severity", "info").lower()
        score -= BASELINE_SEVERITY_DEDUCTION.get(severity, 0)
    return max(0, score)
```

The baseline has two fundamental weaknesses:
1. **No category awareness** — a critical security bug and a critical correctness bug are treated identically, even though they have very different implications
2. **No category capping** — multiple issues in one category can drive the score to 0, even if the rest of the diff is excellent

---

## Side-by-Side Comparison

### Example 1 — Security-heavy diff

A diff with one critical security issue and two minor style issues:

```
Issues found:
- [critical] [security]        SQL injection vulnerability in user query
- [minor]    [maintainability] Variable name 'x' is not descriptive
- [minor]    [documentation]   Missing docstring on public method
```

| | ReviewPilot Agent | Vanilla Baseline |
|---|---|---|
| Correctness | 4,000 / 4,000 | — |
| Security | 0 / 2,000 | — |
| Maintainability | 1,740 / 2,000 | — |
| Test Coverage | 1,000 / 1,000 | — |
| Documentation | 870 / 1,000 | — |
| **Total Score** | **7,610 / 10,000** | **8,300 / 10,000** |

**Why the baseline is misleading here:** The baseline scores this diff at 8,300 — it looks like a good diff. But the agent correctly signals that security is completely compromised (0/2,000) while everything else is healthy. The baseline flattens this signal into a single number that obscures the critical security failure.

---

### Example 2 — Correctness-heavy diff

A diff with two major correctness issues and one minor documentation issue:

```
Issues found:
- [major] [correctness]    Off-by-one error in pagination logic
- [major] [correctness]    Null pointer dereference in edge case
- [minor] [documentation]  Outdated comment references removed function
```

| | ReviewPilot Agent | Vanilla Baseline |
|---|---|---|
| Correctness | 800 / 4,000 | — |
| Security | 2,000 / 2,000 | — |
| Maintainability | 2,000 / 2,000 | — |
| Test Coverage | 1,000 / 1,000 | — |
| Documentation | 870 / 1,000 | — |
| **Total Score** | **6,670 / 10,000** | **8,900 / 10,000** |

**Why the agent wins here:** The baseline gives this diff 8,900 — nearly perfect. The agent correctly shows correctness is severely degraded (800/4,000) while security and maintainability are clean. The category breakdown makes the risk visible.

---

### Example 3 — Clean diff

A diff with only two info-level observations:

```
Issues found:
- [info] [documentation]  Could add JSDoc for better IDE support
- [info] [maintainability] Consider extracting magic number to constant
```

| | ReviewPilot Agent | Vanilla Baseline |
|---|---|---|
| **Total Score** | **10,000 / 10,000** | **10,000 / 10,000** |

Both agree on clean diffs — info-level issues carry zero deduction by design.

---

## Structural Advantages Summary

| Capability | ReviewPilot Agent | Vanilla Claude/Cursor |
|---|---|---|
| Structured JSON output | ✅ Always | ❌ Freeform prose |
| Severity classification | ✅ 4 levels | ❌ None |
| Category classification | ✅ 5 categories | ❌ None |
| Numeric score | ✅ 0–10,000 | ❌ None |
| Category-weighted scoring | ✅ Yes | ❌ No |
| Per-category breakdown | ✅ Yes | ❌ No |
| File path + line number | ✅ When available | ❌ Inconsistent |
| Fix suggestion per issue | ✅ Always | ⚠️ Sometimes |
| GitHub diff integration | ✅ Direct PR URL | ❌ Manual paste |
| Repeatable rubric | ✅ Same every run | ❌ Prompt-dependent |
| Historical storage | ✅ PostgreSQL | ❌ No persistence |
| Benchmark comparison | ✅ Built-in | ❌ No baseline |

---

## Score Interpretation Guide

| Score Range | Grade | Meaning |
|---|---|---|
| 9,000 – 10,000 | Excellent | Production-ready, only cosmetic issues |
| 7,500 – 8,999 | Good | Minor issues, safe to merge with small fixes |
| 5,000 – 7,499 | Fair | Notable issues present, review carefully before merging |
| 2,500 – 4,999 | Poor | Significant problems, requires rework |
| 0 – 2,499 | Critical | Major failures detected, do not merge |

---

## Limitations & Future Improvements

- **Baseline issue count** currently mirrors the agent's issue count. A true baseline would require a second LLM call with a vanilla prompt — planned for v2.
- **Line-level accuracy** depends on the LLM correctly identifying line numbers from the diff context. This is best-effort.
- **Large diffs** (500+ line changes) may exceed context limits — chunking strategy planned for v2.
- **Language-specific rules** (e.g. Python type hints, React hooks rules) could be added as category sub-weights in a future scoring version.