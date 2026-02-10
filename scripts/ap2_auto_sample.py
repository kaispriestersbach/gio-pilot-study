"""
AP2 Hilfsskript: Automatisches Sampling fuer Pipeline-Test.

Waehlt automatisch 50 Studien-Prompts + 5 Kalibrierungs-Prompts
aus den Kandidaten-Listen (data/candidates/) und erstellt eine
gueltige sampled_prompts.csv.

Die Zuordnung zu GIO-Modes ist eine Schaetzung — die eigentliche
Annotation passiert durch die Experten-Rater.

Output: data/sampled_prompts.csv
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config


def estimate_gio_mode(text, block, subtype=""):
    """Grobe GIO-Mode-Schaetzung basierend auf Block und Text."""
    text_lower = text.lower()

    # Edge Cases
    if subtype == "parametric_trap":
        return "1.2"  # High E_spec, sieht wie 1.1 aus, ist aber 1.2
    if subtype == "implicit_demand":
        return "1.3"  # Advisory
    if subtype == "creative_volatile":
        return "2.2"  # Ungrounded Generation mit volatile topic

    # Low GN
    if block == "low_gn":
        if any(k in text_lower for k in ["translate", "convert", "format", "rewrite",
                                          "uebersetze", "konvertiere"]):
            return "2.1"  # Utility
        if any(k in text_lower for k in ["write", "create", "compose", "generate",
                                          "poem", "story", "essay",
                                          "schreibe", "erstelle", "verfasse"]):
            return "2.2"  # Ungrounded Generation
        if any(k in text_lower for k in ["summarize", "rewrite this", "fix",
                                          "zusammenfassen", "korrigiere"]):
            return "2.3"  # Grounded Generation
        if any(k in text_lower for k in ["explain", "how does", "how do",
                                          "describe", "difference between",
                                          "erklaere", "wie funktioniert"]):
            return "1.1"  # Fact Retrieval (Explanation)
        if any(k in text_lower for k in ["what is", "who ", "define ", "when ",
                                          "was ist", "wer ", "wann "]):
            return "1.1"  # Fact Retrieval
        return "2.2"  # Default Low GN -> creative

    # High GN
    if block == "high_gn":
        if any(k in text_lower for k in ["plan", "find", "help me", "compare",
                                          "research", "investigate", "look for",
                                          "hilf mir", "finde", "suche", "vergleiche"]):
            return "3.2"  # Open-Ended Investigation
        if any(k in text_lower for k in ["should", "recommend", "best", "advice",
                                          "opinion", "worth", "advisable",
                                          "sollte", "empfehlen", "bester", "meinung"]):
            return "1.3"  # Advisory
        if any(k in text_lower for k in ["current", "latest", "today", "now",
                                          "price", "weather", "stock", "score",
                                          "aktuell", "heute", "Preis", "Wetter"]):
            return "1.2"  # Real-Time Synthesis
        return "1.2"  # Default High GN

    return "1.1"


def ensure_mode_coverage(rows, min_per_mode=3):
    """Stelle sicher, dass jeder Mode mindestens min_per_mode vertreten ist.

    Weist bei Bedarf Prompts anderen Modes zu, um die Mindestabdeckung
    zu erreichen. Modes 3.1 ist ausgenommen (Warnung, kein Fehler).
    """
    required = ["1.1", "1.2", "1.3", "2.1", "2.2", "2.3", "3.2"]

    # Zaehle aktuelle Verteilung
    from collections import Counter
    mode_counts = Counter(r["gio_mode_estimate"] for r in rows if r["block"] != "calibration")

    # Identifiziere unterbesetzte und ueberbesetzte Modes
    under = {m: max(0, min_per_mode - mode_counts.get(m, 0)) for m in required}
    under = {m: n for m, n in under.items() if n > 0}

    if not under:
        return  # Alles gut

    # Ueberbesetzte Modes (>5 Stück)
    over = {m: mode_counts[m] - 5 for m in required if mode_counts.get(m, 0) > 5}

    # Umverteilen: Aus ueberbesetzten Modes in unterbesetzte
    study_rows = [r for r in rows if r["block"] != "calibration"]

    for needed_mode, needed_count in under.items():
        reassigned = 0
        for row in study_rows:
            if reassigned >= needed_count:
                break
            current_mode = row["gio_mode_estimate"]
            if current_mode in over and over[current_mode] > 0:
                row["gio_mode_estimate"] = needed_mode
                row["justification"] += f" [Reassigned to {needed_mode} for coverage.]"
                over[current_mode] -= 1
                reassigned += 1


def main():
    print("=" * 60)
    print("AP2: Automatisches Sampling (Pipeline-Test)")
    print("=" * 60)

    candidate_dir = config.DATA_DIR / "candidates"

    # Lade Kandidaten
    blocks = {
        "low_gn": ("candidate_low_gn.csv", 18, ""),
        "high_gn": ("candidate_high_gn.csv", 18, ""),
        "edge_pt": ("candidate_parametric_trap.csv", 5, "parametric_trap"),
        "edge_id": ("candidate_implicit_demand.csv", 5, "implicit_demand"),
        "edge_cv": ("candidate_creative_volatile.csv", 4, "creative_volatile"),
    }

    all_rows = []
    prompt_id_counter = 1

    for block_key, (filename, n_needed, subtype) in blocks.items():
        filepath = candidate_dir / filename
        if not filepath.exists():
            print(f"  FEHLER: {filepath} nicht gefunden!")
            sys.exit(1)

        df = pd.read_csv(filepath)
        sample = df.head(n_needed)  # Erste n Zeilen (deterministisch)

        # Block-Name fuer sampled_prompts.csv
        if block_key.startswith("edge"):
            block_name = "edge"
        else:
            block_name = block_key

        for _, row in sample.iterrows():
            mode = estimate_gio_mode(row["prompt_text"], block_name, subtype)
            all_rows.append({
                "prompt_id": f"P{prompt_id_counter:02d}",
                "conversation_id": row["conversation_id"],
                "prompt_text": row["prompt_text"],
                "block": block_name,
                "subtype": subtype if block_name == "edge" else "",
                "gio_mode_estimate": mode,
                "justification": f"Auto-selected from {filename} candidates.",
                "source": "WildChat",
                "language": row["language"],
            })
            prompt_id_counter += 1

        print(f"  {block_name:10s} ({subtype or '-':20s}): {len(sample)} Prompts ausgewaehlt")

    # Kalibrierungs-Prompts (aus Low GN, Zeilen 18-22 = nach Studie)
    print("\n  Kalibrierungs-Prompts:")
    calib_candidates = pd.read_csv(candidate_dir / "candidate_low_gn.csv")
    calib_sample = calib_candidates.iloc[18:23]

    for _, row in calib_sample.iterrows():
        mode = estimate_gio_mode(row["prompt_text"], "calibration", "")
        all_rows.append({
            "prompt_id": f"C{prompt_id_counter - 50:02d}",
            "conversation_id": row["conversation_id"],
            "prompt_text": row["prompt_text"],
            "block": "calibration",
            "subtype": "",
            "gio_mode_estimate": mode,
            "justification": "Calibration prompt for rater training.",
            "source": "WildChat",
            "language": row["language"],
        })
        prompt_id_counter += 1

    print(f"  {'calibration':10s} ({'-':20s}): {len(calib_sample)} Prompts ausgewaehlt")

    # Mode-Abdeckung sicherstellen (Umverteilung falls noetig)
    print("\n  Mode-Abdeckung pruefen und ggf. umverteilen...")
    ensure_mode_coverage(all_rows, min_per_mode=3)

    # Speichern
    df_final = pd.DataFrame(all_rows)
    df_final.to_csv(config.SAMPLED_PROMPTS_PATH, index=False)

    # Zusammenfassung
    study = df_final[df_final["block"] != "calibration"]
    calib = df_final[df_final["block"] == "calibration"]

    print(f"\n  Gesamt: {len(study)} Studien + {len(calib)} Kalibrierung = {len(df_final)} Prompts")

    print(f"\n  Block-Verteilung (Studie):")
    for block, n in sorted(study["block"].value_counts().items()):
        print(f"    {block:15s}: {n}")

    print(f"\n  GIO-Mode-Schaetzung (Studie):")
    for mode in sorted(config.DROPDOWN_GIO_MODES):
        n = (study["gio_mode_estimate"] == mode).sum()
        name = config.GIO_MODES.get(mode, {}).get("name", "?")
        marker = " OK" if n >= 3 else " <-- FEHLT" if mode != "3.1" else ""
        print(f"    Mode {mode} ({name:25s}): {n}{marker}")

    print(f"\n  Gespeichert: {config.SAMPLED_PROMPTS_PATH}")
    print("  Naechster Schritt: make ap2-validate")


if __name__ == "__main__":
    main()
