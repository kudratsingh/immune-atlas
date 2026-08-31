"""Shape baseline sample rows into sample- and subject-level breakdowns."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True, slots=True)
class BaselineSummary:
    """Hold baseline counts with explicit sample- and subject-level tables.

    `by_project` columns are `project, n_samples`; `by_response` columns are
    `response, n_subjects`; `by_sex` columns are `sex, n_subjects`. `sample_ids`
    contains each distinct sample in stable sorted order.
    """

    n_samples: int
    n_subjects: int
    by_project: pd.DataFrame
    by_response: pd.DataFrame
    by_sex: pd.DataFrame
    sample_ids: tuple[str, ...]


def summarise_baseline(samples_df: pd.DataFrame) -> BaselineSummary:
    """Summarise baseline rows without conflating samples and subjects.

    Input columns are `sample, subject, project, response, sex`, with one row per
    sample; a subject may have multiple samples. Output `by_project` counts distinct
    samples, while `by_response` and `by_sex` count distinct subjects. Their output
    columns are respectively `project, n_samples`, `response, n_subjects`, and
    `sex, n_subjects`; `sample_ids` is sorted.
    """
    required = ("sample", "subject", "project", "response", "sex")
    missing = [column for column in required if column not in samples_df.columns]
    if missing:
        raise ValueError(f"missing required columns: {', '.join(missing)}")
    frame = samples_df.loc[:, list(required)].copy()
    if frame[["sample", "subject", "project", "response", "sex"]].isna().any().any():
        raise ValueError("baseline summary columns must not contain null values")
    if frame["sample"].duplicated().any():
        raise ValueError("baseline input must contain one row per sample")
    for column in ("project", "response", "sex"):
        consistency = frame.groupby("subject")[column].nunique(dropna=False)
        if (consistency != 1).any():
            raise ValueError(f"{column} must be constant within each subject")

    subjects = frame.drop_duplicates(subset=["subject"])
    n_samples = int(frame["sample"].nunique())
    n_subjects = int(subjects["subject"].nunique())
    by_project = (
        frame.groupby("project", sort=True)["sample"].nunique().rename("n_samples").reset_index()
    )
    by_response = (
        subjects.groupby("response", sort=True)["subject"]
        .nunique()
        .rename("n_subjects")
        .reset_index()
    )
    by_sex = (
        subjects.groupby("sex", sort=True)["subject"].nunique().rename("n_subjects").reset_index()
    )
    return BaselineSummary(
        n_samples=n_samples,
        n_subjects=n_subjects,
        by_project=by_project,
        by_response=by_response,
        by_sex=by_sex,
        sample_ids=tuple(sorted(frame["sample"].astype(str))),
    )
