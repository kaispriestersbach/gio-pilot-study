"""
Zentrale Konfiguration fuer die GIO Pilot Study.
Alle Scripts importieren Konstanten aus dieser Datei.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Pfade
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
OUTPUT_DIR = BASE_DIR / "output"
DOCS_DIR = BASE_DIR / "docs"
SCRIPTS_DIR = BASE_DIR / "scripts"

FILTERED_POOL_PATH = DATA_DIR / "filtered_pool.csv"
SAMPLED_PROMPTS_PATH = DATA_DIR / "sampled_prompts.csv"
BASELINE_PREDICTIONS_PATH = DATA_DIR / "baseline_predictions.csv"
EVALUATION_RESULTS_PATH = DATA_DIR / "evaluation_results.csv"
ANNOTATION_XLSX_PATH = OUTPUT_DIR / "annotation_spreadsheet.xlsx"
SAMPLING_DOC_PATH = DOCS_DIR / "sampling_documentation.md"

# ---------------------------------------------------------------------------
# Reproduzierbarkeit
# ---------------------------------------------------------------------------
RANDOM_SEED = 42

# ---------------------------------------------------------------------------
# AP1 – Filter-Konstanten
# ---------------------------------------------------------------------------
WILDCHAT_DATASET = "allenai/WildChat-1M"
ALLOWED_LANGUAGES = {"English", "German"}
MIN_WORDS = 5
MAX_WORDS = 150

# Regex-Muster fuer Code-/Debug-Erkennung
CODE_BLOCK_MARKERS = ["```"]
STACKTRACE_PATTERNS = [
    r"Traceback \(most recent call",
    r"Error:",
    r"Exception:",
    r"at line \d+",
    r'File "',
    r"SyntaxError",
    r"TypeError",
    r"ValueError",
    r"IndexError",
    r"KeyError",
    r"AttributeError",
    r"ImportError",
    r"ModuleNotFoundError",
    r"RuntimeError",
    r"NameError",
]
CODE_LINE_INDICATORS = [
    "{", "}", ";",
    "import ", "from ", "def ", "class ",
    "function ", "var ", "const ", "let ",
    "public ", "private ", "static ",
    "return ", "if (", "for (",
    "#include", "using namespace",
]
CODE_RATIO_THRESHOLD = 0.5  # >50% Code-Zeilen -> entfernen

# ---------------------------------------------------------------------------
# AP2 – Sampling-Zielverteilung
# ---------------------------------------------------------------------------
SAMPLING_TARGETS = {
    "low_gn": 18,
    "high_gn": 18,
    "edge_parametric_trap": 5,
    "edge_implicit_demand": 5,
    "edge_creative_volatile": 4,
    "calibration": 5,
}

# Heuristische Keywords fuer Pre-Tagging
TEMPORAL_MARKERS = [
    "current", "currently", "latest", "today", "now", "recent", "recently",
    "2024", "2025", "2026",
    "aktuell", "aktuelle", "aktuellen", "neueste", "neuesten", "heute",
    "derzeit", "momentan",
]

VOLATILITY_INDICATORS = [
    "price", "prices", "cost", "costs",
    "weather", "forecast",
    "score", "scores", "result", "results",
    "poll", "polls", "survey",
    "stock", "stocks", "market",
    "election", "elections", "vote",
    "rate", "rates",
    "Preis", "Preise", "Kosten",
    "Wetter", "Vorhersage",
    "Kurs", "Kurse",
    "Umfrage", "Umfragen",
    "Ergebnis", "Ergebnisse",
    "Wahl", "Wahlen",
]

CREATIVE_KEYWORDS = [
    "write", "create", "compose", "generate", "draft", "design",
    "poem", "story", "essay", "song", "lyrics", "script",
    "slogan", "tagline", "motto",
    "schreibe", "erstelle", "verfasse", "entwerfe", "dichte",
    "Gedicht", "Geschichte", "Aufsatz", "Lied",
]

VOLATILE_TOPICS = [
    "bitcoin", "crypto", "cryptocurrency", "blockchain",
    "ai", "artificial intelligence", "chatgpt", "gpt",
    "startup", "startups",
    "climate", "climate change", "global warming",
    "inflation", "recession", "economy",
    "covid", "pandemic",
    "election", "politics", "policy",
    "war", "conflict",
    "stock market", "nasdaq", "s&p",
    "Kryptowährung", "Künstliche Intelligenz",
    "Klimawandel", "Inflation",
]

IMPLICIT_DEMAND_PATTERNS = [
    r"what should i (?:think|know|do|consider)",
    r"how should i (?:approach|handle|deal with|think about)",
    r"what do you think about",
    r"what's your (?:take|opinion|view) on",
    r"is it (?:worth|good|advisable|wise|safe) to",
    r"should i (?:buy|invest|use|try|switch|start|stop)",
    r"was (?:denkst|meinst|hältst) du",
    r"sollte ich",
    r"lohnt (?:es )?sich",
    r"wie (?:sollte|soll) ich",
]

PARAMETRIC_TRAP_INDICATORS = [
    "ceo", "president", "leader", "head", "chairman",
    "population", "inhabitants",
    "price", "cost", "worth",
    "current", "latest", "now",
    "treatment", "cure", "therapy",
    "CEO", "Präsident", "Bevölkerung", "Einwohner",
    "Behandlung", "Therapie",
]

INTERROGATIVE_STARTERS_EN = ["who ", "when ", "what ", "where ", "how much ", "how many "]
INTERROGATIVE_STARTERS_DE = ["wer ", "wann ", "was ", "wo ", "wie viel ", "wie viele "]

# ---------------------------------------------------------------------------
# AP3 – Keyword-Baseline
# ---------------------------------------------------------------------------
BASELINE_TEMPORAL_MARKERS = [
    "current", "currently", "latest", "today", "2024", "2025", "2026",
    "aktuell", "aktuelle", "aktuellen", "neueste", "neuesten",
]

BASELINE_VOLATILITY_INDICATORS = [
    "price", "prices",
    "weather",
    "score", "scores",
    "poll", "polls",
    "Preis", "Preise",
    "Wetter",
    "Kurs", "Kurse",
    "Umfrage", "Umfragen",
]

BASELINE_INTERROGATIVE_STARTERS = [
    "who ", "when ", "wer ", "wann ",
]

# ~50 allgemein bekannte Entitaeten (Parametric-Trap-sichere Fakten)
COMMON_KNOWLEDGE_ENTITIES = {
    # Gebaeude / Wahrzeichen
    "Eiffel Tower", "Statue of Liberty", "Great Wall of China",
    "Big Ben", "Colosseum", "Taj Mahal", "Pyramids of Giza",
    "Brandenburger Tor", "Brandenburg Gate",
    # Staedte / Laender
    "Paris", "London", "New York", "Tokyo", "Berlin", "Rome",
    "Washington", "Moscow", "Beijing", "Sydney",
    "France", "Germany", "Japan", "United States", "China",
    "United Kingdom", "Italy", "Russia", "Australia", "India",
    # Historische Personen
    "Shakespeare", "Einstein", "Newton", "Mozart", "Beethoven",
    "Leonardo da Vinci", "Galileo", "Darwin", "Marie Curie",
    "Napoleon", "Cleopatra", "Julius Caesar",
    # Naturwissenschaftliche Konstanten / Fakten
    "Earth", "Sun", "Moon", "Mars", "Jupiter",
    "Mount Everest", "Pacific Ocean", "Amazon River", "Nile",
    "Sahara",
    # Allgemeinwissen
    "DNA", "photosynthesis", "gravity", "atom",
    "Photosynthese", "Schwerkraft",
    # Sprachen (werden von spaCy manchmal als Entities erkannt)
    "English", "Spanish", "French", "German", "Chinese",
    "Japanese", "Italian", "Portuguese", "Russian", "Arabic",
    "Englisch", "Spanisch", "Französisch", "Deutsch",
    # Haeufige Fehlerkennungen
    "Translate", "Summary", "JSON", "CSV", "PDF", "HTML",
}

# ---------------------------------------------------------------------------
# GIO-Framework-Definitionen (aus Table 1 des Papers)
# ---------------------------------------------------------------------------
GIO_MODES = {
    "1.1": {
        "name": "Fact Retrieval",
        "category": "ASKING",
        "gn_level": "Low",
        "definition": "Verify a static fact with high consensus.",
        "examples": [
            "What is the height of the Eiffel Tower?",
            "What is the capital of France?",
        ],
        "differentiation": "Unlike 1.2, the answer is stable and does not change over time.",
    },
    "1.2": {
        "name": "Real-Time Synthesis",
        "category": "ASKING",
        "gn_level": "High",
        "definition": "Access dynamic data subject to high volatility.",
        "examples": [
            "What is the current stock price of Apple?",
            "What are the latest election results in Germany?",
        ],
        "differentiation": "Unlike 1.1, the answer changes frequently and requires live data.",
    },
    "1.3": {
        "name": "Advisory",
        "category": "ASKING",
        "gn_level": "High",
        "definition": "Seek expert perspective requiring subjective nuance and diversity of perspectives.",
        "examples": [
            "What is the best SEO strategy for banks in 2026?",
            "What does the new EU AI Act mean for startups?",
        ],
        "differentiation": "Unlike 1.1, requires multi-perspective synthesis, not a single fact.",
    },
    "2.1": {
        "name": "Utility",
        "category": "DOING",
        "gn_level": "None",
        "definition": "Transformation of existing input (translation, formatting, conversion).",
        "examples": [
            "Translate this text to Spanish.",
            "Convert this CSV to JSON format.",
        ],
        "differentiation": "Unlike 2.2, operates on provided input rather than creating new content.",
    },
    "2.2": {
        "name": "Ungrounded Generation",
        "category": "DOING",
        "gn_level": "Low",
        "definition": "Creative creation ex nihilo relying on internal creativity.",
        "examples": [
            "Write a poem about autumn.",
            "Create a short story about a robot who learns to love.",
        ],
        "differentiation": "Unlike 2.3, requires no external source material.",
    },
    "2.3": {
        "name": "Grounded Generation",
        "category": "DOING",
        "gn_level": "N/A",
        "definition": "Source-dependent creation where the user provides the source document.",
        "examples": [
            "Summarize this PDF for me.",
            "Rewrite this paragraph in simpler language.",
        ],
        "differentiation": "Unlike 2.2, depends on user-provided source material.",
    },
    "3.1": {
        "name": "Transactional",
        "category": "ACTING",
        "gn_level": "High",
        "definition": "Execute a purchase, booking, or other transactional action.",
        "examples": [
            "Book a flight from Berlin to New York for next Friday.",
            "Order a large pepperoni pizza from the nearest restaurant.",
        ],
        "differentiation": "Unlike 3.2, involves a concrete, completable transaction.",
    },
    "3.2": {
        "name": "Open-Ended Investigation",
        "category": "ACTING",
        "gn_level": "High",
        "definition": "Solve an underspecified problem requiring iterative exploration.",
        "examples": [
            "Plan a two-week trip to Japan.",
            "Help me find the best laptop for video editing under 1500 EUR.",
        ],
        "differentiation": "Unlike 3.1, the goal is underspecified and requires multi-step exploration.",
    },
}

# GN-Variablen-Definitionen (aus Table 4 des Papers)
GN_VARIABLES = {
    "I_gap": {
        "name": "Information Gap",
        "definition": "The explicit or implicit demand for data density (citations, tables, numerical evidence) in the prompt.",
        "anchors": {
            "Low": "Write a poem about the sea. (No information demand.)",
            "Medium": "Explain how photosynthesis works. (General explanation, some facts needed.)",
            "High": "What are the latest clinical trial results for mRNA cancer vaccines? (Explicit demand for current data.)",
        },
    },
    "T_decay": {
        "name": "Temporal Decay",
        "definition": "Temporal distance from the model's training cutoff to the event referenced in the prompt.",
        "anchors": {
            "Low": "Who wrote Romeo and Juliet? (Historical, no decay.)",
            "Medium": "What were the main outcomes of COP28? (Recent but not real-time.)",
            "High": "What happened in the US elections yesterday? (Post-cutoff event.)",
        },
    },
    "E_spec": {
        "name": "Entity Specificity",
        "definition": "How specific the entities in the prompt are (named individuals, organizations, products vs. general concepts).",
        "anchors": {
            "Low": "What is love? (Abstract concept, no specific entity.)",
            "Medium": "How do electric cars work? (General category.)",
            "High": "Who is the CEO of Siemens? (Specific named entity.)",
        },
    },
    "V_volatility": {
        "name": "Volatility",
        "definition": "How frequently the correct answer changes over time.",
        "anchors": {
            "Low": "What is the speed of light? (Physical constant, never changes.)",
            "Medium": "What is the population of Germany? (Changes slowly, census-level.)",
            "High": "What is the current Bitcoin price? (Changes every second.)",
        },
    },
}

# Dropdown-Werte fuer das Annotations-Spreadsheet
DROPDOWN_GIO_MODES = ["1.1", "1.2", "1.3", "2.1", "2.2", "2.3", "3.1", "3.2"]
DROPDOWN_GN_LEVELS = ["Low", "Medium", "High"]
DROPDOWN_RETRIEVAL = ["Yes", "No"]
DROPDOWN_CONFIDENCE = ["1", "2", "3", "4", "5"]
