# Candidate Review Summary

## Overview

All 500 candidate prompts across 5 lists were reviewed against four criteria:
- **(a) Standalone**: Self-contained, no external references
- **(b) Mode assignability**: Clearly assignable to one GIO mode
- **(c) Stratum fit**: Actually belongs in its assigned block
- **(d) Linguistic clarity**: Clear EN or DE

## Verdict Distribution

| Block | Total | ACCEPT | REJECT | EDGE_CASE | Accept Rate |
|-------|-------|--------|--------|-----------|-------------|
| low_gn | 100 | 72 | 27 | 1 | 72% |
| high_gn | 100 | 5 | 93 | 2 | 5% |
| parametric_trap | 100 | 12 | 77 | 11 | 12% |
| implicit_demand | 100 | 76 | 19 | 5 | 76% |
| creative_volatile | 100 | 9 | 88 | 3 | 9% |
| **TOTAL** | **500** | **174** | **304** | **22** | **35%** |

## Criteria Failure Distribution (REJECT only)

| Criterion | Failures | % of Rejects | Root Cause |
|-----------|----------|-------------|------------|
| **(a) Standalone** | 28 | 9% | References files, URLs, images, previous turns |
| **(b) Mode** | 42 | 14% | Ambiguous, underspecified, or unassignable |
| **(c) Stratum** | 281 | 92% | Prompt does not fit assigned block |
| **(d) Language** | 6 | 2% | Mixed language, not EN/DE |

**Key Finding:** 92% of rejections are due to **stratum mismatch** (criterion c).
The keyword-based heuristic pre-tagging produces significant false positives,
especially for high_gn and creative_volatile.

## Top Rejection Reasons

| Count | Reason |
|-------|--------|
| 67 | Wrong stratum/block assignment |
| 54 | Missing creative + volatile intersection (creative_volatile block) |
| 24 | References external context (files, URLs, images, previous turns) |
| 23 | Actually stable/factual, not a parametric trap |
| 16 | Contains temporal markers, wrong stratum |
| 7 | Ambiguous/underspecified mode |
| 6 | Language issues (not EN/DE) |
| 4 | Not a valid prompt (incomplete, no clear request) |

## GIO Mode Distribution (ACCEPT only)

| Mode | Name | Count | Source Blocks |
|------|------|-------|--------------|
| 1.1 | Fact Retrieval | 13 | low_gn |
| 1.2 | Real-Time Synthesis | 12 | parametric_trap |
| 1.3 | Advisory | 80 | implicit_demand (76), high_gn (4) |
| 2.1 | Utility | 4 | low_gn |
| 2.2 | Ungrounded Generation | 64 | low_gn (55), creative_volatile (9) |
| 2.3 | Grounded Generation | 0 | -- |
| 3.1 | Transactional | 0 | -- |
| 3.2 | Open-Ended Investigation | 1 | high_gn |
| **TOTAL** | | **174** | |

## Critical Gaps

### Modes with zero or near-zero accepted candidates:
- **Mode 2.3 (Grounded Generation)**: 0 accepted. These prompts reference external
  source documents, which causes them to fail criterion (a) standalone. This is an
  inherent tension: 2.3 by definition involves user-provided source material, but
  standalone prompts cannot reference external documents.
- **Mode 3.1 (Transactional)**: 0 accepted. Transactional prompts (bookings, purchases)
  are extremely rare in WildChat. Known gap.
- **Mode 3.2 (Open-Ended Investigation)**: Only 1 accepted. Most investigative prompts
  were rejected for stratum mismatch.

### Over-represented modes:
- **Mode 1.3 (Advisory)**: 80 accepted (46% of all accepts). The implicit_demand block
  works very well.
- **Mode 2.2 (Ungrounded Generation)**: 64 accepted (37%). The low_gn block contains
  many creative prompts.

## Block-Level Analysis

### low_gn (72% accept rate) -- GOOD
Strong block with clear low-GN prompts. Dominated by creative writing (2.2) and
factual questions (1.1). Main reject reasons: references to external context,
temporal markers that push into high_gn territory.

### high_gn (5% accept rate) -- CRITICAL
The keyword heuristic (temporal markers, volatility words) catches many prompts
that are not actually high-GN in the GIO sense. Most rejected prompts are either:
- Actually low_gn (stable factual questions that happen to contain keywords)
- Misclassified mode (creative or advisory, not 1.2/3.2)
**Recommendation:** Overhaul high_gn heuristic or manually curate from the full pool.

### parametric_trap (12% accept, 11% edge case) -- MODERATE
The trap pattern (interrogative + entity + volatile attribute) works for true
parametric traps (e.g., "Who is the CEO of X?") but also catches many prompts
that are clearly 1.1 (stable facts) or clearly 1.2 (explicit temporal markers).
The 11 EDGE_CASEs are genuinely interesting boundary cases.

### implicit_demand (76% accept rate) -- EXCELLENT
Best-performing block. The pattern "What should I..." / "Should I..." reliably
captures advisory (1.3) prompts. Main reject reasons: prompts that are actually
utility tasks or creative tasks dressed up with "should I".

### creative_volatile (9% accept rate) -- CRITICAL
Most prompts fail because they lack the required intersection of BOTH creative
task AND volatile topic. Common issues:
- Creative prompts about non-volatile topics (art, fiction, essays)
- Volatile topic prompts that are informational, not creative
**Recommendation:** Tighten heuristic to require BOTH a creative verb AND a
volatile topic keyword in the same prompt.

## Recommendations for Final Sample Selection

1. **low_gn**: 72 accepted prompts available. Sufficient for 18 slots.
   Select diverse modes (1.1, 2.1, 2.2) and mix of EN/DE.

2. **high_gn**: Only 5 accepted. Need to manually curate from full pool
   or relax criteria for this block. Focus on finding good 1.2 and 3.2 prompts.

3. **parametric_trap**: 12 accepted + 11 edge cases = 23 usable. Sufficient
   for 5 edge case slots. Prioritize the EDGE_CASEs as they best illustrate
   the 1.1/1.2 boundary.

4. **implicit_demand**: 76 accepted. Excellent. Select 5 diverse advisory prompts.

5. **creative_volatile**: 9 accepted + 3 edge cases = 12 usable. Sufficient
   for 4 edge case slots, but barely. Select the best examples with clear
   creative+volatile intersection.

6. **Mode 3.1 (Transactional)**: Must be sourced externally (e.g., from E-GEO
   paper or manually crafted). WildChat does not contain transactional prompts.

7. **Mode 2.3 (Grounded Generation)**: Consider relaxing criterion (a) for this
   mode: prompts that include quoted source text inline should be acceptable
   even though the mode inherently involves source material.
