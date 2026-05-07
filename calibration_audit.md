# C3 Digital Twin — Calibration Audit Report

_Generated 2026-04-16 from `C3_Digital_Twin_Literature_Extraction_Template.xlsx`_

## 1. Headline numbers

- Total payload rows: **285**
- Source papers / labels referenced: **18**
- Sheets with data: **10** of 10
- Rows flagged VERIFY: **31**
- Confidence mix: TABULATED=17, REPORTED=152, DERIVED=18, FIGURE_EST=67, VERIFY=31

## 2. Per-sheet coverage and confidence

| sheet | rows | TABULATED | REPORTED | DERIVED | FIGURE_EST | VERIFY |
|---|---|---|---|---|---|---|
| Template_species_baseline | 45 | 0 | 45 | 0 | 0 | 0 |
| Template_kinetic_parameters | 52 | 0 | 32 | 18 | 0 | 2 |
| Template_parameter_bounds | 25 | 0 | 25 | 0 | 0 | 0 |
| Template_perturbation_rules | 9 | 0 | 9 | 0 | 0 | 0 |
| Template_validation_timeseries | 71 | 10 | 1 | 0 | 60 | 0 |
| Template_reaction_registry | 1 | 0 | 1 | 0 | 0 | 0 |
| Template_steady_state_targets | 25 | 7 | 4 | 0 | 7 | 7 |
| Template_phenotype_mapping | 13 | 0 | 5 | 0 | 0 | 8 |
| Template_drug_pk_parameters | 34 | 0 | 23 | 0 | 0 | 11 |
| Template_reaction_step_kinetics | 10 | 0 | 7 | 0 | 0 | 3 |

## 3. Per-paper contribution

| paper_id | rows | sheets |
|---|---|---|
| BANSAL_2022_QSP | 84 | drug_pk_parameters, kinetic_parameters, parameter_bounds, perturbation_rules, phenotype_mapping, species_baseline, steady_state_targets, validation_timeseries |
| ZEWDE_2016_AP_core | 58 | kinetic_parameters, parameter_bounds, perturbation_rules, reaction_registry, species_baseline, steady_state_targets, validation_timeseries |
| CARUSO_2020_hemolysis | 41 | phenotype_mapping, species_baseline, validation_timeseries |
| ZEWDE_2018_disease_drug | 32 | drug_pk_parameters, kinetic_parameters, parameter_bounds, perturbation_rules, phenotype_mapping, steady_state_targets, validation_timeseries |
| BAKSHI_2020_reduced_AP | 20 | kinetic_parameters, parameter_bounds, steady_state_targets, validation_timeseries |
| GOODRICH_2024_reconstitution | 10 | reaction_step_kinetics |
| LIU_2011_regulation | 7 | kinetic_parameters, species_baseline |
| ZEWDE_2021_full_system | 5 | steady_state_targets |
| PANGBURN_1986 | 4 | kinetic_parameters |
| MEDOF_1987_CD59 | 4 | kinetic_parameters |
| PANGBURN_1983 | 3 | kinetic_parameters |
| RAWAL_1998_C5conv | 3 | kinetic_parameters |
| DISCIPIO_1981_MAC | 3 | kinetic_parameters |
| PODACK_1984_C9poly | 3 | kinetic_parameters |
| HOURCADE_2011_SPR | 2 | kinetic_parameters |
| KATSCHKE_2012 | 2 | kinetic_parameters |
| PRESTON_2003_C5b6 | 2 | kinetic_parameters |
| SCHUBART_2019_LNP023 | 2 | kinetic_parameters |

## 4. VERIFY queue

Rows whose values were inferred from paper conventions or labels rather than read
verbatim from a table. These should be cross-checked against the cited source
before quantitative fitting.

### Template_kinetic_parameters (2 rows)

| row | paper | source | item | note |
|---|---|---|---|---|
| r26 | ZEWDE_2018_disease_drug | S2 Table | R020_C5conv_assemble_b | VERIFY exact koff; Kd ~0.1 uM. |
| r52 | LIU_2011_regulation | Table S2 | R036 | VERIFY: 0.04 s-1 × 60; analogous to FH-cofactored C3b cleavage. |

### Template_steady_state_targets (7 rows)

| row | paper | source | item | note |
|---|---|---|---|---|
| r11 | BAKSHI_2020_reduced_AP | Table 3 | C3b | VERIFY exact value; near-zero on FH-protected surface. |
| r12 | BAKSHI_2020_reduced_AP | Table 3 | C3bB | VERIFY exact value from Table 3. |
| r13 | BAKSHI_2020_reduced_AP | Table 3 | C3bH | VERIFY exact value; FH-bound C3b regulator complex. |
| r15 | BAKSHI_2020_reduced_AP | Table 3 | C3bBb | VERIFY; ~3x higher than minimal model due to P-stabilisation. |
| r16 | BAKSHI_2020_reduced_AP | Table 3 | C3bBbP | VERIFY; properdin-stabilised C3 convertase. |
| r17 | BAKSHI_2020_reduced_AP | Table 3 | iC3b | VERIFY exact value; FI-cleaved inactive product. |
| r27 | ZEWDE_2018_disease_drug | Fig 5/6 results | fC5b9 | VERIFY; soluble TCC elevated marker in FH disorder. |

### Template_phenotype_mapping (8 rows)

| row | paper | source | item | note |
|---|---|---|---|---|
| r4 | CARUSO_2020_hemolysis | S3 Appendix Eq. 1 | MAC_per_cell | VERIFY: Caruso fits a single-hit Poisson form; alternative Hill form also reported. Confir... |
| r5 | CARUSO_2020_hemolysis | S3 Appendix | MAC_per_cell | VERIFY: order-of-magnitude estimate for rabbit RBC; confirm S3 fitted constant. |
| r6 | CARUSO_2020_hemolysis | S3 Appendix | MAC_per_cell | VERIFY: human PNH RBC less MAC-sensitive than rabbit; confirm S3 fitted constant. |
| r7 | CARUSO_2020_hemolysis | S3 Appendix (Hill alt.) | MAC_per_cell | VERIFY Hill coefficient; alternative to Poisson form. |
| r8 | CARUSO_2020_hemolysis | S3 Appendix (Hill alt.) | MAC_per_cell | VERIFY Kh from S3 fit. |
| r10 | CARUSO_2020_hemolysis | Main text Fig 4-5 | hemolysis_fraction | VERIFY proportionality constant; LDH typically 4-8x ULN at full hemolysis. |
| r12 | BANSAL_2022_QSP | Figure 6 | C5b9_per_cell | VERIFY from Fig 6 fit; Bansal uses similar Hill form. |
| r13 | BANSAL_2022_QSP | Figure 6 | C5b9_per_cell | VERIFY from Fig 6 fit. |

### Template_drug_pk_parameters (11 rows)

| row | paper | source | item | note |
|---|---|---|---|---|
| r4 | BANSAL_2022_QSP | Table 2 | small_molecule | VERIFY Table 2 exact value. |
| r5 | BANSAL_2022_QSP | Table 2 | small_molecule | VERIFY Table 2. |
| r6 | BANSAL_2022_QSP | Table 2 | small_molecule | VERIFY Table 2. |
| r7 | BANSAL_2022_QSP | Table 2 | small_molecule | VERIFY Table 2. |
| r8 | BANSAL_2022_QSP | Table 2 | small_molecule | VERIFY Table 2. |
| r9 | BANSAL_2022_QSP | Table 2 | antibody | VERIFY Table 2. |
| r10 | BANSAL_2022_QSP | Table 2 | antibody | VERIFY Table 2. |
| r11 | BANSAL_2022_QSP | Table 2 | antibody | VERIFY Table 2; FcRn-recycled mAb. |
| r12 | BANSAL_2022_QSP | Table 2 | antibody | VERIFY Table 2. |
| r13 | BANSAL_2022_QSP | Table 2 | antibody | VERIFY Table 2. |
| r33 | ZEWDE_2018_disease_drug | S1 Table | peptide | VERIFY clinical PK; estimate from Phase 1 reports. |

### Template_reaction_step_kinetics (3 rows)

| row | paper | source | item | note |
|---|---|---|---|---|
| r6 | GOODRICH_2024_reconstitution | Fig 2 (FD cleavage step) | C3bB + FD -> C3bBb + Ba | VERIFY; ~50% conversion at ~1 min for excess FD. |
| r7 | GOODRICH_2024_reconstitution | Fig 3 (convertase activity) | C3bBb + C3 -> C3b + C3a | VERIFY; estimates apparent kcat in reconstitution. |
| r8 | GOODRICH_2024_reconstitution | Fig 4 (FH decay-acceleration) | C3bBb + FH -> C3b + Bb | VERIFY; FH accelerates intrinsic 90s t1/2 to <30s. |

## 5. Cross-source consistency (shared species)

Species reported by ≥2 papers in the same unit. Spread = (max − min) / max.
Spread > 25% suggests genuine literature disagreement worth investigating.

| species | unit | n_sources | min | max | spread | flag | papers |
|---|---|---|---|---|---|---|---|
| C3 | uM | 3 | 5 | 5.4 | 7.4% | ✓ | ZEWDE_2016_AP_core, BANSAL_2022_QSP, CARUSO_2020_hemolysis |
| FH | uM | 3 | 3.1 | 3.2 | 3.1% | ✓ | ZEWDE_2016_AP_core, BANSAL_2022_QSP, CARUSO_2020_hemolysis |
| C5 | uM | 3 | 0.37 | 0.37 | 0.0% | ✓ | ZEWDE_2016_AP_core, BANSAL_2022_QSP, CARUSO_2020_hemolysis |
| C6 | uM | 2 | 0.57 | 0.57 | 0.0% | ✓ | BANSAL_2022_QSP, CARUSO_2020_hemolysis |
| C7 | uM | 2 | 0.6 | 0.6 | 0.0% | ✓ | BANSAL_2022_QSP, CARUSO_2020_hemolysis |
| C8 | uM | 2 | 0.53 | 0.53 | 0.0% | ✓ | BANSAL_2022_QSP, CARUSO_2020_hemolysis |
| C9 | uM | 2 | 0.85 | 0.85 | 0.0% | ✓ | BANSAL_2022_QSP, CARUSO_2020_hemolysis |
| FB | uM | 3 | 2.2 | 2.2 | 0.0% | ✓ | ZEWDE_2016_AP_core, BANSAL_2022_QSP, CARUSO_2020_hemolysis |
| FI | uM | 2 | 0.4 | 0.4 | 0.0% | ✓ | ZEWDE_2016_AP_core, CARUSO_2020_hemolysis |
| FP | uM | 3 | 0.47 | 0.47 | 0.0% | ✓ | ZEWDE_2016_AP_core, BANSAL_2022_QSP, CARUSO_2020_hemolysis |

## 6. Coverage gaps and recommendations

**Empty sheets**: _(none)_

**Underfilled sheets (<12 rows)**: Template_perturbation_rules (9), Template_reaction_registry (1), Template_reaction_step_kinetics (10)

**Kinetic parameter coverage by reaction context**:

| context | n |
|---|---|
| surface | 12 |
| fluid_phase | 11 |
| plasma | 9 |
| membrane | 8 |
| solution | 6 |
| surface_SPR | 2 |
| surface_self | 2 |
| surface_AMD | 1 |
| fluid_phase_to_membrane | 1 |

**Recommended next extractions** (in priority order):

1. `reaction_registry`: load Zewde 2016 S1 Text → 107 ODE state variables + RHS strings (mechanical extraction from PDF).
2. `perturbation_rules`: add aHUS variants (CFH/CD46/CFI/C3 GoF mutations) and Crovalimab/Danicopan rule cards.
3. `validation_timeseries`: digitize Bansal Fig 5 properdin-negative arm at full time resolution; add Caruso PNH human RBC time courses.
4. `phenotype_mapping`: confirm Caruso S3 Appendix exact form (Poisson vs Hill) and refit N_lethal / Kh from raw data.
