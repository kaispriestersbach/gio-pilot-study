# Candidate Review Summary (v2)

## Overview

All 600 candidate prompts across 6 lists were reviewed against four criteria:
- **(a) Standalone**: Self-contained, no external references
- **(b) Mode assignability**: Clearly assignable to one GIO mode
- **(c) Stratum fit**: Actually belongs in its assigned block
- **(d) Linguistic clarity**: Clear EN or DE

This is the second review round (v2), following the AP2 heuristic overhaul that:
- Added standalone pre-filter (`has_external_reference()`)
- Strengthened high_gn (requires semantic patterns, not just keywords)
- Added negative checks for parametric_trap
- Required creative verbs for creative_volatile
- Added new grounded_gen block (Mode 2.3)

## Verdict Distribution

| Block | Total | ACCEPT | REJECT | EDGE_CASE | Accept Rate | v1 Rate | Delta |
|-------|-------|--------|--------|-----------|-------------|---------|-------|
| low_gn | 100 | 83 | 15 | 2 | **83%** | 72% | +11pp |
| high_gn | 100 | 48 | 50 | 2 | **48%** | 5% | +43pp |
| parametric_trap | 100 | 14 | 82 | 4 | **14%** | 12% | +2pp |
| implicit_demand | 100 | 63 | 27 | 10 | **63%** | 76% | -13pp |
| creative_volatile | 100 | 3 | 93 | 4 | **3%** | 9% | -6pp |
| grounded_gen | 100 | 69 | 28 | 3 | **69%** | -- | NEW |
| **TOTAL** | **600** | **280** | **295** | **25** | **46.7%** | 35% | +12pp |

## Comparison with v1

### Improvements
- **high_gn**: Massive improvement from 5% to 48%. Semantic patterns (advisory,
  investigation, temporal+volatility) are far more precise than keyword-only matching.
- **low_gn**: Improved from 72% to 83%. Standalone pre-filter removes bad candidates early.
- **grounded_gen**: New block with 69% accept rate. Successfully captures Mode 2.3 prompts
  with embedded source text.
- **Overall**: Accept rate improved from 35% (174/500) to 47% (280/600).

### Unchanged or Declined
- **parametric_trap**: Marginal improvement (12% to 14%). The 1.1/1.2 boundary remains
  inherently difficult to capture with keyword heuristics.
- **creative_volatile**: Declined from 9% to 3%. The stricter creative verb requirement
  correctly filters more false positives but the true intersection remains very rare.
- **implicit_demand**: Declined from 76% to 63%. Stricter mode assignability may explain
  this; the heuristic is unchanged but review standards may be slightly different.

## Criteria Failure Distribution (REJECT only)

| Block | (a) Standalone | (b) Mode | (c) Stratum | (d) Language |
|-------|---------------|----------|-------------|-------------|
| low_gn | 3 | 1 | 10 | 2 |
| high_gn | 7 | 1 | 45 | 3 |
| parametric_trap | 7 | 51 | 75 | 0 |
| implicit_demand | 3 | 18 | 24 | 0 |
| creative_volatile | 11 | 37 | 89 | 3 |
| grounded_gen | 4 | 0 | 27 | 1 |
| **TOTAL** | **35** | **108** | **270** | **9** |

Note: A single prompt can fail multiple criteria, so column totals exceed reject counts.

**Key Finding:** Stratum mismatch (c) remains the dominant rejection reason (270 of 295
rejects, 92%), consistent with v1. However, mode assignability (b) failures increased
significantly in parametric_trap and creative_volatile, reflecting the stricter v2 review.

## GIO Mode Distribution (ACCEPT only)

| Mode | Name | Count | Source Blocks |
|------|------|-------|--------------|
| 1.1 | Fact Retrieval | 3 | low_gn (3) |
| 1.2 | Real-Time Synthesis | 9 | high_gn (9) |
| 1.3 | Advisory | 82 | implicit_demand (63), high_gn (19) |
| 2.1 | Utility | 31 | low_gn (27), high_gn (4) |
| 2.2 | Ungrounded Generation | 57 | low_gn (53), creative_volatile (3), high_gn (1*) |
| 2.3 | Grounded Generation | 75 | grounded_gen (69), high_gn (6) |
| 3.1 | Transactional | 1 | high_gn (1) |
| 3.2 | Open-Ended Investigation | 9 | high_gn (9) |
| 1.1/1.2 | Parametric Trap | 14 | parametric_trap (14) |
| **TOTAL** | | **280+1*** | |

*Note: Some high_gn accepts were classified into unexpected modes (2.1, 2.3) by the
reviewer, reflecting the broad nature of the high_gn advisory/investigation patterns.

### Mode Coverage vs v1

| Mode | v1 Count | v2 Count | Status |
|------|----------|----------|--------|
| 1.1 | 13 | 3 | Sufficient (low_gn) |
| 1.2 | 12 | 9 | Sufficient |
| 1.3 | 80 | 82 | Abundant |
| 2.1 | 4 | 31 | Greatly improved |
| 2.2 | 64 | 57 | Abundant |
| 2.3 | 0 | 75 | **RESOLVED** (was critical gap) |
| 3.1 | 0 | 1 | Marginal (still rare in WildChat) |
| 3.2 | 1 | 9 | **RESOLVED** (was critical gap) |

## Block-Level Analysis

### low_gn (83% accept rate) -- EXCELLENT
Strongest block. Dominated by creative writing (2.2: 53) and utility tasks (2.1: 27).
Few factual questions (1.1: 3) — stable facts may be under-represented. Main rejects:
stratum mismatch (prompts needing dynamic data) and minor standalone issues.

### high_gn (48% accept rate) -- GOOD (was CRITICAL)
Massive improvement from 5% to 48%. Semantic advisory patterns capture Mode 1.3 well (19),
investigation patterns capture 3.2 (9), and temporal+volatility captures 1.2 (9).
Remaining rejects are mostly stratum mismatches (stable facts or pure creative tasks).

### parametric_trap (14% accept rate, 4% edge) -- MODERATE
Slight improvement (12% to 14%). The 1.1/1.2 boundary is inherently hard to capture
heuristically. 14 accepted + 4 edge cases = 18 usable prompts, sufficient for 5 slots.
High mode-assignability failure rate (51) reflects many prompts that are clearly one side.

### implicit_demand (63% accept rate) -- GOOD
Accept rate declined from 76% to 63%, possibly due to stricter review standards.
All 63 accepts are Mode 1.3 (advisory). 10 edge cases provide additional candidates.
73 usable prompts — more than sufficient for 5 slots.

### creative_volatile (3% accept rate) -- CRITICAL (unchanged)
Despite the v2 heuristic requiring creative verbs, the intersection of creative generation
+ volatile topic remains extremely rare. 3 accepts + 4 edge cases = 7 usable prompts.
Sufficient for 4 slots but with minimal margin.

### grounded_gen (69% accept rate) -- GOOD (NEW)
New block successfully captures Mode 2.3. All 69 accepts and 3 edge cases contain
embedded source text with creative/rewriting tasks. Main rejects: stratum mismatch
(utility-only tasks or prompts without substantial embedded text).

## Sample Feasibility Assessment

| Block | Target Slots | Accepted | Edge Cases | Total Usable | Feasible? |
|-------|-------------|----------|------------|-------------|-----------|
| low_gn | 18 | 83 | 2 | 85 | YES |
| high_gn | 18 | 48 | 2 | 50 | YES |
| parametric_trap | 5 | 14 | 4 | 18 | YES |
| implicit_demand | 5 | 63 | 10 | 73 | YES |
| creative_volatile | 4 | 3 | 4 | 7 | MARGINAL |
| grounded_gen | -- | 69 | 3 | 72 | YES |
| calibration | 5 | -- | -- | -- | Manual |

All blocks except creative_volatile have sufficient candidates for the target sample.
The creative_volatile block is marginal with only 7 usable prompts for 4 slots.

## Dedicated Transactional Search (Mode 3.1)

The standard candidate blocks yielded only 1 Mode 3.1 prompt (in high_gn).
To address this gap, a dedicated exhaustive search was conducted across the
entire filtered pool.

### Search Methodology

1. **Pattern-based keyword search** across 230,289 filtered prompts using
   transactional verbs and noun patterns (book, reserve, purchase, order,
   schedule, subscribe, sign up, register, cancel, checkout, etc.)
2. **Multi-pattern scoring**: Each prompt scored by number of distinct
   transactional keyword matches + presence of action-intent markers
   ("I want to", "I need to", "help me", "can you")
3. **Top 100 candidates** selected by score, saved as
   `candidate_transactional.csv`
4. **Expert review** against the standard 4 criteria

### Results

| Stage | Count |
|-------|-------|
| Filtered pool | 230,289 |
| Keyword matches (broad) | ~7,400 |
| Scored & ranked candidates | 100 |
| ACCEPT | **1** (1%) |
| REJECT | 99 |

### Rejection Analysis

The 99 rejected prompts were reclassified by actual GIO mode:

| Actual Mode | Count | Typical Pattern |
|-------------|-------|-----------------|
| 2.1 Utility | 38 | "Draft/write an email to book..." |
| 1.3 Advisory | 32 | "Should I book...", "Is it worth..." |
| 1.1/1.2 Factual | 20 | "What is the booking policy...", "How much does..." |
| 2.2/3.2 Other | 10 | Creative scenarios, research tasks |

### Interpretation

The near-absence of Mode 3.1 in WildChat reflects a fundamental
**affordance mismatch**: users understand that current (non-agentic) LLMs
cannot execute real-world transactions. Prompts containing transactional
vocabulary overwhelmingly use it in a non-transactional context (drafting
communication about transactions, seeking advice about transactions, or
asking factual questions about transactional processes).

This finding is itself a methodological contribution: Mode 3.1 represents
a theoretical category in the GIO framework that is not yet empirically
observable in standard chatbot corpora, but will likely emerge with the
adoption of agentic LLM systems (tool use, function calling, browser
automation).

### Integration into Sample

The single accepted transactional prompt was integrated into the high_gn
block by replacing one overrepresented Mode 1.3 prompt, bringing the
Mode 3.1 count from 1 to 2 in the final sample. This remains below the
minimum threshold of 3 per mode.

## Recommendations

1. **Proceed to AP2 final sampling** for low_gn, high_gn, parametric_trap,
   implicit_demand, and grounded_gen. All have sufficient candidate pools.

2. **creative_volatile**: Consider relaxing criteria slightly (e.g., accept prompts
   where the volatile topic is the primary subject even if the creative aspect is
   implicit), or manually source additional candidates from the untagged pool.

3. **Mode 3.1 (Transactional)**: Exhaustive search of 230k prompts confirms
   systematic absence. Only 2 prompts in final sample (below min. 3 threshold).
   Recommend documenting as methodological finding in the paper. Future studies
   should target agentic LLM corpora for this mode.

4. **Mode 1.1 balance**: Only 3 Fact Retrieval accepts in low_gn (v1 had 13).
   Review whether the v2 heuristic over-filters simple factual questions. Consider
   checking the low_gn reject list for borderline 1.1 prompts.

5. **grounded_gen integration**: Decide how grounded_gen fits into the 55-prompt
   sample. Currently not in SAMPLING_TARGETS — may need a dedicated slot allocation.
