"""
AP5: Auswertungs-Script fuer die GIO Pilot Study.

Berechnet nach der Annotation:
  - Cohen's kappa fuer retrieval_judgment (binaer)
  - Cohen's kappa fuer gio_mode (nominal, 8 Kategorien)
  - Gewichtetes Cohen's kappa fuer gn_level (ordinal, 5 Stufen, linear)
  - Bootstrap 95%-Konfidenzintervalle (1000 Iterationen) fuer alle drei kappa-Werte
  - Confusion Matrix: Baseline vs. Experten-Konsens
  - F1-Score, Precision, Recall der Baseline gegen Experten-Konsens
  - Liste aller Disagreement-Faelle

Input:  output/annotations_rater_a.json, output/annotations_rater_b.json,
        data/baseline_predictions.csv
Output: Console + data/evaluation_results.csv
"""

import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import (
    cohen_kappa_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config

warnings.filterwarnings("ignore", category=RuntimeWarning)


def load_rater_data():
    """Lade Rater-Daten aus den JSON-Annotationsdateien."""
    with open(config.ANNOTATION_RATER_A_JSON, "r", encoding="utf-8") as f:
        data_a = json.load(f)
    with open(config.ANNOTATION_RATER_B_JSON, "r", encoding="utf-8") as f:
        data_b = json.load(f)

    rater_a = pd.DataFrame(data_a["study"]).set_index("prompt_id").sort_index()
    rater_b = pd.DataFrame(data_b["study"]).set_index("prompt_id").sort_index()

    # Sicherstellen, dass gleiche Prompts vorhanden
    common_ids = rater_a.index.intersection(rater_b.index)
    if len(common_ids) < len(rater_a):
        diff = set(rater_a.index) - set(common_ids)
        print(f"WARNUNG: {len(diff)} Prompts nur in Rater_A: {diff}")
    if len(common_ids) < len(rater_b):
        diff = set(rater_b.index) - set(common_ids)
        print(f"WARNUNG: {len(diff)} Prompts nur in Rater_B: {diff}")

    rater_a = rater_a.loc[common_ids]
    rater_b = rater_b.loc[common_ids]

    return rater_a, rater_b


def load_baseline_data():
    """Lade Baseline-Vorhersagen aus der CSV-Datei."""
    baseline = pd.read_csv(config.BASELINE_PREDICTIONS_PATH)
    baseline = baseline.set_index("prompt_id").sort_index()
    return baseline


def check_missing_values(rater_a, rater_b, column):
    """Pruefe auf fehlende Werte und gib bereinigte Arrays zurueck."""
    a = rater_a[column]
    b = rater_b[column]

    # Fehlende Werte identifizieren
    missing_a = a.isna()
    missing_b = b.isna()
    missing = missing_a | missing_b

    n_missing = missing.sum()
    if n_missing > 0:
        print(f"  WARNUNG: {n_missing} fehlende Werte in '{column}' — werden ausgeschlossen.")
        ids = missing[missing].index.tolist()
        print(f"           Betroffene IDs: {ids}")

    return a[~missing].values, b[~missing].values, ~missing


def bootstrap_kappa(a, b, n_iterations=1000, weights=None, seed=42):
    """Berechne Bootstrap 95%-Konfidenzintervall fuer Cohen's kappa."""
    rng = np.random.default_rng(seed)
    n = len(a)
    kappas = []

    for _ in range(n_iterations):
        idx = rng.integers(0, n, size=n)
        a_sample = a[idx]
        b_sample = b[idx]

        # Sonderfall: Alle gleich -> kappa undefiniert
        if len(set(a_sample)) <= 1 and len(set(b_sample)) <= 1:
            if np.array_equal(a_sample, b_sample):
                kappas.append(1.0)
            else:
                kappas.append(0.0)
            continue

        try:
            k = cohen_kappa_score(a_sample, b_sample, weights=weights)
            kappas.append(k)
        except (ValueError, ZeroDivisionError):
            continue

    kappas = np.array(kappas)
    if len(kappas) == 0:
        return np.nan, np.nan
    ci_low = np.percentile(kappas, 2.5)
    ci_high = np.percentile(kappas, 97.5)
    return ci_low, ci_high


def compute_inter_rater_agreement(rater_a, rater_b):
    """Berechne alle Inter-Rater-Agreement-Metriken."""
    results = {}

    print("\n" + "=" * 60)
    print("1. Inter-Rater Agreement")
    print("=" * 60)

    # --- retrieval_judgment (binaer) ---
    print("\n--- retrieval_judgment (binaer: Yes/No) ---")
    a_ret, b_ret, mask_ret = check_missing_values(rater_a, rater_b, "retrieval_judgment")

    if len(a_ret) > 0:
        # Zu numerisch konvertieren
        a_ret_num = np.array([1 if x == "Yes" else 0 for x in a_ret])
        b_ret_num = np.array([1 if x == "Yes" else 0 for x in b_ret])

        kappa_ret = cohen_kappa_score(a_ret_num, b_ret_num)
        ci_low, ci_high = bootstrap_kappa(a_ret_num, b_ret_num)
        agreement = np.mean(a_ret_num == b_ret_num)

        print(f"  Cohen's kappa:   {kappa_ret:.3f}")
        print(f"  95% CI:          [{ci_low:.3f}, {ci_high:.3f}]")
        print(f"  Rohuebereinst.:  {agreement:.1%} ({int(agreement * len(a_ret))}/{len(a_ret)})")

        results["kappa_retrieval"] = kappa_ret
        results["kappa_retrieval_ci_low"] = ci_low
        results["kappa_retrieval_ci_high"] = ci_high
        results["agreement_retrieval"] = agreement
        results["n_retrieval"] = len(a_ret)
    else:
        print("  FEHLER: Keine gueltigen Werte fuer retrieval_judgment.")

    # --- gio_mode (nominal, 8 Kategorien) ---
    print("\n--- gio_mode (nominal, 8 Kategorien) ---")
    a_mode, b_mode, mask_mode = check_missing_values(rater_a, rater_b, "gio_mode")

    if len(a_mode) > 0:
        # Zu String konvertieren
        a_mode_str = np.array([str(x) for x in a_mode])
        b_mode_str = np.array([str(x) for x in b_mode])

        kappa_mode = cohen_kappa_score(a_mode_str, b_mode_str)
        ci_low, ci_high = bootstrap_kappa(a_mode_str, b_mode_str)
        agreement = np.mean(a_mode_str == b_mode_str)

        print(f"  Cohen's kappa:   {kappa_mode:.3f}")
        print(f"  95% CI:          [{ci_low:.3f}, {ci_high:.3f}]")
        print(f"  Rohuebereinst.:  {agreement:.1%} ({int(agreement * len(a_mode))}/{len(a_mode)})")

        results["kappa_gio_mode"] = kappa_mode
        results["kappa_gio_mode_ci_low"] = ci_low
        results["kappa_gio_mode_ci_high"] = ci_high
        results["agreement_gio_mode"] = agreement
        results["n_gio_mode"] = len(a_mode)
    else:
        print("  FEHLER: Keine gueltigen Werte fuer gio_mode.")

    # --- gn_level (ordinal, 5 Stufen, linear gewichtet) ---
    print("\n--- gn_level (ordinal: None/GfC/Low/Medium/High, linear gewichtet) ---")
    a_gn, b_gn, mask_gn = check_missing_values(rater_a, rater_b, "gn_level")

    if len(a_gn) > 0:
        # Ordinal-Mapping (5-stufig: None < Grounding from Context < Low < Medium < High)
        ordinal_map = {"None": 0, "Grounding from Context": 1, "Low": 2, "Medium": 3, "High": 4}
        a_gn_ord = np.array([ordinal_map.get(str(x), -1) for x in a_gn])
        b_gn_ord = np.array([ordinal_map.get(str(x), -1) for x in b_gn])

        # Ungueltige Werte filtern
        valid = (a_gn_ord >= 0) & (b_gn_ord >= 0)
        if valid.sum() < len(a_gn):
            n_invalid = len(a_gn) - valid.sum()
            print(f"  WARNUNG: {n_invalid} ungueltige Werte (nicht in ordinal_map) ausgeschlossen.")

        a_gn_valid = a_gn_ord[valid]
        b_gn_valid = b_gn_ord[valid]

        kappa_gn = cohen_kappa_score(a_gn_valid, b_gn_valid, weights="linear")
        ci_low, ci_high = bootstrap_kappa(a_gn_valid, b_gn_valid, weights="linear")
        agreement = np.mean(a_gn_valid == b_gn_valid)

        print(f"  Cohen's kappa (gew.): {kappa_gn:.3f}")
        print(f"  95% CI:               [{ci_low:.3f}, {ci_high:.3f}]")
        print(f"  Rohuebereinst.:       {agreement:.1%} ({int(agreement * len(a_gn_valid))}/{len(a_gn_valid)})")

        results["kappa_gn_level"] = kappa_gn
        results["kappa_gn_level_ci_low"] = ci_low
        results["kappa_gn_level_ci_high"] = ci_high
        results["agreement_gn_level"] = agreement
        results["n_gn_level"] = len(a_gn_valid)
    else:
        print("  FEHLER: Keine gueltigen Werte fuer gn_level.")

    return results


def compute_baseline_comparison(rater_a, rater_b, baseline):
    """Vergleiche Baseline-Vorhersagen mit Experten-Konsens."""
    results = {}

    print("\n" + "=" * 60)
    print("2. Baseline vs. Experten-Konsens")
    print("=" * 60)

    # Experten-Konsens bilden (nur bei Uebereinstimmung)
    a_ret = rater_a["retrieval_judgment"]
    b_ret = rater_b["retrieval_judgment"]

    # Gemeinsame IDs mit Baseline
    common_ids = rater_a.index.intersection(baseline.index)
    if len(common_ids) == 0:
        print("  FEHLER: Keine gemeinsamen Prompt-IDs zwischen Ratern und Baseline.")
        return results

    consensus = {}
    dissens_ids = []
    for pid in common_ids:
        a_val = a_ret.get(pid)
        b_val = b_ret.get(pid)
        if pd.isna(a_val) or pd.isna(b_val):
            continue
        if a_val == b_val:
            consensus[pid] = 1 if a_val == "Yes" else 0
        else:
            dissens_ids.append(pid)

    n_consensus = len(consensus)
    n_dissens = len(dissens_ids)
    print(f"\n  Konsens-Faelle:  {n_consensus}")
    print(f"  Dissens-Faelle:  {n_dissens} (werden von Baseline-Vergleich ausgeschlossen)")

    if n_consensus == 0:
        print("  FEHLER: Kein Konsens — Baseline-Vergleich nicht moeglich.")
        return results

    # Baseline-Predictions fuer Konsens-Faelle
    consensus_ids = list(consensus.keys())
    expert_labels = np.array([consensus[pid] for pid in consensus_ids])
    baseline_labels = np.array([
        int(baseline.loc[pid, "baseline_prediction"]) for pid in consensus_ids
    ])

    # Confusion Matrix
    cm = confusion_matrix(expert_labels, baseline_labels, labels=[0, 1])
    print(f"\n  Confusion Matrix (Experten vs. Baseline):")
    print(f"                   Baseline=No  Baseline=Yes")
    print(f"  Expert=No  (TN)  {cm[0, 0]:>8}     (FP) {cm[0, 1]:>8}")
    print(f"  Expert=Yes (FN)  {cm[1, 0]:>8}     (TP) {cm[1, 1]:>8}")

    # Metriken
    f1 = f1_score(expert_labels, baseline_labels, zero_division=0)
    prec = precision_score(expert_labels, baseline_labels, zero_division=0)
    rec = recall_score(expert_labels, baseline_labels, zero_division=0)
    accuracy = np.mean(expert_labels == baseline_labels)

    print(f"\n  F1-Score:    {f1:.3f}")
    print(f"  Precision:   {prec:.3f}")
    print(f"  Recall:      {rec:.3f}")
    print(f"  Accuracy:    {accuracy:.1%}")

    results["baseline_f1"] = f1
    results["baseline_precision"] = prec
    results["baseline_recall"] = rec
    results["baseline_accuracy"] = accuracy
    results["n_consensus"] = n_consensus
    results["n_dissens"] = n_dissens
    results["cm_tn"] = int(cm[0, 0])
    results["cm_fp"] = int(cm[0, 1])
    results["cm_fn"] = int(cm[1, 0])
    results["cm_tp"] = int(cm[1, 1])

    return results


def find_disagreements(rater_a, rater_b):
    """Finde alle Faelle, in denen die Rater uneins sind."""
    print("\n" + "=" * 60)
    print("3. Disagreement-Analyse")
    print("=" * 60)

    annotation_cols = ["gio_mode", "i_gap", "t_decay", "e_spec",
                       "v_volatility", "gn_level", "retrieval_judgment", "confidence"]

    disagreements = []
    for pid in rater_a.index:
        if pid not in rater_b.index:
            continue
        for col in annotation_cols:
            a_val = rater_a.loc[pid, col]
            b_val = rater_b.loc[pid, col]
            if pd.isna(a_val) and pd.isna(b_val):
                continue
            if str(a_val) != str(b_val):
                disagreements.append({
                    "prompt_id": pid,
                    "column": col,
                    "rater_a": str(a_val),
                    "rater_b": str(b_val),
                    "prompt_text": rater_a.loc[pid, "prompt_text"][:80] if "prompt_text" in rater_a.columns else "",
                })

    if not disagreements:
        print("\n  Keine Disagreements gefunden (perfekte Uebereinstimmung).")
        return pd.DataFrame()

    dis_df = pd.DataFrame(disagreements)

    # Zusammenfassung
    dis_by_col = dis_df["column"].value_counts()
    print(f"\n  Gesamt Disagreements: {len(dis_df)}")
    print(f"  Betroffene Prompts:   {dis_df['prompt_id'].nunique()}")
    print("\n  Disagreements pro Feld:")
    for col, n in dis_by_col.items():
        print(f"    {col:25s}: {n:3d}")

    # Prompts mit den meisten Disagreements
    dis_by_prompt = dis_df.groupby("prompt_id").size().sort_values(ascending=False)
    print(f"\n  Top-5 Prompts mit meisten Disagreements:")
    for pid, n in dis_by_prompt.head(5).items():
        text = dis_df[dis_df["prompt_id"] == pid]["prompt_text"].iloc[0]
        print(f"    {pid}: {n} Felder — {text}")

    return dis_df


def main():
    print("=" * 60)
    print("AP5: Auswertung der GIO Pilot Study")
    print("=" * 60)

    # Daten laden
    print(f"\nLade Rater-Daten aus JSON...")
    for p in [config.ANNOTATION_RATER_A_JSON, config.ANNOTATION_RATER_B_JSON]:
        if not p.exists():
            print(f"FEHLER: {p} nicht gefunden.")
            print("Bitte sicherstellen, dass die Annotation abgeschlossen ist.")
            sys.exit(1)

    rater_a, rater_b = load_rater_data()
    print(f"  Rater_A: {len(rater_a)} Prompts")
    print(f"  Rater_B: {len(rater_b)} Prompts")

    if not config.BASELINE_PREDICTIONS_PATH.exists():
        print(f"FEHLER: {config.BASELINE_PREDICTIONS_PATH} nicht gefunden.")
        sys.exit(1)

    baseline = load_baseline_data()
    print(f"  Baseline: {len(baseline)} Prompts")

    # 1. Inter-Rater Agreement
    irr_results = compute_inter_rater_agreement(rater_a, rater_b)

    # 2. Baseline vs. Experten-Konsens
    baseline_results = compute_baseline_comparison(rater_a, rater_b, baseline)

    # 3. Disagreement-Analyse
    dis_df = find_disagreements(rater_a, rater_b)

    # Ergebnisse zusammenfuehren und speichern
    all_results = {**irr_results, **baseline_results}
    results_df = pd.DataFrame([all_results])

    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(config.EVALUATION_RESULTS_PATH, index=False)
    print(f"\nErgebnisse gespeichert: {config.EVALUATION_RESULTS_PATH}")

    # Disagreements als CSV
    if not dis_df.empty:
        dis_path = config.DATA_DIR / "disagreements.csv"
        dis_df.to_csv(dis_path, index=False)
        print(f"Disagreements gespeichert: {dis_path}")

    # Zusammenfassung
    print("\n" + "=" * 60)
    print("ZUSAMMENFASSUNG")
    print("=" * 60)
    if "kappa_retrieval" in all_results:
        print(f"  kappa(retrieval): {all_results['kappa_retrieval']:.3f} "
              f"[{all_results.get('kappa_retrieval_ci_low', 'N/A'):.3f}, "
              f"{all_results.get('kappa_retrieval_ci_high', 'N/A'):.3f}]")
    if "kappa_gio_mode" in all_results:
        print(f"  kappa(gio_mode):  {all_results['kappa_gio_mode']:.3f} "
              f"[{all_results.get('kappa_gio_mode_ci_low', 'N/A'):.3f}, "
              f"{all_results.get('kappa_gio_mode_ci_high', 'N/A'):.3f}]")
    if "kappa_gn_level" in all_results:
        print(f"  kappa(gn_level):  {all_results['kappa_gn_level']:.3f} "
              f"[{all_results.get('kappa_gn_level_ci_low', 'N/A'):.3f}, "
              f"{all_results.get('kappa_gn_level_ci_high', 'N/A'):.3f}]")
    if "baseline_f1" in all_results:
        print(f"  Baseline F1:      {all_results['baseline_f1']:.3f}")
        print(f"  Baseline Prec:    {all_results['baseline_precision']:.3f}")
        print(f"  Baseline Recall:  {all_results['baseline_recall']:.3f}")

    print("\nFertig.")


if __name__ == "__main__":
    main()
