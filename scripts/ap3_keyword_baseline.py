"""
AP3: Keyword-Baseline fuer Retrieval-Vorhersage.

Nimmt die 50 Studien-Prompts als Input und trifft eine binaere
Retrieval-Vorhersage basierend auf einfachen Keyword-Regeln:

Retrieval = YES wenn mindestens eine Bedingung zutrifft:
  1. Temporale Marker (current, latest, today, 2024, 2025, 2026, aktuell, neueste)
  2. Volatilitaets-Indikatoren (price, weather, score, poll, Preis, Wetter, Kurs, Umfrage)
  3. Interrogativ + Named Entity (Prompt beginnt mit Who/When/Wer/Wann UND enthaelt NE)
  4. Named Entity NOT IN common_knowledge_list

Input:  data/sampled_prompts.csv
Output: data/baseline_predictions.csv
"""

import sys
from pathlib import Path

import pandas as pd
import spacy

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config


def load_spacy_models():
    """Lade spaCy-Modelle fuer EN und DE NER."""
    models = {}
    try:
        models["en"] = spacy.load("en_core_web_sm")
    except OSError:
        print("WARNUNG: en_core_web_sm nicht installiert.")
        print("  python -m spacy download en_core_web_sm")
        sys.exit(1)
    try:
        models["de"] = spacy.load("de_core_news_sm")
    except OSError:
        print("WARNUNG: de_core_news_sm nicht installiert. Deutsche Prompts nutzen EN-Modell.")
        models["de"] = models["en"]
    return models


def get_named_entities(text, nlp):
    """Extrahiere Named Entities aus dem Text.

    Nur Entities mit hoher Relevanz fuer Grounding Necessity:
    PERSON, ORG, GPE, PRODUCT, EVENT, WORK_OF_ART, FAC, LAW.
    Ausgeschlossen: NORP (Nationalitaeten/Sprachen), LANGUAGE, CARDINAL, ORDINAL, etc.
    """
    doc = nlp(text)
    entities = set()
    relevant_labels = {"PERSON", "ORG", "GPE", "PRODUCT", "EVENT",
                       "WORK_OF_ART", "FAC", "LAW", "PER"}
    for ent in doc.ents:
        if ent.label_ in relevant_labels:
            entities.add(ent.text)
    return entities


def check_temporal_markers(text):
    """Regel 1: Temporale Marker."""
    text_lower = text.lower()
    found = []
    for marker in config.BASELINE_TEMPORAL_MARKERS:
        if marker.lower() in text_lower:
            found.append(marker)
    return found


def check_volatility_indicators(text):
    """Regel 2: Volatilitaets-Indikatoren."""
    text_lower = text.lower()
    found = []
    for indicator in config.BASELINE_VOLATILITY_INDICATORS:
        if indicator.lower() in text_lower:
            found.append(indicator)
    return found


def check_interrogative_entity(text, entities):
    """Regel 3: Prompt beginnt mit Who/When/Wer/Wann UND enthaelt Named Entity."""
    text_lower = text.lower().strip()
    starts_interrogative = any(
        text_lower.startswith(starter)
        for starter in config.BASELINE_INTERROGATIVE_STARTERS
    )
    if starts_interrogative and len(entities) > 0:
        return True
    return False


def check_unknown_entities(entities):
    """Regel 4: Named Entity NOT IN common_knowledge_list."""
    common_lower = {e.lower() for e in config.COMMON_KNOWLEDGE_ENTITIES}
    unknown = []
    for ent in entities:
        if ent.lower() not in common_lower:
            unknown.append(ent)
    return unknown


def predict_retrieval(text, nlp):
    """Wende alle 4 Regeln an und gib (prediction, triggered_rules) zurueck."""
    triggered = []

    # Regel 1: Temporale Marker
    temporal = check_temporal_markers(text)
    if temporal:
        triggered.append(f"temporal:{','.join(temporal[:3])}")

    # Regel 2: Volatilitaets-Indikatoren
    volatility = check_volatility_indicators(text)
    if volatility:
        triggered.append(f"volatility:{','.join(volatility[:3])}")

    # NER (wird fuer Regel 3 und 4 benoetigt)
    entities = get_named_entities(text, nlp)

    # Regel 3: Interrogativ + Entity
    if check_interrogative_entity(text, entities):
        triggered.append(f"interrogative+entity")

    # Regel 4: Unbekannte Entities
    unknown = check_unknown_entities(entities)
    if unknown:
        triggered.append(f"unknown_entity:{','.join(unknown[:3])}")

    prediction = 1 if len(triggered) > 0 else 0
    return prediction, "; ".join(triggered) if triggered else ""


def run_sanity_check(nlp_en):
    """10 hartcodierte Testfaelle als Sanity Check."""
    print("\n--- Sanity Check (10 Testfaelle) ---")
    test_cases = [
        # 5x klar Retrieval (expected=1)
        ("What is the current stock price of Tesla?", 1),
        ("Who is the CEO of Microsoft in 2025?", 1),
        ("What are the latest election poll results?", 1),
        ("What is the weather forecast for Berlin today?", 1),
        ("How much does the iPhone 16 cost currently?", 1),
        # 5x klar kein Retrieval (expected=0)
        ("Write a poem about the ocean.", 0),
        ("Translate 'hello' to Spanish.", 0),
        ("What is the speed of light?", 0),
        ("Explain how gravity works.", 0),
        ("Create a short story about a cat.", 0),
    ]

    all_passed = True
    for text, expected in test_cases:
        pred, rules = predict_retrieval(text, nlp_en)
        status = "OK" if pred == expected else "FAIL"
        if pred != expected:
            all_passed = False
        print(f"  [{status}] expected={expected} got={pred} | {text[:60]}")
        if rules:
            print(f"         Regeln: {rules}")

    if all_passed:
        print("\n  Alle 10 Sanity Checks bestanden.")
    else:
        print("\n  WARNUNG: Nicht alle Sanity Checks bestanden!")

    return all_passed


def main():
    print("=" * 60)
    print("AP3: Keyword-Baseline")
    print("=" * 60)

    # spaCy laden
    print("\n[1/4] Lade spaCy-Modelle...")
    nlp_models = load_spacy_models()
    print("       Modelle geladen.")

    # Prompts laden
    print(f"\n[2/4] Lade Prompts aus {config.SAMPLED_PROMPTS_PATH}...")
    if not config.SAMPLED_PROMPTS_PATH.exists():
        print(f"FEHLER: {config.SAMPLED_PROMPTS_PATH} nicht gefunden.")
        print("Bitte zuerst AP2 ausfuehren.")
        sys.exit(1)

    df = pd.read_csv(config.SAMPLED_PROMPTS_PATH)

    # Nur Studien-Prompts (keine Kalibrierung)
    study_df = df[df["block"] != "calibration"].copy()
    print(f"       {len(study_df)} Studien-Prompts geladen.")

    # Vorhersagen berechnen
    print("\n[3/4] Berechne Baseline-Vorhersagen...")
    predictions = []
    for _, row in study_df.iterrows():
        text = row["prompt_text"]
        lang = row.get("language", "en")
        nlp = nlp_models.get(lang, nlp_models["en"])

        pred, rules = predict_retrieval(text, nlp)
        predictions.append({
            "prompt_id": row["prompt_id"],
            "prompt_text": text,
            "baseline_prediction": pred,
            "triggered_rules": rules,
        })

    result_df = pd.DataFrame(predictions)

    # Statistiken
    n_retrieval = result_df["baseline_prediction"].sum()
    n_no_retrieval = len(result_df) - n_retrieval
    print(f"\n       Ergebnis: {n_retrieval} Retrieval=YES, {n_no_retrieval} Retrieval=NO")

    # Speichern
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    result_df.to_csv(config.BASELINE_PREDICTIONS_PATH, index=False)
    print(f"       Gespeichert: {config.BASELINE_PREDICTIONS_PATH}")

    # Sanity Check
    run_sanity_check(nlp_models["en"])

    print("\nFertig.")


if __name__ == "__main__":
    main()
