# GIO Pilot Study -- Experiment Code

Replication code and materials for the pilot annotation study of the
**Generative Intent Operationalization (GIO)** framework, as described in:

> Spriestersbach, K. & Vollmer, S. (2025). *From Search Intent to Retrieval
> Demand: A Pre-Generation Framework for Generative Engine Optimization (GEO) —
> Proposing the Generative Intent Operationalization (GIO).*
> RPTU Kaiserslautern-Landau.

The pilot study tests whether the eight GIO modes and the four Grounding
Necessity (GN) variables can be reliably annotated by human raters on
real-world LLM prompts drawn from the WildChat-1M dataset.

---

## Overview

| Work Package | Script | Description |
|---|---|---|
| **AP1** | `ap1_filter_wildchat.py` | Download and filter WildChat-1M (EN/DE, 5-150 words, no code) |
| **AP2** | `ap2_stratified_sampling.py` | Stratified sampling: pre-tag, generate candidate lists, validate |
| **AP3** | `ap3_keyword_baseline.py` | Keyword + NER baseline for retrieval prediction |
| **AP4** | `ap4_create_annotation.py` | Generate Excel annotation spreadsheet with dropdowns |
| **AP5** | `ap5_evaluate.py` | Compute Cohen's kappa, Bootstrap CI, F1, disagreement analysis |

### Study Design

- **50 study prompts** + **5 calibration prompts** drawn from WildChat-1M
- **2 expert raters** annotate independently
- **Stratified sample**: 18 Low GN, 18 High GN, 14 Edge Cases
  (5 Parametric Trap, 5 Implicit Demand, 4 Creative-Volatile)
- **Annotation dimensions**: GIO mode, I_gap, T_decay, E_spec, V_volatility,
  GN level, retrieval judgment, confidence
- **Known gap**: Mode 3.1 (Transactional) is systematically absent from
  WildChat — an exhaustive search of 230k prompts yielded only 1 genuine
  transactional prompt (see [Sampling Documentation](docs/sampling_documentation.md))

---

## Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) (with Docker Compose)
- A [HuggingFace](https://huggingface.co/) account with an access token
  (the WildChat-1M dataset requires authentication)

### 1. Build the Docker image

```bash
make build
```

### 2. Set your HuggingFace token

```bash
export HF_TOKEN=hf_your_token_here
```

### 3. Run the full pipeline

```bash
# AP1: Filter WildChat-1M (~10 min, downloads ~3 GB)
make ap1

# AP2: Generate candidate lists for manual sampling
make ap2-tag
make ap2-template

# --- Manual step: select 55 prompts into data/sampled_prompts.csv ---

# AP2: Validate selection
make ap2-validate

# AP3: Compute keyword baseline
make ap3

# AP4: Create annotation spreadsheet
make ap4

# AP2: Export sampling documentation
make ap2-export

# --- Manual step: expert raters annotate in Excel ---

# AP5: Evaluate inter-rater agreement
make ap5
```

### Pipeline Test (automated, no manual steps)

To run the entire pipeline with automatically generated samples and
simulated annotations (for testing/verification):

```bash
make build
export HF_TOKEN=hf_your_token_here
make ap1
make ap2-tag
make ap2-auto-sample
make ap3
make ap4
make ap5-simulate
make ap5
```

---

## Project Structure

```
Experiment/
|-- config.py                  # Central configuration (GIO definitions, paths, keywords)
|-- Dockerfile                 # Python 3.11 + spaCy + DuckDB + pyarrow
|-- docker-compose.yml         # Container orchestration with volume mounts
|-- Makefile                   # All make targets (run `make help`)
|-- requirements.txt           # Python dependencies
|-- README.md                  # This file
|-- LICENSE                    # MIT License
|-- CITATION.cff               # Machine-readable citation metadata
|
|-- scripts/
|   |-- ap1_filter_wildchat.py       # WildChat download + filtering
|   |-- ap2_stratified_sampling.py   # Stratified sampling helper
|   |-- ap2_auto_sample.py          # Automated sampling (pipeline test)
|   |-- ap3_keyword_baseline.py      # Keyword + NER baseline
|   |-- ap4_create_annotation.py     # Excel spreadsheet generator
|   |-- ap5_evaluate.py              # Evaluation (kappa, CI, F1)
|   |-- ap5_simulate_annotations.py  # Simulated annotations (pipeline test)
|
|-- data/                      # Study data (included in repository + Zenodo)
|   |-- sampled_prompts.csv         # 55 selected prompts (study + calibration)
|   |-- baseline_predictions.csv    # Keyword baseline retrieval predictions
|   |-- evaluation_results.csv      # Inter-rater agreement metrics
|   |-- disagreements.csv           # Rater disagreement details
|   |-- candidates/                 # Candidate lists per sampling block
|   |-- filtered_pool.csv           # ~230k filtered prompts (Zenodo only, 59 MB)
|   |-- raw/                        # AP1 shard checkpoints (not published)
|   |-- hf_cache/                   # HuggingFace download cache (not published)
|
|-- output/
|   |-- annotation_spreadsheet.xlsx  # Annotation workbook (6 sheets, dropdowns)
|
|-- docs/
|   |-- sampling_documentation.md    # Sampling methodology and decisions
```

---

## Data Availability

### Included in this repository

The following data files are included directly:

| File | Description | Size |
|---|---|---|
| `data/sampled_prompts.csv` | 55 selected prompts (50 study + 5 calibration) | 24 KB |
| `data/baseline_predictions.csv` | Keyword baseline retrieval predictions | ~10 KB |
| `data/evaluation_results.csv` | Inter-rater agreement metrics | ~1 KB |
| `data/disagreements.csv` | Detailed rater disagreement analysis | ~15 KB |
| `data/candidates/*.csv` | Candidate lists per sampling block (5 files, 100 each) | ~200 KB |
| `output/annotation_spreadsheet.xlsx` | Annotation workbook with dropdowns | 48 KB |
| `docs/sampling_documentation.md` | Sampling methodology documentation | 8 KB |

### Available on Zenodo

The full filtered prompt pool is published separately on Zenodo due to
its size:

| File | Description | Size |
|---|---|---|
| `filtered_pool.csv` | 230,289 filtered WildChat prompts (EN/DE) | 59 MB |

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.18593413.svg)](https://doi.org/10.5281/zenodo.18593413)

Download from: https://zenodo.org/records/18593414

To use the Zenodo data, download `filtered_pool.csv` and place it in the
`data/` directory. Alternatively, regenerate it with `make ap1`.

### Source dataset

This study uses the [WildChat-1M](https://huggingface.co/datasets/allenai/WildChat-1M)
dataset (Zhao et al., 2024), which contains 1 million real-world
conversations with ChatGPT collected via the Hugging Face ChatGPT
deployment.

- **License**: The dataset is released under the
  [ODC-BY](https://opendatacommons.org/licenses/by/) license
  (changed from AI2 ImpACT on 2024-06-26, retroactively applied).
- **Access**: Requires a HuggingFace account and acceptance of the
  dataset terms.
- **Download**: AP1 downloads Parquet files via `huggingface_hub`
  (CDN/Git-LFS) and filters locally. Only English and German
  conversations are retained.
- **Statistics**: Of 1M conversations, 495,363 are EN/DE. After
  filtering (word count, code removal, deduplication), 230,289 prompts
  remain (226,042 EN / 4,247 DE).

---

## GIO Framework Reference

The eight GIO modes (from the paper):

| Mode | Name | Category | GN Level |
|---|---|---|---|
| 1.1 | Fact Retrieval | ASKING | Low |
| 1.2 | Real-Time Synthesis | ASKING | High |
| 1.3 | Advisory | ASKING | High |
| 2.1 | Utility | DOING | None |
| 2.2 | Ungrounded Generation | DOING | Low |
| 2.3 | Grounded Generation | DOING | N/A |
| 3.1 | Transactional | ACTING | High |
| 3.2 | Open-Ended Investigation | ACTING | High |

The four Grounding Necessity (GN) variables:

| Variable | Description | Anchors |
|---|---|---|
| **I_gap** | Information demand density | Low: poem / Medium: explain concept / High: clinical trial data |
| **T_decay** | Temporal distance from training cutoff | Low: historical / Medium: recent / High: post-cutoff |
| **E_spec** | Entity specificity | Low: abstract / Medium: category / High: named entity |
| **V_volatility** | Answer change frequency | Low: physical constant / Medium: census / High: stock price |

---

## Evaluation Metrics

AP5 computes the following metrics:

- **Cohen's kappa (binary)**: retrieval judgment (Yes/No)
- **Cohen's kappa (nominal)**: GIO mode (8 categories)
- **Cohen's kappa (linear-weighted ordinal)**: GN level (Low/Medium/High)
- **Bootstrap 95% CI**: 1000 iterations for all kappa values
- **Baseline comparison**: F1, Precision, Recall of keyword baseline
  vs. expert consensus (agreement-only cases)
- **Disagreement analysis**: per-field and per-prompt breakdown

---

## Reproducibility

All generated data files can be reproduced from scratch:

```bash
make clean   # Remove all generated files
make build   # Rebuild Docker image
make ap1     # Re-download and filter WildChat-1M
```

The pipeline is fully deterministic (random seed = 42) except for:
- The WildChat-1M dataset itself (immutable on HuggingFace)
- The manual prompt selection step (AP2)
- The expert annotations (AP5 input)

### System Requirements

- Docker with at least 4 GB RAM allocated
- ~3 GB disk space for HuggingFace cache
- ~500 MB for filtered data
- Internet connection for initial WildChat download

---

## License

This code is released under the [MIT License](LICENSE).

The WildChat-1M dataset is subject to the
[Open Data Commons Attribution License (ODC-BY)](https://opendatacommons.org/licenses/by/).

---

## Citation

If you use this code or data, please cite both the paper and the dataset:

```bibtex
@article{spriestersbach2025gio,
  title       = {From Search Intent to Retrieval Demand: A Pre-Generation
                 Framework for Generative Engine Optimization ({GEO}) --
                 Proposing the Generative Intent Operationalization ({GIO})},
  author      = {Spriestersbach, Kai and Vollmer, Sebastian},
  year        = {2025},
  institution = {RPTU Kaiserslautern-Landau},
  note        = {Department of Computer Science}
}
```

```bibtex
@dataset{spriestersbach2025gio_data,
  title     = {WildChat-GIO: Filtered English/German Prompt Pool
               for the GIO Pilot Annotation Study},
  author    = {Spriestersbach, Kai and Vollmer, Sebastian},
  year      = {2025},
  publisher = {Zenodo},
  doi       = {10.5281/zenodo.18593413}
}
```

Please also cite the WildChat dataset:

```bibtex
@article{zhao2024wildchat,
  title   = {WildChat: 1M ChatGPT Interaction Logs in the Wild},
  author  = {Zhao, Wenting and others},
  year    = {2024}
}
```
