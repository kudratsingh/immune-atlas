CREATE TABLE projects (
    project_id   TEXT PRIMARY KEY
);

CREATE TABLE subjects (
    subject_id   TEXT PRIMARY KEY,
    project_id   TEXT NOT NULL REFERENCES projects(project_id),
    condition    TEXT NOT NULL,
    age          INTEGER NOT NULL CHECK (age >= 0),
    sex          TEXT NOT NULL CHECK (sex IN ('M', 'F')),
    treatment    TEXT NOT NULL,
    response     TEXT CHECK (response IN ('yes', 'no'))   -- NULL when not applicable
);

CREATE TABLE samples (
    sample_id                  TEXT PRIMARY KEY,
    subject_id                 TEXT NOT NULL REFERENCES subjects(subject_id),
    sample_type                TEXT NOT NULL,
    time_from_treatment_start  INTEGER NOT NULL CHECK (time_from_treatment_start >= 0),
    UNIQUE (subject_id, sample_type, time_from_treatment_start)
);

CREATE TABLE cell_populations (
    population_id  INTEGER PRIMARY KEY,
    name           TEXT NOT NULL UNIQUE,
    display_name   TEXT NOT NULL,
    sort_order     INTEGER NOT NULL
);

CREATE TABLE cell_counts (
    sample_id      TEXT NOT NULL REFERENCES samples(sample_id),
    population_id  INTEGER NOT NULL REFERENCES cell_populations(population_id),
    count          INTEGER NOT NULL CHECK (count >= 0),
    PRIMARY KEY (sample_id, population_id)
);

CREATE INDEX idx_subjects_project   ON subjects(project_id);
CREATE INDEX idx_subjects_cohort    ON subjects(condition, treatment, response);
CREATE INDEX idx_samples_subject    ON samples(subject_id);
CREATE INDEX idx_samples_type_time  ON samples(sample_type, time_from_treatment_start);
CREATE INDEX idx_counts_population  ON cell_counts(population_id);

CREATE VIEW v_sample_totals AS
SELECT sample_id, SUM(count) AS total_count
FROM cell_counts GROUP BY sample_id;

CREATE VIEW v_cell_frequencies AS
SELECT c.sample_id AS sample,
       t.total_count,
       p.name       AS population,
       c.count,
       100.0 * c.count / t.total_count AS percentage
FROM cell_counts c
JOIN cell_populations p USING (population_id)
JOIN v_sample_totals  t USING (sample_id);
