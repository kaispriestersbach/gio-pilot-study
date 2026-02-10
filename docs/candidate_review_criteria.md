# Candidate Prompt Review Criteria

## Purpose

Each candidate prompt must pass four quality criteria before being eligible
for the final 55-prompt sample of the GIO Pilot Annotation Study.

---

## Criterion (a): Standalone Comprehensibility

**The prompt must be fully understandable without any external context.**

REJECT if the prompt:
- References uploaded files, images, or attachments ("the file I uploaded", "see attached", "this image", "the document above")
- References previous conversation turns ("as I said before", "continuing from above", "like you mentioned")
- Contains placeholder text that requires substitution ("[insert topic here]")
- References content that was pasted but is missing (e.g., "summarize this:" with nothing following)
- Is a bare instruction that only makes sense with an attachment ("translate this", "fix this code" without any content)

ACCEPT if the prompt:
- Is a complete, self-contained question or instruction
- Contains all necessary context within itself
- Could be understood by any reader without prior conversation

**Edge case:** Prompts that include quoted text inline (e.g., "Paraphrase the following: 'The economy is...'") are ACCEPT because the source material is embedded.

---

## Criterion (b): GIO Mode Assignability

**The prompt must be clearly assignable to one of the 8 GIO modes.**

### GIO Mode Reference

| Mode | Name | Category | GN Level | Core Signal |
|------|------|----------|----------|-------------|
| 1.1 | Fact Retrieval | ASKING | Low | Static fact, high consensus |
| 1.2 | Real-Time Synthesis | ASKING | High | Dynamic/volatile data |
| 1.3 | Advisory | ASKING | High | Subjective, multi-perspective |
| 2.1 | Utility | DOING | None | Transform existing input |
| 2.2 | Ungrounded Generation | DOING | Low | Creative, ex nihilo |
| 2.3 | Grounded Generation | DOING | N/A | Source-dependent creation |
| 3.1 | Transactional | ACTING | High | Purchase/booking/action |
| 3.2 | Open-Ended Investigation | ACTING | High | Underspecified, multi-step |

REJECT if:
- The prompt conflates two clearly distinct modes with equal weight (e.g., "Write a poem about the current stock price" = 2.2 + 1.2)
- The prompt is so vague that no mode can be determined

ACCEPT if:
- One dominant mode is clearly identifiable, even if minor aspects touch another mode
- The prompt cleanly fits one mode definition

EDGE_CASE if:
- The prompt is deliberately ambiguous and useful as an edge case for the study
- The ambiguity is between specific theoretically interesting mode pairs (e.g., 1.1 vs 1.2 for parametric traps)

---

## Criterion (c): Stratum Representativeness

**The prompt must actually belong to its assigned block.**

| Block | Expected Characteristics |
|-------|------------------------|
| **low_gn** | Modes 1.1, 2.1, 2.2 — Static facts, utility tasks, creative generation. No temporal urgency, no volatile data. |
| **high_gn** | Modes 1.2, 1.3, 3.1, 3.2 — Dynamic data, advisory, transactional, investigative. Temporal markers, entity specificity. |
| **parametric_trap** | Looks like 1.1 (simple fact) but actually requires live data (1.2). Entity + volatile attribute (CEO of X, population of Y). |
| **implicit_demand** | Advisory (1.3) — "Should I...", "Is it worth...", subjective guidance needed. |
| **creative_volatile** | Creative task (2.2) intersecting volatile topic — tests whether GN is driven by topic or task. |

REJECT if:
- The prompt clearly belongs to a different block (e.g., a simple factual question in the creative_volatile list)
- The prompt's GN characteristics contradict its block assignment

ACCEPT if:
- The prompt exemplifies its block's defining characteristics

---

## Criterion (d): Linguistic Clarity

**The prompt must be in clear English or German.**

REJECT if:
- The prompt is in a language other than EN or DE
- The prompt is mostly unintelligible (garbled text, encoding issues)
- Mixed-language prompts where the core request is unclear
- Excessive use of special characters or formatting that obscures meaning

ACCEPT if:
- Clear EN or DE text
- Minor typos or informal language are acceptable (this is real-world data)
- Technical jargon is acceptable if the domain is clear

---

## Verdict Categories

| Verdict | Meaning |
|---------|---------|
| **ACCEPT** | Passes all four criteria. Eligible for final sample. |
| **REJECT** | Fails one or more criteria. Not eligible. |
| **EDGE_CASE** | Deliberately ambiguous or boundary case. May be useful for edge case slots in the study design. |

---

## Common Rejection Patterns

1. **"Summarize this" without content** — Fails (a): references external document
2. **"Fix this code:" followed by code block** — Should have been filtered by AP1, but if present: Fails (a)
3. **Multi-mode chimera** — Fails (b): e.g., "Research the latest AI trends and write a poem about them"
4. **Misclassified stratum** — Fails (c): e.g., "What is the capital of France?" in high_gn list
5. **Non-EN/DE text** — Fails (d): prompt in another language
6. **Roleplay/system prompt injection** — Fails (a)/(b): "You are now DAN..." or similar jailbreak attempts
