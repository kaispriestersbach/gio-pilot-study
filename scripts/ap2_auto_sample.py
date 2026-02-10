"""
AP2 Hilfsskript: Review-gestuetztes Sampling.

Waehlt automatisch 50 Studien-Prompts + 5 Kalibrierungs-Prompts
aus den Kandidaten-Listen (data/candidates/), gefiltert durch die
v2-Reviews (data/candidate_reviews/review_v2_*.csv).

Nur Prompts mit verdict=ACCEPT werden beruecksichtigt.
Die GIO-Mode-Schaetzung stammt aus den Reviews (nicht aus Heuristik).

Output: data/sampled_prompts.csv
"""

import sys
from collections import Counter
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config


def load_accepted_candidates(candidate_path, review_path, n_needed=0):
    """Lade Kandidaten und filtere auf ACCEPT-Verdicts aus der Review.

    Falls n_needed > 0 und nicht genug ACCEPTs vorhanden sind, werden
    EDGE_CASE-Prompts als Fallback hinzugenommen.

    Returns:
        DataFrame mit Spalten aus Kandidaten-CSV plus 'mode' aus Review.
    """
    candidates = pd.read_csv(candidate_path)
    reviews = pd.read_csv(review_path)

    # Primaer: ACCEPTs
    accepted_revs = reviews[reviews["verdict"] == "ACCEPT"][["conversation_id", "mode"]]
    merged = candidates.merge(accepted_revs, on="conversation_id", how="inner")

    # Fallback: EDGE_CASEs wenn ACCEPTs nicht reichen
    if n_needed > 0 and len(merged) < n_needed:
        shortfall = n_needed - len(merged)
        edge_revs = reviews[reviews["verdict"] == "EDGE_CASE"][["conversation_id", "mode"]]
        edge_merged = candidates.merge(edge_revs, on="conversation_id", how="inner")
        if len(edge_merged) > 0:
            # Nur so viele EDGE_CASEs wie noetig
            edge_fill = edge_merged.head(min(shortfall, len(edge_merged)))
            merged = pd.concat([merged, edge_fill], ignore_index=True)
            print(f"    -> {len(edge_fill)} EDGE_CASE(s) als Fallback hinzugefuegt")

    return merged


def ensure_mode_coverage(rows, min_per_mode=3):
    """Stelle sicher, dass jeder Mode mindestens min_per_mode vertreten ist.

    Weist bei Bedarf Prompts anderen Modes zu, um die Mindestabdeckung
    zu erreichen. Mode 3.1 ist ausgenommen (Warnung, kein Fehler).
    """
    required = ["1.1", "1.2", "1.3", "2.1", "2.2", "2.3", "3.2"]

    # Zaehle aktuelle Verteilung
    mode_counts = Counter(
        r["gio_mode_estimate"] for r in rows if r["block"] != "calibration"
    )

    # Identifiziere unterbesetzte und ueberbesetzte Modes
    under = {m: max(0, min_per_mode - mode_counts.get(m, 0)) for m in required}
    under = {m: n for m, n in under.items() if n > 0}

    if not under:
        return  # Alles gut

    # Ueberbesetzte Modes (>5 Stueck)
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
    print("AP2: Review-gestuetztes Sampling (v2)")
    print("=" * 60)

    candidate_dir = config.DATA_DIR / "candidates"
    review_dir = config.DATA_DIR / "candidate_reviews"

    # Block-Definitionen: (candidate_file, review_file, block_name, subtype, n_needed)
    blocks = [
        ("candidate_low_gn.csv", "review_v2_low_gn.csv", "low_gn", "", 18),
        ("candidate_high_gn.csv", "review_v2_high_gn.csv", "high_gn", "", 18),
        ("candidate_parametric_trap.csv", "review_v2_parametric_trap.csv", "edge", "parametric_trap", 5),
        ("candidate_implicit_demand.csv", "review_v2_implicit_demand.csv", "edge", "implicit_demand", 5),
        ("candidate_creative_volatile.csv", "review_v2_creative_volatile.csv", "edge", "creative_volatile", 4),
    ]

    all_rows = []
    prompt_id_counter = 1
    low_gn_accepted = None  # Fuer Kalibrierung merken

    for cand_file, rev_file, block_name, subtype, n_needed in blocks:
        cand_path = candidate_dir / cand_file
        rev_path = review_dir / rev_file

        if not cand_path.exists():
            print(f"  FEHLER: {cand_path} nicht gefunden!")
            sys.exit(1)
        if not rev_path.exists():
            print(f"  FEHLER: {rev_path} nicht gefunden!")
            sys.exit(1)

        accepted = load_accepted_candidates(cand_path, rev_path, n_needed=n_needed)
        n_available = len(accepted)

        # low_gn merken fuer Kalibrierung
        if block_name == "low_gn":
            low_gn_accepted = accepted.copy()

        # Warnung wenn nicht genug Kandidaten
        if n_available < n_needed:
            print(f"  WARNUNG: {cand_file}: nur {n_available} ACCEPTs, "
                  f"brauche {n_needed}. Nehme alle verfuegbaren.")

        # Stratifiziertes Sampling: nach Mode diversifizieren
        n_sample = min(n_needed, n_available)
        if n_sample < n_available:
            # Versuche Mode-Diversitaet durch gruppiertes Sampling
            sample = _stratified_sample(accepted, n_sample)
        else:
            sample = accepted.head(n_sample)

        label = f"{block_name}/{subtype}" if subtype else block_name
        print(f"  {label:30s}: {n_available:3d} ACCEPTs -> {n_sample} ausgewaehlt")

        for _, row in sample.iterrows():
            # Mode aus Review uebernehmen (nicht aus Heuristik)
            review_mode = str(row["mode"])
            # Parametric Traps: Review gibt "1.1/1.2" — fuer Validation auf "1.2" mappen
            if review_mode == "1.1/1.2":
                gio_mode = "1.2"
            else:
                gio_mode = review_mode

            all_rows.append({
                "prompt_id": f"P{prompt_id_counter:02d}",
                "conversation_id": row["conversation_id"],
                "prompt_text": row["prompt_text"],
                "block": block_name,
                "subtype": subtype if block_name == "edge" else "",
                "gio_mode_estimate": gio_mode,
                "justification": f"Review-accepted ({review_mode}) from {cand_file}.",
                "source": "WildChat",
                "language": row["language"],
            })
            prompt_id_counter += 1

    # --- Transaktionale Prompts (Mode 3.1) ---
    # Separat gesucht, da WildChat fast keine echten 3.1 Prompts enthaelt
    tx_cand_path = candidate_dir / "candidate_transactional.csv"
    tx_rev_path = review_dir / "review_v2_transactional.csv"
    if tx_cand_path.exists() and tx_rev_path.exists():
        tx_accepted = load_accepted_candidates(tx_cand_path, tx_rev_path, n_needed=1)
        tx_already_used = {r["conversation_id"] for r in all_rows}
        tx_new = tx_accepted[~tx_accepted["conversation_id"].isin(tx_already_used)]

        if len(tx_new) > 0:
            # Ersetze einen Prompt im high_gn Block mit ueberbesetztem Mode
            # um die Block-Verteilung beizubehalten (high_gn: 18)
            replaced = False
            # Finde den haeufigsten Mode in high_gn und ersetze den letzten davon
            hg_modes = Counter(
                r["gio_mode_estimate"] for r in all_rows if r["block"] == "high_gn"
            )
            most_common_mode = hg_modes.most_common(1)[0][0] if hg_modes else None

            if most_common_mode:
                # Letzten Prompt mit diesem Mode in high_gn ersetzen (rueckwaerts)
                for i in range(len(all_rows) - 1, -1, -1):
                    row = all_rows[i]
                    if row["block"] == "high_gn" and row["gio_mode_estimate"] == most_common_mode:
                        replaced_id = row["prompt_id"]
                        tx_row = tx_new.iloc[0]
                        all_rows[i] = {
                            "prompt_id": replaced_id,
                            "conversation_id": tx_row["conversation_id"],
                            "prompt_text": tx_row["prompt_text"],
                            "block": "high_gn",
                            "subtype": "",
                            "gio_mode_estimate": "3.1",
                            "justification": "Transactional (3.1) from dedicated WildChat search. "
                                             f"Replaces overrepresented {most_common_mode} in high_gn.",
                            "source": "WildChat",
                            "language": tx_row["language"],
                        }
                        print(f"\n  Transactional (3.1): 1 Prompt eingefuegt "
                              f"(ersetzt {replaced_id}/{most_common_mode} in high_gn)")
                        replaced = True
                        break

            if not replaced:
                print(f"\n  WARNUNG: Kein ersetzbarer high_gn Prompt fuer 3.1 gefunden")
        else:
            print(f"\n  Transactional: Keine neuen ACCEPTs verfuegbar")
    else:
        print(f"\n  Transactional: Keine Kandidaten-/Review-Dateien gefunden (optional)")

    # --- Kalibrierungs-Prompts ---
    # Aus low_gn ACCEPTs die NICHT bereits fuer Studie verwendet wurden
    print(f"\n  Kalibrierungs-Prompts:")
    if low_gn_accepted is None:
        print("  FEHLER: low_gn Kandidaten nicht geladen!")
        sys.exit(1)

    study_ids = {r["conversation_id"] for r in all_rows}
    calib_pool = low_gn_accepted[~low_gn_accepted["conversation_id"].isin(study_ids)]

    n_calib = min(5, len(calib_pool))
    if n_calib < 5:
        print(f"  WARNUNG: Nur {n_calib} low_gn ACCEPTs fuer Kalibrierung verfuegbar.")

    calib_sample = calib_pool.head(n_calib)

    for _, row in calib_sample.iterrows():
        review_mode = str(row["mode"])
        all_rows.append({
            "prompt_id": f"C{prompt_id_counter - 50:02d}",
            "conversation_id": row["conversation_id"],
            "prompt_text": row["prompt_text"],
            "block": "calibration",
            "subtype": "",
            "gio_mode_estimate": review_mode,
            "justification": f"Calibration prompt (review-accepted, {review_mode}).",
            "source": "WildChat",
            "language": row["language"],
        })
        prompt_id_counter += 1

    print(f"  {'calibration':30s}: {len(calib_pool):3d} verfuegbar -> {n_calib} ausgewaehlt")

    # --- Mode-Abdeckung sicherstellen ---
    print("\n  Mode-Abdeckung pruefen und ggf. umverteilen...")
    ensure_mode_coverage(all_rows, min_per_mode=3)

    # --- Speichern ---
    df_final = pd.DataFrame(all_rows)
    df_final.to_csv(config.SAMPLED_PROMPTS_PATH, index=False)

    # --- Zusammenfassung ---
    study = df_final[df_final["block"] != "calibration"]
    calib = df_final[df_final["block"] == "calibration"]

    print(f"\n  Gesamt: {len(study)} Studien + {len(calib)} Kalibrierung "
          f"= {len(df_final)} Prompts")

    print(f"\n  Block-Verteilung (Studie):")
    for block, n in sorted(study["block"].value_counts().items()):
        print(f"    {block:15s}: {n}")

    print(f"\n  Subtype-Verteilung (Edge Cases):")
    edges = study[study["block"] == "edge"]
    for st, n in sorted(edges["subtype"].value_counts().items()):
        print(f"    {st:25s}: {n}")

    print(f"\n  GIO-Mode-Schaetzung (Studie):")
    for mode in sorted(config.DROPDOWN_GIO_MODES):
        n = (study["gio_mode_estimate"] == mode).sum()
        name = config.GIO_MODES.get(mode, {}).get("name", "?")
        marker = " OK" if n >= 3 else " <-- FEHLT" if mode != "3.1" else ""
        print(f"    Mode {mode} ({name:25s}): {n}{marker}")

    print(f"\n  Sprach-Verteilung:")
    for lang, n in sorted(df_final["language"].value_counts().items()):
        print(f"    {lang}: {n}")

    print(f"\n  Gespeichert: {config.SAMPLED_PROMPTS_PATH}")
    print("  Naechster Schritt: make ap2-validate")


def _stratified_sample(df, n, seed=None):
    """Stratifiziertes Sampling nach Mode-Diversitaet.

    Versucht, moeglichst viele verschiedene Modes in der Stichprobe zu haben,
    indem aus jeder Mode-Gruppe mindestens 1 Prompt gezogen wird (falls moeglich).
    """
    if seed is None:
        seed = config.RANDOM_SEED

    modes = df["mode"].unique()

    if len(modes) <= 1 or n >= len(df):
        # Nur ein Mode oder alle noetig -> einfaches Random-Sample
        return df.sample(n=min(n, len(df)), random_state=seed)

    selected = []
    remaining_budget = n

    # Phase 1: Je 1 Prompt pro Mode (garantierte Diversitaet)
    for mode in modes:
        if remaining_budget <= 0:
            break
        mode_group = df[df["mode"] == mode]
        pick = mode_group.sample(n=1, random_state=seed)
        selected.append(pick)
        remaining_budget -= 1

    # Phase 2: Restliches Budget proportional auffuellen
    if remaining_budget > 0:
        already_picked_ids = pd.concat(selected)["conversation_id"].tolist()
        pool = df[~df["conversation_id"].isin(already_picked_ids)]
        if len(pool) > 0:
            fill = pool.sample(n=min(remaining_budget, len(pool)), random_state=seed)
            selected.append(fill)

    result = pd.concat(selected).head(n)
    return result


if __name__ == "__main__":
    main()
