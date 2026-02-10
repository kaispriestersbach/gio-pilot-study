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
- Mode 1.2 (Real-Time Synthesis): 20
- Mode 1.3 (Advisory): 8
- Mode 2.1 (Utility): 4
- Mode 2.2 (Ungrounded Generation): 9
- Mode 2.3 (Grounded Generation): 3
- Mode 3.1 (Transactional): 0
- Mode 3.2 (Open-Ended Investigation): 3

### Quellen

- WildChat: 55

## Bekannte Luecken

- Mode 3.1 (Transactional) ist in WildChat unterrepraesentiert.
- Der Code-Filter ist heuristisch und koennte einige Prompts mit Code-Referenzen faelschlicherweise entfernen.
- Die Spracherkennung (fasttext) hat bei sehr kurzen Prompts niedrigere Genauigkeit.

## Prompt-Details

| ID | Block | Subtyp | Mode | Quelle | Begruendung |
|---|---|---|---|---|---|
| P01 | low_gn | nan | 1.1 | WildChat | Auto-selected from candidate_low_gn.csv candidates. [Reassigned to 1.1 for coverage.] |
| P02 | low_gn | nan | 1.1 | WildChat | Auto-selected from candidate_low_gn.csv candidates. [Reassigned to 1.1 for coverage.] |
| P03 | low_gn | nan | 2.1 | WildChat | Auto-selected from candidate_low_gn.csv candidates. |
| P04 | low_gn | nan | 2.3 | WildChat | Auto-selected from candidate_low_gn.csv candidates. [Reassigned to 2.3 for coverage.] |
| P05 | low_gn | nan | 2.3 | WildChat | Auto-selected from candidate_low_gn.csv candidates. [Reassigned to 2.3 for coverage.] |
| P06 | low_gn | nan | 2.1 | WildChat | Auto-selected from candidate_low_gn.csv candidates. |
| P07 | low_gn | nan | 2.3 | WildChat | Auto-selected from candidate_low_gn.csv candidates. [Reassigned to 2.3 for coverage.] |
| P08 | low_gn | nan | 3.2 | WildChat | Auto-selected from candidate_low_gn.csv candidates. [Reassigned to 3.2 for coverage.] |
| P09 | low_gn | nan | 3.2 | WildChat | Auto-selected from candidate_low_gn.csv candidates. [Reassigned to 3.2 for coverage.] |
| P10 | low_gn | nan | 3.2 | WildChat | Auto-selected from candidate_low_gn.csv candidates. [Reassigned to 3.2 for coverage.] |
| P11 | low_gn | nan | 2.2 | WildChat | Auto-selected from candidate_low_gn.csv candidates. |
| P12 | low_gn | nan | 2.2 | WildChat | Auto-selected from candidate_low_gn.csv candidates. |
| P13 | low_gn | nan | 1.1 | WildChat | Auto-selected from candidate_low_gn.csv candidates. |
| P14 | low_gn | nan | 2.2 | WildChat | Auto-selected from candidate_low_gn.csv candidates. |
| P15 | low_gn | nan | 2.2 | WildChat | Auto-selected from candidate_low_gn.csv candidates. |
| P16 | low_gn | nan | 2.2 | WildChat | Auto-selected from candidate_low_gn.csv candidates. |
| P17 | low_gn | nan | 2.1 | WildChat | Auto-selected from candidate_low_gn.csv candidates. |
| P18 | low_gn | nan | 2.1 | WildChat | Auto-selected from candidate_low_gn.csv candidates. |
| P19 | high_gn | nan | 1.2 | WildChat | Auto-selected from candidate_high_gn.csv candidates. |
| P20 | high_gn | nan | 1.3 | WildChat | Auto-selected from candidate_high_gn.csv candidates. |
| P21 | high_gn | nan | 1.3 | WildChat | Auto-selected from candidate_high_gn.csv candidates. |
| P22 | high_gn | nan | 1.3 | WildChat | Auto-selected from candidate_high_gn.csv candidates. |
| P23 | high_gn | nan | 1.2 | WildChat | Auto-selected from candidate_high_gn.csv candidates. |
| P24 | high_gn | nan | 1.2 | WildChat | Auto-selected from candidate_high_gn.csv candidates. |
| P25 | high_gn | nan | 1.2 | WildChat | Auto-selected from candidate_high_gn.csv candidates. |
| P26 | high_gn | nan | 1.2 | WildChat | Auto-selected from candidate_high_gn.csv candidates. |
| P27 | high_gn | nan | 1.2 | WildChat | Auto-selected from candidate_high_gn.csv candidates. |
| P28 | high_gn | nan | 1.2 | WildChat | Auto-selected from candidate_high_gn.csv candidates. |
| P29 | high_gn | nan | 1.2 | WildChat | Auto-selected from candidate_high_gn.csv candidates. |
| P30 | high_gn | nan | 1.2 | WildChat | Auto-selected from candidate_high_gn.csv candidates. |
| P31 | high_gn | nan | 1.2 | WildChat | Auto-selected from candidate_high_gn.csv candidates. |
| P32 | high_gn | nan | 1.2 | WildChat | Auto-selected from candidate_high_gn.csv candidates. |
| P33 | high_gn | nan | 1.2 | WildChat | Auto-selected from candidate_high_gn.csv candidates. |
| P34 | high_gn | nan | 1.2 | WildChat | Auto-selected from candidate_high_gn.csv candidates. |
| P35 | high_gn | nan | 1.2 | WildChat | Auto-selected from candidate_high_gn.csv candidates. |
| P36 | high_gn | nan | 1.2 | WildChat | Auto-selected from candidate_high_gn.csv candidates. |
| P37 | edge | parametric_trap | 1.2 | WildChat | Auto-selected from candidate_parametric_trap.csv candidates. |
| P38 | edge | parametric_trap | 1.2 | WildChat | Auto-selected from candidate_parametric_trap.csv candidates. |
| P39 | edge | parametric_trap | 1.2 | WildChat | Auto-selected from candidate_parametric_trap.csv candidates. |
| P40 | edge | parametric_trap | 1.2 | WildChat | Auto-selected from candidate_parametric_trap.csv candidates. |
| P41 | edge | parametric_trap | 1.2 | WildChat | Auto-selected from candidate_parametric_trap.csv candidates. |
| P42 | edge | implicit_demand | 1.3 | WildChat | Auto-selected from candidate_implicit_demand.csv candidates. |
| P43 | edge | implicit_demand | 1.3 | WildChat | Auto-selected from candidate_implicit_demand.csv candidates. |
| P44 | edge | implicit_demand | 1.3 | WildChat | Auto-selected from candidate_implicit_demand.csv candidates. |
| P45 | edge | implicit_demand | 1.3 | WildChat | Auto-selected from candidate_implicit_demand.csv candidates. |
| P46 | edge | implicit_demand | 1.3 | WildChat | Auto-selected from candidate_implicit_demand.csv candidates. |
| P47 | edge | creative_volatile | 2.2 | WildChat | Auto-selected from candidate_creative_volatile.csv candidates. |
| P48 | edge | creative_volatile | 2.2 | WildChat | Auto-selected from candidate_creative_volatile.csv candidates. |
| P49 | edge | creative_volatile | 2.2 | WildChat | Auto-selected from candidate_creative_volatile.csv candidates. |
| P50 | edge | creative_volatile | 2.2 | WildChat | Auto-selected from candidate_creative_volatile.csv candidates. |
| C01 | calibration | nan | 1.1 | WildChat | Calibration prompt for rater training. |
| C02 | calibration | nan | 1.1 | WildChat | Calibration prompt for rater training. |
| C03 | calibration | nan | 1.1 | WildChat | Calibration prompt for rater training. |
| C04 | calibration | nan | 1.1 | WildChat | Calibration prompt for rater training. |
| C05 | calibration | nan | 1.1 | WildChat | Calibration prompt for rater training. |