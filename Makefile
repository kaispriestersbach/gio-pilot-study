.PHONY: build shell ap1 ap2-tag ap2-template ap2-auto-sample ap2-validate ap2-export ap3 ap4 ap5 ap5-simulate clean pipeline-test help

IMAGE_NAME = gio-pilot-study
RUN = docker compose run --rm gio-experiment

help: ## Zeige diese Hilfe
	@echo ""
	@echo "GIO Pilot Study — Docker-Befehle"
	@echo "================================="
	@echo ""
	@grep -E '^[a-zA-Z0-9_-]+:.*##' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*##"}; {printf "  make %-20s %s\n", $$1, $$2}'
	@echo ""
	@echo "Workflow (manuell):"
	@echo "  1. make build            (einmalig)"
	@echo "  2. make ap1              (WildChat filtern, ~10 Min)"
	@echo "  3. make ap2-tag          (Kandidaten-Listen generieren)"
	@echo "  4. make ap2-template     (CSV-Template fuer manuelle Auswahl)"
	@echo "  5. [Manuell: sampled_prompts.csv ausfuellen]"
	@echo "  6. make ap2-validate     (Auswahl pruefen)"
	@echo "  7. make ap3              (Keyword-Baseline)"
	@echo "  8. make ap4              (Excel-Spreadsheet)"
	@echo "  9. make ap2-export       (Dokumentation)"
	@echo "  10. [Experten annotieren]"
	@echo "  11. make ap5             (Auswertung)"
	@echo ""
	@echo "Pipeline-Test (automatisch, ohne manuelle Schritte):"
	@echo "  make pipeline-test"
	@echo ""

build: ## Docker-Image bauen (inkl. spaCy + pyarrow + DuckDB)
	docker compose build

shell: ## Interaktive Shell im Container
	$(RUN) bash

# ---------------------------------------------------------------------------
# AP1: WildChat filtern
# ---------------------------------------------------------------------------

ap1: ## AP1: WildChat filtern -> data/filtered_pool.csv
	$(RUN) python scripts/ap1_filter_wildchat.py

# ---------------------------------------------------------------------------
# AP2: Stratifiziertes Sampling
# ---------------------------------------------------------------------------

ap2-tag: ## AP2: Pre-Tagging + Kandidaten-Listen generieren
	$(RUN) python scripts/ap2_stratified_sampling.py tag

ap2-template: ## AP2: Leeres CSV-Template generieren
	$(RUN) python scripts/ap2_stratified_sampling.py template

ap2-auto-sample: ## AP2: Automatisches Sampling (Pipeline-Test)
	$(RUN) python scripts/ap2_auto_sample.py

ap2-validate: ## AP2: Manuelle Auswahl validieren
	$(RUN) python scripts/ap2_stratified_sampling.py validate

ap2-export: ## AP2: Dokumentation exportieren
	$(RUN) python scripts/ap2_stratified_sampling.py export

# ---------------------------------------------------------------------------
# AP3–AP5: Baseline, Annotation, Auswertung
# ---------------------------------------------------------------------------

ap3: ## AP3: Keyword-Baseline berechnen
	$(RUN) python scripts/ap3_keyword_baseline.py

ap4: ## AP4: Annotations-Spreadsheet erstellen
	$(RUN) python scripts/ap4_create_annotation.py

ap5-simulate: ## AP5: Simulierte Annotationen eintragen (Pipeline-Test)
	$(RUN) python scripts/ap5_simulate_annotations.py

ap5: ## AP5: Auswertung nach Annotation
	$(RUN) python scripts/ap5_evaluate.py

# ---------------------------------------------------------------------------
# Pipeline-Test (vollautomatisch)
# ---------------------------------------------------------------------------

pipeline-test: build ap1 ap2-tag ap2-auto-sample ap2-validate ap3 ap4 ap2-export ap5-simulate ap5 ## Vollstaendiger Pipeline-Test (automatisch)
	@echo ""
	@echo "================================================"
	@echo "Pipeline-Test abgeschlossen!"
	@echo "================================================"
	@echo "Ergebnisse:"
	@echo "  data/filtered_pool.csv          (AP1)"
	@echo "  data/sampled_prompts.csv        (AP2)"
	@echo "  data/baseline_predictions.csv   (AP3)"
	@echo "  output/annotation_spreadsheet.xlsx (AP4)"
	@echo "  data/evaluation_results.csv     (AP5)"
	@echo "  docs/sampling_documentation.md  (AP2)"
	@echo ""

# ---------------------------------------------------------------------------
# Aufraeumen
# ---------------------------------------------------------------------------

clean: ## Generierte Daten loeschen (VORSICHT!)
	@echo "Dies loescht alle generierten Daten. Ctrl+C zum Abbrechen."
	@sleep 3
	rm -f data/filtered_pool.csv
	rm -f data/sampled_prompts.csv
	rm -f data/sampled_prompts_template.csv
	rm -f data/baseline_predictions.csv
	rm -f data/evaluation_results.csv
	rm -f data/disagreements.csv
	rm -rf data/candidates/
	rm -f output/annotation_spreadsheet.xlsx
	rm -f docs/sampling_documentation.md
	@echo "Bereinigt."
