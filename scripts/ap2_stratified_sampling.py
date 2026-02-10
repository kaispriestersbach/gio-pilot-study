"""
AP2: Stratifiziertes Sampling — Hilfsskript.

Liest den bereinigten Pool (data/filtered_pool.csv) und unterstuetzt
den Hiwi beim manuellen Sampling durch:
  1. Heuristisches Pre-Tagging in Block-Kandidaten
  2. Generierung von Kandidaten-Listen pro Block
  3. Validierung der finalen Auswahl (Mode-Abdeckung, Verteilung)
  4. Export der finalen Auswahl als sampled_prompts.csv

Nutzung:
  python ap2_stratified_sampling.py tag       # Schritt 1+2: Pre-Tagging + Kandidaten
  python ap2_stratified_sampling.py validate  # Schritt 3: Finale Auswahl validieren
  python ap2_stratified_sampling.py export    # Schritt 4: CSV + Dokumentation exportieren

Input:  data/filtered_pool.csv
Output: data/sampled_prompts.csv, docs/sampling_documentation.md
"""

import re
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config


# -------------------------------------------------------------------------
# Pre-Tagging Heuristiken
# -------------------------------------------------------------------------

def has_temporal_markers(text):
    text_lower = text.lower()
    return any(m.lower() in text_lower for m in config.TEMPORAL_MARKERS)


def has_volatility_indicators(text):
    text_lower = text.lower()
    return any(v.lower() in text_lower for v in config.VOLATILITY_INDICATORS)


def has_creative_keywords(text):
    text_lower = text.lower()
    return any(k.lower() in text_lower for k in config.CREATIVE_KEYWORDS)


def has_volatile_topics(text):
    text_lower = text.lower()
    return any(t.lower() in text_lower for t in config.VOLATILE_TOPICS)


def has_implicit_demand(text):
    text_lower = text.lower()
    return any(re.search(p, text_lower) for p in config.IMPLICIT_DEMAND_PATTERNS)


def has_parametric_trap_indicators(text):
    text_lower = text.lower()
    starts_interrogative = any(
        text_lower.startswith(s) for s in
        config.INTERROGATIVE_STARTERS_EN + config.INTERROGATIVE_STARTERS_DE
    )
    has_trap_indicator = any(i.lower() in text_lower for i in config.PARAMETRIC_TRAP_INDICATORS)
    return starts_interrogative and has_trap_indicator


def is_translation_or_utility(text):
    text_lower = text.lower()
    utility_patterns = [
        r"translate", r"convert", r"format", r"rewrite",
        r"summarize this", r"fix (?:the )?grammar",
        r"uebersetze", r"konvertiere", r"formatiere",
    ]
    return any(re.search(p, text_lower) for p in utility_patterns)


def is_factual_stable(text):
    """Heuristik fuer stabile Faktenfragen (Mode 1.1 Kandidaten)."""
    text_lower = text.lower()
    stable_patterns = [
        r"what is the (?:height|weight|length|area|distance|speed|formula)",
        r"who (?:wrote|invented|discovered|founded|painted|composed)",
        r"what (?:year|century) (?:was|did|were)",
        r"what is the capital of",
        r"what is the meaning of",
        r"define ",
        r"was ist", r"wer hat .* erfunden", r"was bedeutet",
    ]
    return any(re.search(p, text_lower) for p in stable_patterns)


def is_general_explanation(text):
    """Heuristik fuer allgemeine Erklaerungen (Mode 1.1 mit mehr Tiefe)."""
    text_lower = text.lower()
    patterns = [
        r"(?:explain|describe|what is) (?:the )?(?:concept|process|difference|mechanism)",
        r"how (?:does|do) .* work",
        r"what (?:is|are) the (?:main|key|basic) (?:types|kinds|features|characteristics)",
        r"erklaere", r"beschreibe", r"wie funktioniert",
    ]
    return any(re.search(p, text_lower) for p in patterns)


def tag_prompt(text):
    """
    Ordne einem Prompt einen oder mehrere Kandidaten-Tags zu.
    Gibt eine Liste von Tags zurueck (ein Prompt kann mehrere Kandidaten sein).
    """
    tags = []

    # Edge Cases zuerst (spezifischer)
    if has_creative_keywords(text) and has_volatile_topics(text):
        tags.append("candidate_creative_volatile")

    if has_implicit_demand(text):
        tags.append("candidate_implicit_demand")

    if has_parametric_trap_indicators(text):
        tags.append("candidate_parametric_trap")

    # High GN
    if has_temporal_markers(text) or has_volatility_indicators(text):
        tags.append("candidate_high_gn")

    # Low GN
    if has_creative_keywords(text) and not has_volatile_topics(text):
        tags.append("candidate_low_gn")
    if is_translation_or_utility(text):
        tags.append("candidate_low_gn")
    if is_factual_stable(text):
        tags.append("candidate_low_gn")
    if is_general_explanation(text):
        tags.append("candidate_low_gn")

    # Fallback: untagged
    if not tags:
        tags.append("untagged")

    return tags


# -------------------------------------------------------------------------
# Kommandos
# -------------------------------------------------------------------------

def cmd_tag():
    """Schritt 1+2: Pre-Tagging und Kandidaten-Listen generieren."""
    print("=" * 60)
    print("AP2: Pre-Tagging und Kandidaten-Listen")
    print("=" * 60)

    if not config.FILTERED_POOL_PATH.exists():
        print(f"FEHLER: {config.FILTERED_POOL_PATH} nicht gefunden.")
        print("Bitte zuerst AP1 ausfuehren.")
        sys.exit(1)

    print(f"\nLade {config.FILTERED_POOL_PATH}...")
    df = pd.read_csv(config.FILTERED_POOL_PATH)
    print(f"{len(df):,} Prompts geladen.")

    # Pre-Tagging
    print("\nPre-Tagging...")
    df["tags"] = df["prompt_text"].apply(tag_prompt)
    df["primary_tag"] = df["tags"].apply(lambda t: t[0])

    # Statistik
    all_tags = []
    for tags in df["tags"]:
        all_tags.extend(tags)
    tag_counts = Counter(all_tags)

    print("\nTag-Verteilung:")
    for tag, count in sorted(tag_counts.items(), key=lambda x: -x[1]):
        print(f"  {tag:35s} {count:>8,}")

    # Kandidaten-Listen als separate CSVs speichern
    candidate_dir = config.DATA_DIR / "candidates"
    candidate_dir.mkdir(parents=True, exist_ok=True)

    blocks = [
        "candidate_low_gn",
        "candidate_high_gn",
        "candidate_parametric_trap",
        "candidate_implicit_demand",
        "candidate_creative_volatile",
    ]

    for block in blocks:
        mask = df["tags"].apply(lambda t: block in t)
        candidates = df[mask].copy()
        # Zufaellige Stichprobe (max 100 Kandidaten pro Block)
        n = min(100, len(candidates))
        if n > 0:
            sample = candidates.sample(n, random_state=config.RANDOM_SEED)
            out_path = candidate_dir / f"{block}.csv"
            sample[["conversation_id", "prompt_text", "language", "word_count"]].to_csv(
                out_path, index=False
            )
            print(f"\n  {block}: {len(candidates):,} gesamt, {n} Kandidaten -> {out_path}")
        else:
            print(f"\n  {block}: KEINE Kandidaten gefunden!")

    # Hinweis zu Mode 3.1
    print("\n" + "-" * 60)
    print("HINWEIS zu Mode 3.1 (Transactional):")
    print("  WildChat enthaelt wenige transaktionale Prompts.")
    print("  Bitte manuell im E-GEO-Paper (arXiv:2511.20867)")
    print("  nach passenden Prompts suchen, falls <3 im Pool.")
    print("-" * 60)

    print(f"\nKandidaten-Listen gespeichert in: {candidate_dir}/")
    print("Naechster Schritt: Manuell Prompts auswaehlen und in")
    print(f"  {config.SAMPLED_PROMPTS_PATH} eintragen.")
    print(f"  Dann: python ap2_stratified_sampling.py validate")


def cmd_validate():
    """Schritt 3: Finale Auswahl validieren."""
    print("=" * 60)
    print("AP2: Validierung der Prompt-Auswahl")
    print("=" * 60)

    if not config.SAMPLED_PROMPTS_PATH.exists():
        print(f"FEHLER: {config.SAMPLED_PROMPTS_PATH} nicht gefunden.")
        print("Bitte zuerst die manuelle Auswahl in diese Datei eintragen.")
        print("\nErwartete Spalten:")
        print("  prompt_id, conversation_id, prompt_text, block, subtype,")
        print("  gio_mode_estimate, justification, source, language")
        sys.exit(1)

    df = pd.read_csv(config.SAMPLED_PROMPTS_PATH)
    # gio_mode_estimate als String sicherstellen (pandas liest "1.1" als Float)
    df["gio_mode_estimate"] = df["gio_mode_estimate"].astype(str)
    print(f"\n{len(df)} Prompts geladen.")

    errors = []
    warnings = []

    # Check 1: Gesamtanzahl
    study = df[df["block"] != "calibration"]
    calib = df[df["block"] == "calibration"]
    if len(study) != 50:
        errors.append(f"Erwartet 50 Studien-Prompts, gefunden: {len(study)}")
    if len(calib) != 5:
        errors.append(f"Erwartet 5 Kalibrierungs-Prompts, gefunden: {len(calib)}")

    # Check 2: Block-Verteilung
    block_counts = study["block"].value_counts().to_dict()
    expected = {"low_gn": 18, "high_gn": 18}
    for block, expected_n in expected.items():
        actual_n = block_counts.get(block, 0)
        if actual_n != expected_n:
            errors.append(f"Block '{block}': erwartet {expected_n}, gefunden {actual_n}")

    # Edge Cases
    edge = study[study["block"] == "edge"]
    if len(edge) != 14:
        errors.append(f"Edge Cases: erwartet 14, gefunden {len(edge)}")
    else:
        subtype_counts = edge["subtype"].value_counts().to_dict()
        expected_subtypes = {
            "parametric_trap": 5,
            "implicit_demand": 5,
            "creative_volatile": 4,
        }
        for st, n in expected_subtypes.items():
            actual = subtype_counts.get(st, 0)
            if actual != n:
                errors.append(f"Edge-Subtyp '{st}': erwartet {n}, gefunden {actual}")

    # Check 3: GIO-Mode-Abdeckung (mindestens 3x pro Mode, ausser 3.1)
    mode_counts = study["gio_mode_estimate"].value_counts().to_dict()
    required_modes = ["1.1", "1.2", "1.3", "2.1", "2.2", "2.3", "3.2"]
    for mode in required_modes:
        count = mode_counts.get(mode, 0)
        if count < 3:
            errors.append(f"GIO-Mode {mode}: nur {count}x vertreten (min. 3 erforderlich)")

    # Mode 3.1 separat (darf <3 sein, aber Warnung)
    mode_31 = mode_counts.get("3.1", 0)
    if mode_31 < 3:
        warnings.append(
            f"GIO-Mode 3.1 (Transactional): nur {mode_31}x vertreten. "
            f"Bitte aus E-GEO ergaenzen falls moeglich."
        )

    # Check 4: Pflichtfelder
    required_cols = ["prompt_id", "prompt_text", "block", "gio_mode_estimate",
                     "justification", "source"]
    for col in required_cols:
        if col not in df.columns:
            errors.append(f"Spalte '{col}' fehlt.")
        elif df[col].isna().any():
            n_missing = df[col].isna().sum()
            warnings.append(f"Spalte '{col}': {n_missing} fehlende Werte.")

    # Check 5: Prompt-IDs eindeutig
    if df["prompt_id"].duplicated().any():
        dupes = df[df["prompt_id"].duplicated()]["prompt_id"].tolist()
        errors.append(f"Doppelte Prompt-IDs: {dupes}")

    # Ergebnisse
    print("\n" + "=" * 60)
    if errors:
        print(f"FEHLER ({len(errors)}):")
        for e in errors:
            print(f"  [X] {e}")
    if warnings:
        print(f"\nWARNUNGEN ({len(warnings)}):")
        for w in warnings:
            print(f"  [!] {w}")
    if not errors and not warnings:
        print("VALIDIERUNG BESTANDEN — Alle Checks OK.")

    # Mode-Verteilung anzeigen
    print("\nGIO-Mode-Verteilung (Studien-Prompts):")
    for mode in sorted(config.DROPDOWN_GIO_MODES):
        n = mode_counts.get(mode, 0)
        name = config.GIO_MODES.get(mode, {}).get("name", "?")
        marker = " <-- FEHLT" if n < 3 and mode != "3.1" else ""
        print(f"  Mode {mode} ({name:25s}): {n:2d}x{marker}")

    print("\nBlock-Verteilung:")
    for block, n in sorted(df["block"].value_counts().items()):
        print(f"  {block:25s}: {n:2d}")

    if errors:
        print(f"\n{len(errors)} Fehler gefunden. Bitte korrigieren.")
        sys.exit(1)
    else:
        print("\nValidierung abgeschlossen. Weiter mit:")
        print(f"  python ap2_stratified_sampling.py export")


def cmd_export():
    """Schritt 4: CSV und Dokumentation exportieren."""
    print("=" * 60)
    print("AP2: Export")
    print("=" * 60)

    if not config.SAMPLED_PROMPTS_PATH.exists():
        print(f"FEHLER: {config.SAMPLED_PROMPTS_PATH} nicht gefunden.")
        sys.exit(1)

    df = pd.read_csv(config.SAMPLED_PROMPTS_PATH)
    df["gio_mode_estimate"] = df["gio_mode_estimate"].astype(str)

    # Sampling-Dokumentation generieren
    study = df[df["block"] != "calibration"]
    calib = df[df["block"] == "calibration"]

    doc_lines = [
        "# Sampling-Dokumentation — GIO Pilot Study",
        "",
        "## Filterkriterien (AP1)",
        "",
        f"- Datensatz: {config.WILDCHAT_DATASET}",
        f"- Nur erster User-Turn pro Konversation",
        f"- Wortlaenge: {config.MIN_WORDS}–{config.MAX_WORDS} Woerter",
        f"- Sprachen: {', '.join(sorted(config.ALLOWED_LANGUAGES))}",
        f"- Code-Debugging-Prompts entfernt",
        f"- Exakte Duplikate entfernt",
        "",
        "## Sampling-Entscheidungen (AP2)",
        "",
        f"- Studien-Prompts: {len(study)}",
        f"- Kalibrierungs-Prompts: {len(calib)}",
        "",
        "### Block-Verteilung",
        "",
    ]

    for block, n in sorted(study["block"].value_counts().items()):
        doc_lines.append(f"- {block}: {n}")

    doc_lines.extend([
        "",
        "### GIO-Mode-Verteilung",
        "",
    ])

    for mode in sorted(config.DROPDOWN_GIO_MODES):
        n = study[study["gio_mode_estimate"] == mode].shape[0]
        name = config.GIO_MODES.get(mode, {}).get("name", "?")
        doc_lines.append(f"- Mode {mode} ({name}): {n}")

    doc_lines.extend([
        "",
        "### Quellen",
        "",
    ])
    source_counts = df["source"].value_counts()
    for source, n in source_counts.items():
        doc_lines.append(f"- {source}: {n}")

    doc_lines.extend([
        "",
        "## Bekannte Luecken",
        "",
        "- Mode 3.1 (Transactional) ist in WildChat unterrepraesentiert.",
        "- Der Code-Filter ist heuristisch und koennte einige Prompts mit Code-Referenzen faelschlicherweise entfernen.",
        "- Die Spracherkennung (fasttext) hat bei sehr kurzen Prompts niedrigere Genauigkeit.",
        "",
        "## Prompt-Details",
        "",
        "| ID | Block | Subtyp | Mode | Quelle | Begruendung |",
        "|---|---|---|---|---|---|",
    ])

    for _, row in df.iterrows():
        doc_lines.append(
            f"| {row.get('prompt_id', '')} "
            f"| {row.get('block', '')} "
            f"| {row.get('subtype', '')} "
            f"| {row.get('gio_mode_estimate', '')} "
            f"| {row.get('source', '')} "
            f"| {row.get('justification', '')} |"
        )

    config.DOCS_DIR.mkdir(parents=True, exist_ok=True)
    doc_path = config.SAMPLING_DOC_PATH
    doc_path.write_text("\n".join(doc_lines), encoding="utf-8")
    print(f"\nDokumentation gespeichert: {doc_path}")

    print("\nExport abgeschlossen.")
    print("Naechste Schritte:")
    print("  1. python scripts/ap3_keyword_baseline.py")
    print("  2. python scripts/ap4_create_annotation.py")


# -------------------------------------------------------------------------
# CSV-Template generieren (Hilfsfunktion)
# -------------------------------------------------------------------------

def cmd_template():
    """Generiere ein leeres CSV-Template fuer die manuelle Auswahl."""
    print("Generiere leeres Template...")

    columns = [
        "prompt_id", "conversation_id", "prompt_text", "block", "subtype",
        "gio_mode_estimate", "justification", "source", "language",
    ]
    df = pd.DataFrame(columns=columns)

    # Beispielzeile
    example = {
        "prompt_id": "P01",
        "conversation_id": "abc123",
        "prompt_text": "What is the height of the Eiffel Tower?",
        "block": "low_gn",
        "subtype": "",
        "gio_mode_estimate": "1.1",
        "justification": "Static fact about well-known landmark, answerable from parametric memory.",
        "source": "WildChat",
        "language": "en",
    }
    df = pd.concat([df, pd.DataFrame([example])], ignore_index=True)

    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    template_path = config.DATA_DIR / "sampled_prompts_template.csv"
    df.to_csv(template_path, index=False)
    print(f"Template gespeichert: {template_path}")
    print("Bitte dieses Template ausfuellen und als sampled_prompts.csv speichern.")


def main():
    if len(sys.argv) < 2:
        print("Nutzung:")
        print("  python ap2_stratified_sampling.py tag       # Pre-Tagging + Kandidaten")
        print("  python ap2_stratified_sampling.py template  # Leeres CSV-Template")
        print("  python ap2_stratified_sampling.py validate  # Auswahl validieren")
        print("  python ap2_stratified_sampling.py export    # CSV + Doku exportieren")
        sys.exit(1)

    cmd = sys.argv[1].lower()
    if cmd == "tag":
        cmd_tag()
    elif cmd == "template":
        cmd_template()
    elif cmd == "validate":
        cmd_validate()
    elif cmd == "export":
        cmd_export()
    else:
        print(f"Unbekannter Befehl: {cmd}")
        sys.exit(1)


if __name__ == "__main__":
    main()
