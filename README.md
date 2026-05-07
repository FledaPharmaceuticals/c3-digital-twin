# C3 Digital Twin

Alternative pathway complement digital twin — interactive QSP simulator with literature validation.

This is a standalone Fleda demo application for medical research and clinical-consulting demonstrations. It is independent from Gummynology, GN OS, GN Lab, GN Quote, procurement, and any GN customer or production data.

## Quick Start

```bash
pip install -r requirements.txt
streamlit run app.py
```

Open `http://localhost:8501`.

## Included Assets

- `app.py`: Streamlit dashboard and ODE simulation UI.
- `c3_twin_loader.py`: pure `openpyxl` XLSX loader and dataclass query API.
- `C3_Digital_Twin_Literature_Extraction_Template.xlsx`: literature calibration workbook.
- `calibration_audit.md`: calibration data audit report.
- `demo_ap_core.py`: command-line ODE demo for advanced users.

## Data Sources

The calibration workbook consolidates complement-system model and validation data from major literature sources, including:

- Zewde & Morikis 2016, PLoS ONE, DOI: `10.1371/journal.pone.0152337`
- Zewde & Morikis 2018, PLoS ONE, DOI: `10.1371/journal.pone.0197970`
- Bakshi et al. 2020, Bulletin of Mathematical Biology, PMCID: `PMC7024062`
- Bansal et al. 2022, Frontiers in Pharmacology, DOI: `10.3389/fphar.2022.855743`
- Caruso et al. 2020, PLoS Computational Biology, DOI: `10.1371/journal.pcbi.1008139`
- Liu et al. 2011, PLoS Computational Biology, DOI: `10.1371/journal.pcbi.1001059`
- Pangburn & Muller-Eberhard 1983, Journal of Immunology
- Pangburn & Muller-Eberhard 1986, Biochemical Journal
- Hourcade 2011, Journal of Biological Chemistry

See `calibration_audit.md` for row-level source checks, confidence flags, VERIFY markers, and cross-source consistency notes.

## Calibration Status

The current Streamlit application includes scenario-aware validation against the workbook's `Template_validation_timeseries` data. The `Validate against experiments` action runs canonical simulations per experimental condition and reports aggregate and per-scenario fit status.

Core scientific constraints for this deployment:

- Do not modify `rhs()`.
- Do not modify `default_k()`.
- Do not modify `CONDITION_TO_SCENARIO`.
- Do not modify `C3_Digital_Twin_Literature_Extraction_Template.xlsx`.
- Do not add `pandas`; the loader intentionally uses `openpyxl` only.

## Deployment

Preferred public demo deployment: Streamlit Community Cloud with a Fleda subdomain such as `c3twin.fledausa.com`.

After deployment, update this section with:

- Public URL:
- Deployment platform:
- DNS target:

See `DEPLOYMENT.md` for deployment and rollback notes.

## Academic Use

If using this simulator in academic or consulting materials, cite this repository and the primary literature sources listed above. The simulator is intended for research and demonstration use, not for diagnosis, treatment decisions, or electronic health record use.

## License

MIT License.
