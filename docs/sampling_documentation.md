# Sampling-Dokumentation — GIO Pilot Study

## Filterkriterien (AP1)

- Datensatz: allenai/WildChat-1M
- Nur erster User-Turn pro Konversation
- Wortlaenge: 5–150 Woerter
- Sprachen: English, German
- Code-Debugging-Prompts entfernt
- Exakte Duplikate entfernt

## Sampling-Entscheidungen (AP2)

- Studien-Prompts: 50
- Kalibrierungs-Prompts: 5

### Block-Verteilung

- edge: 14
- high_gn: 18
- low_gn: 18

### GIO-Mode-Verteilung

- Mode 1.1 (Fact Retrieval): 3
- Mode 1.2 (Real-Time Synthesis): 9
- Mode 1.3 (Advisory): 11
- Mode 2.1 (Utility): 5
- Mode 2.2 (Ungrounded Generation): 14
- Mode 2.3 (Grounded Generation): 3
- Mode 3.1 (Transactional): 2
- Mode 3.2 (Open-Ended Investigation): 3

### Quellen

- WildChat: 55

## Bekannte Luecken

### Mode 3.1 (Transactional) — Systematische Corpus-Luecke

Mode 3.1 (Transactional) ist in WildChat systematisch unterrepraesentiert.
Dies ist kein Sampling-Artefakt, sondern ein strukturelles Corpus-Merkmal:

**Suchstrategie:**
- Ausgangsbasis: 230.289 gefilterte WildChat-Prompts (EN/DE)
- Mehrfache Muster-basierte Suche mit Transaktions-Keywords
  (book, reserve, purchase, order, schedule, subscribe, etc.)
- Scoring-basiertes Ranking (Keyword-Treffer + Aktions-Intent-Marker)
- 100 Top-Kandidaten manuell gegen die 4 Review-Kriterien geprueft

**Ergebnis:**

| Stufe                        | Anzahl  |
|------------------------------|---------|
| Gefilterter WildChat-Pool    | 230.289 |
| Transaktions-Keyword-Treffer | ~7.400  |
| Scored & ranked Kandidaten   | 100     |
| Review-Ergebnis: ACCEPT      | 1 (1%) |
| Im finalen Sample            | 2       |

**Umklassifizierung der 99 abgelehnten Kandidaten:**
- 38% Utility/Email-Entwurf (Mode 2.1) — "draft an email to book..."
- 32% Advisory/Empfehlung (Mode 1.3) — "should I book..."
- 20% Faktisch/Technisch (Mode 1.1/1.2) — "what is the booking policy..."
- 10% Sonstige (Mode 2.2, 3.2)

**Ursache:** Nutzer wissen, dass aktuelle LLMs keine realen Transaktionen
ausfuehren koennen (Hotelbuchungen, Kaeufe, API-Aufrufe). Deshalb
formulieren sie solche Anfragen nicht. Mode 3.1 repraesentiert eine
Affordance-Luecke zwischen dem GIO-Framework (das agentic capabilities
theoretisch abdeckt) und dem tatsaechlichen Nutzungsverhalten bei
nicht-agentischen Chatbots.

**Konsequenz fuer die Studie:** Mode 3.1 ist mit nur 2 Prompts im
finalen Sample unter dem Mindest-Schwellenwert von 3 vertreten. Inter-
Rater-Uebereinstimmungswerte fuer diesen Mode sind daher nicht
aussagekraeftig und werden in der Auswertung (AP5) separat ausgewiesen.

**Empfehlung fuer kuenftige Studien:** Korpora von agentischen LLM-
Systemen (mit Tool-Use, Function Calling oder Browser-Nutzung) werden
voraussichtlich erheblich mehr Mode-3.1-Prompts enthalten.

### Weitere bekannte Luecken

- Der Code-Filter ist heuristisch und koennte einige Prompts mit Code-Referenzen faelschlicherweise entfernen.
- Die Spracherkennung (fasttext) hat bei sehr kurzen Prompts niedrigere Genauigkeit.
- creative_volatile: Nur 3 ACCEPTs + 1 EDGE_CASE fuer 4 Slots — minimaler Spielraum.

## Prompt-Details

| ID | Block | Subtyp | Mode | Quelle | Begruendung |
|---|---|---|---|---|---|
| P01 | low_gn | nan | 1.1 | WildChat | Review-accepted (2.2) from candidate_low_gn.csv. [Reassigned to 1.1 for coverage.] |
| P02 | low_gn | nan | 2.3 | WildChat | Review-accepted (2.1) from candidate_low_gn.csv. [Reassigned to 2.3 for coverage.] |
| P03 | low_gn | nan | 1.1 | WildChat | Review-accepted (1.1) from candidate_low_gn.csv. |
| P04 | low_gn | nan | 2.2 | WildChat | Review-accepted (2.2) from candidate_low_gn.csv. |
| P05 | low_gn | nan | 2.2 | WildChat | Review-accepted (2.2) from candidate_low_gn.csv. |
| P06 | low_gn | nan | 2.2 | WildChat | Review-accepted (2.2) from candidate_low_gn.csv. |
| P07 | low_gn | nan | 2.2 | WildChat | Review-accepted (2.2) from candidate_low_gn.csv. |
| P08 | low_gn | nan | 2.1 | WildChat | Review-accepted (2.1) from candidate_low_gn.csv. |
| P09 | low_gn | nan | 2.2 | WildChat | Review-accepted (2.2) from candidate_low_gn.csv. |
| P10 | low_gn | nan | 2.1 | WildChat | Review-accepted (2.1) from candidate_low_gn.csv. |
| P11 | low_gn | nan | 2.2 | WildChat | Review-accepted (2.2) from candidate_low_gn.csv. |
| P12 | low_gn | nan | 2.2 | WildChat | Review-accepted (2.2) from candidate_low_gn.csv. |
| P13 | low_gn | nan | 2.2 | WildChat | Review-accepted (2.2) from candidate_low_gn.csv. |
| P14 | low_gn | nan | 2.1 | WildChat | Review-accepted (2.1) from candidate_low_gn.csv. |
| P15 | low_gn | nan | 2.1 | WildChat | Review-accepted (2.1) from candidate_low_gn.csv. |
| P16 | low_gn | nan | 1.1 | WildChat | Review-accepted (1.1) from candidate_low_gn.csv. |
| P17 | low_gn | nan | 2.2 | WildChat | Review-accepted (2.2) from candidate_low_gn.csv. |
| P18 | low_gn | nan | 2.2 | WildChat | Review-accepted (2.2) from candidate_low_gn.csv. |
| P19 | high_gn | nan | 1.3 | WildChat | Review-accepted (1.3) from candidate_high_gn.csv. |
| P20 | high_gn | nan | 2.1 | WildChat | Review-accepted (2.1) from candidate_high_gn.csv. |
| P21 | high_gn | nan | 2.3 | WildChat | Review-accepted (2.3) from candidate_high_gn.csv. |
| P22 | high_gn | nan | 1.2 | WildChat | Review-accepted (1.2) from candidate_high_gn.csv. |
| P23 | high_gn | nan | 3.2 | WildChat | Review-accepted (3.2) from candidate_high_gn.csv. |
| P24 | high_gn | nan | 3.1 | WildChat | Review-accepted (3.1) from candidate_high_gn.csv. |
| P25 | high_gn | nan | 1.2 | WildChat | Review-accepted (1.2) from candidate_high_gn.csv. |
| P26 | high_gn | nan | 1.3 | WildChat | Review-accepted (1.3) from candidate_high_gn.csv. |
| P27 | high_gn | nan | 1.3 | WildChat | Review-accepted (1.3) from candidate_high_gn.csv. |
| P28 | high_gn | nan | 1.3 | WildChat | Review-accepted (1.3) from candidate_high_gn.csv. |
| P29 | high_gn | nan | 3.2 | WildChat | Review-accepted (3.2) from candidate_high_gn.csv. |
| P30 | high_gn | nan | 1.2 | WildChat | Review-accepted (1.2) from candidate_high_gn.csv. |
| P31 | high_gn | nan | 1.3 | WildChat | Review-accepted (1.3) from candidate_high_gn.csv. |
| P32 | high_gn | nan | 1.3 | WildChat | Review-accepted (1.3) from candidate_high_gn.csv. |
| P33 | high_gn | nan | 1.2 | WildChat | Review-accepted (1.2) from candidate_high_gn.csv. |
| P34 | high_gn | nan | 3.1 | WildChat | Transactional (3.1) from dedicated WildChat search. Replaces overrepresented 1.3 in high_gn. |
| P35 | high_gn | nan | 3.2 | WildChat | Review-accepted (3.2) from candidate_high_gn.csv. |
| P36 | high_gn | nan | 2.3 | WildChat | Review-accepted (2.3) from candidate_high_gn.csv. |
| P37 | edge | parametric_trap | 1.2 | WildChat | Review-accepted (1.1/1.2) from candidate_parametric_trap.csv. |
| P38 | edge | parametric_trap | 1.2 | WildChat | Review-accepted (1.1/1.2) from candidate_parametric_trap.csv. |
| P39 | edge | parametric_trap | 1.2 | WildChat | Review-accepted (1.1/1.2) from candidate_parametric_trap.csv. |
| P40 | edge | parametric_trap | 1.2 | WildChat | Review-accepted (1.1/1.2) from candidate_parametric_trap.csv. |
| P41 | edge | parametric_trap | 1.2 | WildChat | Review-accepted (1.1/1.2) from candidate_parametric_trap.csv. |
| P42 | edge | implicit_demand | 1.3 | WildChat | Review-accepted (1.3) from candidate_implicit_demand.csv. |
| P43 | edge | implicit_demand | 1.3 | WildChat | Review-accepted (1.3) from candidate_implicit_demand.csv. |
| P44 | edge | implicit_demand | 1.3 | WildChat | Review-accepted (1.3) from candidate_implicit_demand.csv. |
| P45 | edge | implicit_demand | 1.3 | WildChat | Review-accepted (1.3) from candidate_implicit_demand.csv. |
| P46 | edge | implicit_demand | 1.3 | WildChat | Review-accepted (1.3) from candidate_implicit_demand.csv. |
| P47 | edge | creative_volatile | 2.2 | WildChat | Review-accepted (2.2) from candidate_creative_volatile.csv. |
| P48 | edge | creative_volatile | 2.2 | WildChat | Review-accepted (2.2) from candidate_creative_volatile.csv. |
| P49 | edge | creative_volatile | 2.2 | WildChat | Review-accepted (2.2) from candidate_creative_volatile.csv. |
| P50 | edge | creative_volatile | 2.2 | WildChat | Review-accepted (2.2) from candidate_creative_volatile.csv. |
| C01 | calibration | nan | 2.2 | WildChat | Calibration prompt (review-accepted, 2.2). |
| C02 | calibration | nan | 2.2 | WildChat | Calibration prompt (review-accepted, 2.2). |
| C03 | calibration | nan | 2.1 | WildChat | Calibration prompt (review-accepted, 2.1). |
| C04 | calibration | nan | 2.2 | WildChat | Calibration prompt (review-accepted, 2.2). |
| C05 | calibration | nan | 2.2 | WildChat | Calibration prompt (review-accepted, 2.2). |