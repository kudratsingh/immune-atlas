# Assignment specification

Section 1 is the assignment text as provided, transcribed without edits so that
every requirement can be traced. Section 2 turns it into a checklist with the
verification method for each item. Section 3 records interpretation decisions
where the text left room for more than one reading.

## 1. Assignment text (verbatim)

### Data Provided

File cell-count.csv contains cell count information for various immune cell
populations of each patient sample. There are five populations: b_cell,
cd8_t_cell, cd4_t_cell, nk_cell, and monocyte. Each row in the file corresponds to
a biological sample.

The file also includes sample metadata such as sample_id, indication, treatment,
time_from_treatment_start, response, and gender.

### Your Task

Bob Loblaw, a drug developer at Loblaw Bio, is running a clinical trial and needs
your help to understand how his drug candidate affects immune cell populations.
Your job is to:

- Design a Python program that meets Bob's analytical needs, as outlined in Parts
  1-4 below.
- Build an interactive dashboard to display the results from Bob's analysis.

### Part 1: Data Management

Using the data provided in cell-count.csv, your first task is to:

- Design a relational database schema (using SQLite) that models this data
  effectively.
- Create a Python script named "load_data.py" in the root directory of your
  repository that:
  - Initializes the database with your schema.
  - Loads all rows from cell-count.csv.
- Requirements:
  The script must be named `load_data.py` and located in the root directory (not
  in subdirectories like `src/`).
  - When executed with `python load_data.py`, it should create a SQLite database
    file (`.db` extension) in the repository root.
  - The script should be executable directly without command-line arguments or
    module-style execution (`python -m`).

### Part 2: Initial Analysis - Data Overview

Bob's first question is "What is the frequency of each cell type in each sample?"
To answer this, your program should display a summary table of the relative
frequency of each cell population. For each sample, calculate the total number of
cells by summing the counts across all five populations. Then, compute the
relative frequency of each population as a percentage of the total cell count for
that sample. Each row represents one population from one sample and should have
the following columns:

- sample: the sample id as in column sample in cell-count.csv
- total_count: total cell count of sample
- population: name of the immune cell population (e.g. b_cell, cd8_t_cell, etc.)
- count: cell count
- percentage: relative frequency in percentage

### Part 3: Statistical Analysis

As the trial progresses, Bob wants to identify patterns that might predict
treatment response and share those findings with his colleague, Yah D'yada. Using
the data reported in the summary table, your program should provide functionality
to:

- Compare the differences in cell population relative frequencies of melanoma
  patients receiving miraclib who respond (responders) versus those who do not
  (non-responders), with the overarching aim of predicting response to the
  treatment miraclib. Response information can be found in column "response",
  with value "yes" for responding and value "no" for non-responding. Please only
  include PBMC samples.
- Visualize the population relative frequencies comparing responders versus
  non-responders using a boxplot of for each immune cell population.
- Report which cell populations have a significant difference in relative
  frequencies between responders and non-responders. Statistics are needed to
  support any conclusion to convince Yah of Bob's findings.

### Part 4 Data Subset Analysis

Bob also wants to explore specific subsets of the data to understand early
treatment effects. Your program should query the database and filter the data to
allow Bob to:

1. Identify all melanoma PBMC samples at baseline (time_from_treatment_start is 0)
   from patients who have been treated with miraclib.
2. Among these samples, extend the query to determine:
   1. How many samples from each project
   2. How many subjects were responders/non-responders
   3. How many subjects were males/females

### Form question

Considering Melanoma males of all sample and treatment types, what is the average
number of B cells for responders at time=0? Use two decimals (XXX.XX).

### Submission Requirements

Please submit your solution as a GitHub repository link.

Your project should include:

- Your Python program with all accompanying files
- Any input or output files generated
- A README.md with:
  - Any instructions needed to run your code and reproduce the outputs (We will
    run your code using GitHub Codespaces).
  - An explanation of the schema used for the relational database, with rationale
    for the design and how this would scale if there were hundreds of projects,
    thousands of samples and various types of analytics you'd want to perform.
  - A brief overview of your code structure and an explanation of why you
    designed it the way you did.
  - A link to the dashboard.
- **A Makefile in the root directory.** We will use this to automatically grade
  your submission using GitHub Codespaces. Your Makefile **must** implement the
  following three targets exactly as named:
  - make setup: Installs all necessary dependencies for your project (e.g., from a
    requirements.txt, environment.yml, or pyproject.toml).
  - make pipeline: Executes your entire data pipeline sequentially from start to
    finish without any manual intervention. When our grader runs this command, it
    should initialize the database, load the data (Part 1), and generate all
    required output tables and plots (Parts 2-4). (Note: You may use pure Python,
    bash scripts, Snakemake, or any other orchestration tool, as long as make
    pipeline triggers the complete execution).
  - make dashboard: Starts the local server for your interactive dashboard.

Link to your Github repository (publicly accessible is fine) with all relevant
files.

## 2. Acceptance checklist

Each item names how it is verified. "IT" means an integration test under
`tests/integration/`; "CI" means a dedicated CI job; "Review" means checked by
reading before submission.

### Part 1 — data management

| # | Requirement | Verified by |
| - | ----------- | ----------- |
| 1.1 | Relational SQLite schema models the data (projects, subjects, samples, populations, counts). | Review of `schema.sql` against ADR-0001; unit tests on constraints. |
| 1.2 | `load_data.py` exists in the repository root. | CI `pipeline` job: `test -f load_data.py`. |
| 1.3 | `python load_data.py` with no arguments creates a `.db` file in the repository root. | IT runs the script via `subprocess` in a temp copy of the repo and asserts the file exists. |
| 1.4 | All 10,500 rows load; row counts in DB equal CSV. | IT compares `COUNT(*)` against the CSV. |
| 1.5 | Script is re-runnable (fresh database each run, no duplicate rows). | IT runs it twice. |
| 1.6 | Loader rejects malformed input loudly (missing column, negative count, unknown population). | Unit tests on the validator. |

### Part 2 — summary table

| # | Requirement | Verified by |
| - | ----------- | ----------- |
| 2.1 | Table has exactly the columns `sample, total_count, population, count, percentage` in that order. | Unit test + IT on `outputs/cell_frequencies.csv`. |
| 2.2 | One row per (sample, population): 10,500 × 5 = 52,500 rows. | IT. |
| 2.3 | `total_count` is the sum of the five populations for that sample. | Unit test on synthetic data; IT spot-checks. |
| 2.4 | `percentage` = count / total_count × 100; the five percentages per sample sum to 100 ± 1e-6. | Unit test + IT. |
| 2.5 | Table is written to `outputs/` by `make pipeline` and shown in the dashboard. | IT + e2e. |

### Part 3 — response comparison

| # | Requirement | Verified by |
| - | ----------- | ----------- |
| 3.1 | Cohort filter: condition = melanoma, treatment = miraclib, sample_type = PBMC. | Unit test; IT asserts 1,968 samples / 656 subjects (see DATA_NOTES). |
| 3.2 | Groups: response = yes vs response = no; nulls excluded. | Unit test. |
| 3.3 | Per-population comparison of relative frequency with a statistical test, effect size, and multiple-comparison adjustment (ADR-0002). | Unit tests with known-effect synthetic data; IT on real data. |
| 3.4 | Boxplot per population, responders vs non-responders, saved to `outputs/plots/`. | IT asserts files exist and are non-trivial PNGs. |
| 3.5 | A report states which populations differ significantly, with the numbers that justify it. | `outputs/response_comparison.csv` + `.md`; dashboard page; README findings. |
| 3.6 | Per-subject sensitivity analysis accompanies the per-sample primary analysis. | Unit test + IT. |

### Part 4 — baseline subset

| # | Requirement | Verified by |
| - | ----------- | ----------- |
| 4.1 | SQL query returns melanoma PBMC baseline (time 0) samples from miraclib-treated subjects. | IT asserts 656 samples. |
| 4.2 | Samples per project. | IT asserts prj1 = 384, prj3 = 272. |
| 4.3 | Subjects per response. | IT asserts yes = 331, no = 325. |
| 4.4 | Subjects per sex. | IT asserts M = 344, F = 312. |
| 4.5 | Queries run against the database, not the CSV. | Review: implemented in `db/queries.py` as SQL. |

### Dashboard

| # | Requirement | Verified by |
| - | ----------- | ----------- |
| D.1 | Interactive; displays Parts 2, 3 and 4 results. | e2e smoke tests. |
| D.2 | `make dashboard` starts it locally with no manual steps. | CI `pipeline` job starts the server and curls it. |
| D.3 | Publicly hosted; README links to it. | Review before submission. |

### Repository and grading

| # | Requirement | Verified by |
| - | ----------- | ----------- |
| R.1 | `Makefile` at root with `setup`, `pipeline`, `dashboard` targets exactly as named. | CI `pipeline` job runs all three. |
| R.2 | `make pipeline` is idempotent; data outputs are byte-identical across runs. | CI: `git diff --exit-code` on `outputs/` (excluding plots and the run report) and the bundle; IT checks the database and plots structurally. |
| R.3 | README covers: run instructions (Codespaces), schema + rationale + scaling, code structure + rationale, dashboard link. | Review against this list. |
| R.4 | Input and output files are committed. | Review. |
| R.5 | Works from a fresh Codespace on the default image. | Manual run in a Codespace before submission. |

## 3. Interpretations

- **"sample_id", "indication", "gender"** in the prose correspond to the actual
  CSV columns `sample`, `condition`, `sex`. The CSV wins; the Part 2 output uses
  `sample` as the assignment explicitly states.
- **"Using the data reported in the summary table"** (Part 3) means the comparison
  is on `percentage` from the Part 2 table, not raw counts.
- **"Significant"** is reported at α = 0.05 both before and after
  Benjamini–Hochberg adjustment across the five populations; the report says which
  threshold each population clears. Hiding the adjustment would be the wrong way
  to convince Yah.
- **"Query the database"** (Part 4) is taken literally: the subset queries are SQL
  against SQLite, exposed as Python functions and executed by the pipeline. The
  dashboard shows the results and lets the user re-filter the same sample table
  client-side.
- **"Interactive dashboard"** is a web application. No stack was prescribed; see
  ADR-0003 for the choice.
- **Form question**: "average number of B cells" is the arithmetic mean of the raw
  `b_cell` count over matching samples (condition = melanoma, sex = M,
  response = yes, time_from_treatment_start = 0, any sample_type, any treatment).
  The pipeline computes and writes it so the number is reproducible.
