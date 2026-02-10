"""
AP1: WildChat-Datensatz filtern.

Laedt WildChat-1M Parquet-Dateien via huggingface_hub herunter (CDN/Git-LFS,
kein Rate-Limit-Problem) und filtert shard-weise mit pyarrow.

Jeder Shard wird einzeln verarbeitet und sofort wieder freigegeben,
um den Speicherverbrauch gering zu halten.

Filter:
  - Sprache: nur English/German
  - Ersten User-Turn extrahieren
  - Wortlaenge: 5–150 Woerter
  - Code-Debugging entfernen
  - Exakte Duplikate entfernen

Output: data/filtered_pool.csv

Voraussetzung: HuggingFace-Token als Umgebungsvariable HF_TOKEN
"""

import gc
import json
import os
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from huggingface_hub import hf_hub_download, list_repo_tree
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config

# HuggingFace Dataset-Info
HF_REPO_ID = "allenai/WildChat-1M"
HF_REVISION = "refs/convert/parquet"  # Auto-converted Parquet branch
HF_PARQUET_DIR = "default/train"


# -------------------------------------------------------------------------
# Code-/Debug-Filter
# -------------------------------------------------------------------------

_STACKTRACE_RE = re.compile(
    "|".join(config.STACKTRACE_PATTERNS),
    re.IGNORECASE,
)


def contains_code_block(text):
    return "```" in text


def contains_stacktrace(text):
    return bool(_STACKTRACE_RE.search(text))


def is_code_heavy(text):
    lines = text.strip().split("\n")
    if len(lines) < 2:
        return False
    code_lines = 0
    total_nonempty = 0
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        total_nonempty += 1
        if any(indicator in stripped for indicator in config.CODE_LINE_INDICATORS):
            code_lines += 1
    if total_nonempty == 0:
        return False
    return (code_lines / total_nonempty) > config.CODE_RATIO_THRESHOLD


def is_code_debugging(text):
    return contains_code_block(text) or contains_stacktrace(text) or is_code_heavy(text)


def count_words(text):
    return len(text.split())


# -------------------------------------------------------------------------
# Erster User-Turn extrahieren
# -------------------------------------------------------------------------

def extract_first_user_turn(conversation):
    """Extrahiere den ersten User-Turn.

    conversation kann verschiedene Typen haben je nach Ladeweg:
      - JSON-String
      - Python-Liste von Dicts
      - NumPy-Array (pyarrow-Output)
      - Liste von Struct-artigen Objekten
    """
    if isinstance(conversation, str):
        try:
            conversation = json.loads(conversation)
        except (json.JSONDecodeError, TypeError):
            return None

    if isinstance(conversation, np.ndarray):
        conversation = conversation.tolist()

    try:
        iter(conversation)
    except TypeError:
        return None

    if len(conversation) == 0:
        return None

    for turn in conversation:
        if not isinstance(turn, dict):
            try:
                turn = dict(turn)
            except (TypeError, ValueError):
                continue
        if turn.get("role") == "user":
            content = turn.get("content", "")
            if isinstance(content, str):
                content = content.strip()
                if content:
                    return content
    return None


# -------------------------------------------------------------------------
# Parquet-Dateien via huggingface_hub herunterladen
# -------------------------------------------------------------------------

def get_parquet_files(hf_token):
    """Liste alle Parquet-Dateien im Dataset-Repo auf."""
    print("       Suche Parquet-Dateien im Repository...")
    files = []
    for entry in list_repo_tree(
        HF_REPO_ID,
        path_in_repo=HF_PARQUET_DIR,
        revision=HF_REVISION,
        repo_type="dataset",
        token=hf_token or None,
    ):
        if hasattr(entry, "rfilename") and entry.rfilename.endswith(".parquet"):
            files.append(entry.rfilename)
    files.sort()
    return files


def download_parquet_shard(parquet_path, hf_token, cache_dir):
    """Lade eine einzelne Parquet-Datei via huggingface_hub (CDN/Git-LFS)."""
    local_path = hf_hub_download(
        repo_id=HF_REPO_ID,
        filename=parquet_path,
        revision=HF_REVISION,
        repo_type="dataset",
        token=hf_token or None,
        cache_dir=str(cache_dir),
    )
    return local_path


def load_and_filter_shard_pyarrow(local_parquet_path):
    """Lade eine lokale Parquet-Datei und filtere auf EN/DE mit pyarrow.

    Liest nur die benoetigten Spalten und filtert sofort nach Sprache.
    Gibt ein pandas DataFrame zurueck.
    """
    # Nur die Spalten lesen, die wir brauchen
    table = pq.read_table(
        local_parquet_path,
        columns=["conversation_hash", "conversation", "language"],
    )

    # Sprache filtern mit pyarrow compute
    import pyarrow.compute as pc
    mask = pc.or_(
        pc.equal(table.column("language"), "English"),
        pc.equal(table.column("language"), "German"),
    )
    filtered_table = table.filter(mask)

    # Zu pandas konvertieren
    df = filtered_table.to_pandas()

    # Speicher freigeben
    del table, filtered_table, mask
    gc.collect()

    return df


def process_shard(df_shard, stats, seen_texts, results):
    """Verarbeite einen einzelnen Shard: Extrahiere Prompts und filtere.

    Modifiziert stats, seen_texts und results in-place.
    """
    for _, row in df_shard.iterrows():
        conv = row["conversation"]
        conv_id = row["conversation_hash"]
        lang_label = row["language"]
        lang = "en" if lang_label == "English" else "de"

        prompt = extract_first_user_turn(conv)
        if prompt is None:
            stats["no_user_turn"] += 1
            continue

        wc = count_words(prompt)
        if wc < config.MIN_WORDS:
            stats["too_short"] += 1
            continue
        if wc > config.MAX_WORDS:
            stats["too_long"] += 1
            continue

        if is_code_debugging(prompt):
            stats["code_debugging"] += 1
            continue

        if prompt in seen_texts:
            stats["duplicates"] += 1
            continue
        seen_texts.add(prompt)

        results.append({
            "conversation_id": conv_id,
            "prompt_text": prompt,
            "language": lang,
            "word_count": wc,
        })
        stats["passed"] += 1


# -------------------------------------------------------------------------
# Hauptprogramm
# -------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("AP1: WildChat-Datensatz filtern (huggingface_hub + pyarrow)")
    print("=" * 60)

    hf_token = os.environ.get("HF_TOKEN", "")

    if hf_token:
        print(f"\n       HF_TOKEN vorhanden.")
    else:
        print("\n       WARNUNG: Kein HF_TOKEN gesetzt!")
        print("       export HF_TOKEN=hf_...")
        print("       Ohne Token koennten Zugriffsprobleme auftreten.")

    # Verzeichnisse
    checkpoint_dir = config.DATA_DIR / "raw"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    hf_cache_dir = config.DATA_DIR / "hf_cache"
    hf_cache_dir.mkdir(parents=True, exist_ok=True)

    # Parquet-Dateien auflisten
    print(f"\n[1/3] Lade und filtere Parquet-Dateien shard-weise...")
    print(f"       Methode: huggingface_hub (CDN/Git-LFS, kein API-Rate-Limit)")
    print(f"       Sprachfilter: nur English/German (pyarrow)\n")

    parquet_files = get_parquet_files(hf_token)
    total_files = len(parquet_files)
    print(f"       {total_files} Parquet-Dateien gefunden.\n")

    # Statistiken und Ergebnisse
    stats = {
        "total_en_de": 0,
        "no_user_turn": 0,
        "too_short": 0,
        "too_long": 0,
        "code_debugging": 0,
        "duplicates": 0,
        "passed": 0,
    }
    results = []
    seen_texts = set()

    for i, parquet_path in enumerate(parquet_files):
        filename = parquet_path.split("/")[-1]
        checkpoint_path = checkpoint_dir / f"shard_{i:04d}_filtered.csv"

        # Falls Checkpoint existiert (bereits vollstaendig gefiltert)
        if checkpoint_path.exists():
            print(f"  [{i + 1:2d}/{total_files}] {filename} — Checkpoint vorhanden, lade gefilterte Prompts...")
            df_checkpoint = pd.read_csv(checkpoint_path)
            # Duplikate gegen bisherige Ergebnisse pruefen
            new_count = 0
            for _, row in df_checkpoint.iterrows():
                if row["prompt_text"] not in seen_texts:
                    seen_texts.add(row["prompt_text"])
                    results.append(row.to_dict())
                    new_count += 1
                else:
                    stats["duplicates"] += 1
            print(f"         {len(df_checkpoint)} Prompts geladen, {new_count} neu")
            continue

        print(f"  [{i + 1:2d}/{total_files}] {filename} — ", end="", flush=True)

        # Schritt 1: Herunterladen via huggingface_hub (CDN)
        local_path = download_parquet_shard(parquet_path, hf_token, hf_cache_dir)
        print(f"heruntergeladen, ", end="", flush=True)

        # Schritt 2: Lokal mit pyarrow filtern (EN/DE)
        df_shard = load_and_filter_shard_pyarrow(local_path)
        en_de_count = len(df_shard)
        stats["total_en_de"] += en_de_count
        print(f"{en_de_count:,} EN/DE, ", end="", flush=True)

        # Schritt 3: Prompts extrahieren und filtern
        shard_results = []
        shard_stats = {
            "no_user_turn": 0,
            "too_short": 0,
            "too_long": 0,
            "code_debugging": 0,
            "duplicates": 0,
            "passed": 0,
        }

        for _, row in df_shard.iterrows():
            conv = row["conversation"]
            conv_id = row["conversation_hash"]
            lang_label = row["language"]
            lang = "en" if lang_label == "English" else "de"

            prompt = extract_first_user_turn(conv)
            if prompt is None:
                shard_stats["no_user_turn"] += 1
                continue

            wc = count_words(prompt)
            if wc < config.MIN_WORDS:
                shard_stats["too_short"] += 1
                continue
            if wc > config.MAX_WORDS:
                shard_stats["too_long"] += 1
                continue

            if is_code_debugging(prompt):
                shard_stats["code_debugging"] += 1
                continue

            if prompt in seen_texts:
                shard_stats["duplicates"] += 1
                continue
            seen_texts.add(prompt)

            entry = {
                "conversation_id": conv_id,
                "prompt_text": prompt,
                "language": lang,
                "word_count": wc,
            }
            shard_results.append(entry)
            results.append(entry)
            shard_stats["passed"] += 1

        # Shard-Stats zu Gesamt-Stats addieren
        for key in shard_stats:
            stats[key] = stats.get(key, 0) + shard_stats[key]

        print(f"{shard_stats['passed']:,} Prompts behalten")

        # Checkpoint der gefilterten Prompts speichern (viel kleiner als Roh-Daten)
        if shard_results:
            pd.DataFrame(shard_results).to_csv(checkpoint_path, index=False)

        # Speicher freigeben
        del df_shard, shard_results
        gc.collect()

    # Statistiken
    print("\n" + "=" * 60)
    print("Filterstatistiken:")
    print("=" * 60)
    print(f"  Geladen (EN/DE):         {stats['total_en_de']:>10,}")
    print(f"  Kein User-Turn:          {stats['no_user_turn']:>10,}")
    print(f"  Zu kurz (<{config.MIN_WORDS} Woerter):    {stats['too_short']:>10,}")
    print(f"  Zu lang (>{config.MAX_WORDS} Woerter):   {stats['too_long']:>10,}")
    print(f"  Code/Debugging:          {stats['code_debugging']:>10,}")
    print(f"  Duplikate:               {stats['duplicates']:>10,}")
    print(f"  ----------------------------------------")
    print(f"  Behalten (bereinigt):    {stats['passed']:>10,}")

    # Speichern
    print(f"\n[2/3] Speichere nach {config.FILTERED_POOL_PATH}...")
    df = pd.DataFrame(results)
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(config.FILTERED_POOL_PATH, index=False)
    print(f"       {len(df):,} Prompts gespeichert.")

    # Stichprobe
    print("\n[3/3] Stichprobe (10 zufaellige Prompts):")
    if len(df) > 10:
        sample = df.sample(10, random_state=config.RANDOM_SEED)
    else:
        sample = df
    for _, row in sample.iterrows():
        text = row["prompt_text"][:80] + ("..." if len(row["prompt_text"]) > 80 else "")
        print(f"  [{row['language']}] ({row['word_count']}w) {text}")

    print("\nFertig.")
    print(f"\nHinweis: Checkpoints liegen in {checkpoint_dir}/")
    print("Bei erneutem Lauf werden bereits geladene Shards aus dem Checkpoint gelesen.")


if __name__ == "__main__":
    main()
