# LaTeX source of the report

LaTeX source of the group report. The results come from the post-freeze correction run of 18 November 2026 (`results/corrections/2026-11-18/`), which gives the same recommendation as the freeze of 17 November 2026. The additional runs of 21 November 2026 (`results/corrections/2026-11-21/`) answer review questions and do not change the recommendation.

**The submission is one PDF of 49 pages.**
- Pages 1–2: title page and contents.
- Pages 3–21: Sections 1–6, about 18 pages of narrative.
- Pages 21–23: statement on assistance and references.
- Pages 24–49: Appendices A–E.

This folder is the LaTeX source of `report/report.pdf`. In this public copy the title page lists the team without student IDs.

## Opening it in Overleaf

1. In Overleaf, choose **New Project → Upload Project** and upload a ZIP of this `report/latex/` folder.
2. Open **Menu → Settings** and set **Compiler** to **XeLaTeX**. Leave **Main document** as `main.tex`.
3. Recompile. Overleaf runs BibTeX automatically.

`report/report.pdf` was compiled from this folder with Tectonic 0.17.0, which uses the same XeTeX engine as Overleaf's XeLaTeX. The preamble also has an untested pdfLaTeX branch (newtx Times fonts); use XeLaTeX.

## Files

| Path | What it is | Who edits it |
|---|---|---|
| `main.tex` | Preamble, layout settings, title page with abstract, and the list of section files | Change only the title page and settings |
| `sections/1_problem.tex` to `6_evaluation.tex` | Sections 1 to 6 | The team |
| `sections/statement_on_assistance.tex` | The statement on assistance | The team |
| `sections/appendix_*.tex` | Appendices A to E | The team |
| `figures/budget_wages.tex` | Figure 1, drawn with pgfplots from `tables/fig_*.dat` | Styling only; never type values here |
| `tables/*.tex`, `tables/*.dat` | Tables and figure data generated from the saved outputs and input files | Nobody: regenerate them instead (see below) |
| `code/transfer_model.py` | The optimisation model, printed in full in Appendix D | Nobody: copy again from `src/` after a code change |
| `code/run_toy_example.py`, `code/toy/` | The runnable example of Appendix D: driver, two input files and its recorded output | Copy again from `demo/` and `data/toy/` |
| `references.bib` | References; every entry was checked against its DOI record | The team |

## What the main text contains

1. **Problem:** the decision, the scope and objective, and related work.
2. **Data:** sources, players and roles, the quality proxy, and fees and wages.
3. **Formulation:** sets, parameters and variables, the objective, the constraints, and the model type and structure (network flow and total unimodularity).
4. **Method:** the solver, the linear relaxation, and a one-paragraph validation summary.
5. **Results:**
   - the base plan;
   - which limits restrict it (Figure 1 and the one-step table with relaxation dual prices);
   - the other sensitivity runs;
   - a protected wage limit (robust counterpart);
   - the stability of each purchase.
6. **Evaluation:** the 2025/26 outcomes, limitations and the conclusion.

## What the appendices contain

- **A:**
  - the summary table of inputs;
  - candidate filters and the existing players;
  - fee and wage rules, with the evidence behind the 1.3 mark-up;
  - score formulas with two worked examples.
- **B:**
  - the base line-up;
  - full plans and direct alternatives, with the deal-label rules;
  - the additional runs of 21 November;
  - every run of 18 November;
  - the shortlist review, hand-entered lists and dated sources.
- **C:** validation summary (including the additional runs and the check of the protected-wage method), actual arrivals, players at two clubs and individual outcomes.
- **D:**
  - versions and external data;
  - a table of the processing scripts, which are kept in `src/` and not printed;
  - the symbol-to-code correspondence;
  - the runnable example;
  - the complete `transfer_model.py`.
- **E:** the stages of the study and the dated record of the procedure.

Code listings fill pages 40–48. **Not printed** (all files remain in the repository):
- the supporting scripts, including `extra_runs.py`;
- the full test framework;
- the individual outcomes of the 18 direct alternatives, which are summarised in the evaluation table;
- the 42-row youth-team name list;
- the raw data and the payroll page.

## Regenerating the tables and figure data

From the repository root:

```
C=results/corrections/2026-11-18
python src/extra_runs.py --out results/corrections/2026-11-21
python src/make_latex_tables.py --model $C/model --evaluation $C/evaluation --extra results/corrections/2026-11-21 --out report/latex/tables
```

The first command is needed only if the additional runs must be repeated (about 25 seconds with Gurobi). Then upload the refreshed `tables/` folder to Overleaf. Some figures in the prose are typed in, for example 1,100.959, £198.691m, £147.94m, 20.5, 6.9, 7.5, 2.46 and the playing-time counts 153 and 830, so check them against the tables after any rerun.

## Running the example

Put `transfer_model.py`, `run_toy_example.py`, `toy/players.csv` and `toy/roles.csv` in one folder and run `python run_toy_example.py`. It needs Python 3 and `gurobipy`; the licence bundled with `gurobipy` is enough. The output should match `toy/output.txt` (objective 234 at a £40m net allowance and 230 at £30m).

## Formatting

- **Font:** TeX Gyre Termes (Times family) at 12 pt; code in Inconsolata at 12 pt; the figure uses the document font.
- **Page:** A4 with one-inch margins and page numbers on every page.
- **Spacing:** prose is double-spaced, including the appendices. Tables, code listings and the reference list are single-spaced.
- **Hyphenation:** off in the text. A long code line wraps at a space and the continuation is marked with an arrow.
- **Page layout:** all pages are portrait.
- **Appendix tables:** they may float within their own appendix but never cross into the next one.

## Before submission

- **Placeholders:** none remain. The title page (group 20, names, student IDs, instructor and teaching assistants) was completed by the team on 22 November 2026, and the statement on assistance was drafted the same day; the team should confirm that it names every tool used.
- **Team review:** every member should be able to explain each constraint, the protected wage limit and the code in Appendix D.
