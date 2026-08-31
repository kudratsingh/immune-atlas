/* Generated from contracts/dashboard-bundle.schema.json. Do not edit directly. */

export type NonNegativeInt = number;
export type Population = "b_cell" | "cd8_t_cell" | "cd4_t_cell" | "nk_cell" | "monocyte";
export type Sex = "M" | "F";
export type Response = "yes" | "no";
export type Percentage = number;
export type NullableNumber = number | null;
export type Interval = [number, number] | null;

/**
 * Everything the dashboard renders. Written by immune_atlas.export, read by dashboard/src/lib/bundle.ts.
 */
export interface DashboardBundle {
  schema_version: "1.0";
  meta: Meta;
  samples: Sample[];
  frequencies_long: FrequencyRow[];
  response_analysis: ResponseAnalysis;
  baseline_subset: BaselineSubset;
  form_answer: FormAnswer;
  run: RunReport;
}
export interface Meta {
  generated_at: string;
  source_file: string;
  source_sha256: string;
  n_rows: NonNegativeInt;
  n_samples: NonNegativeInt;
  n_subjects: NonNegativeInt;
  n_projects: NonNegativeInt;
  /**
   * @minItems 1
   */
  populations: [PopulationInfo, ...PopulationInfo[]];
  time_points: NonNegativeInt[];
  conditions: string[];
  treatments: string[];
  sample_types: string[];
}
export interface PopulationInfo {
  name: Population;
  display_name: string;
  sort_order: NonNegativeInt;
}
export interface Sample {
  sample: string;
  subject: string;
  project: string;
  condition: string;
  age: NonNegativeInt;
  sex: Sex;
  treatment: string;
  response: Response | null;
  sample_type: string;
  time: NonNegativeInt;
  total_count: number;
  counts: CountsByPopulation;
  percentages: PercentagesByPopulation;
}
export interface CountsByPopulation {
  b_cell: NonNegativeInt;
  cd8_t_cell: NonNegativeInt;
  cd4_t_cell: NonNegativeInt;
  nk_cell: NonNegativeInt;
  monocyte: NonNegativeInt;
}
export interface PercentagesByPopulation {
  b_cell: Percentage;
  cd8_t_cell: Percentage;
  cd4_t_cell: Percentage;
  nk_cell: Percentage;
  monocyte: Percentage;
}
/**
 * One row of the Part 2 summary table, column names as required by the assignment.
 */
export interface FrequencyRow {
  sample: string;
  total_count: number;
  population: Population;
  count: NonNegativeInt;
  percentage: Percentage;
}
export interface ResponseAnalysis {
  cohort: CohortFilter;
  n: GroupCounts;
  by_sample: Comparison;
  by_subject: Comparison;
  by_time: TimeComparison[];
  distributions: Distribution[];
}
export interface CohortFilter {
  condition: string;
  treatment: string;
  sample_type: string;
  time?: NonNegativeInt;
}
export interface GroupCounts {
  samples_yes: NonNegativeInt;
  samples_no: NonNegativeInt;
  subjects_yes: NonNegativeInt;
  subjects_no: NonNegativeInt;
}
export interface Comparison {
  unit: "sample" | "subject";
  alpha: number;
  method: string;
  adjustment: string;
  n_samples: NonNegativeInt;
  n_subjects: NonNegativeInt;
  rows: ComparisonRow[];
}
/**
 * Statistics for one population. Numeric fields are null when a group has fewer than three values.
 */
export interface ComparisonRow {
  population: Population;
  n_yes: NonNegativeInt;
  n_no: NonNegativeInt;
  mean_yes: NullableNumber;
  mean_no: NullableNumber;
  sd_yes: NullableNumber;
  sd_no: NullableNumber;
  median_yes: NullableNumber;
  median_no: NullableNumber;
  iqr_yes: Interval;
  iqr_no: Interval;
  u_statistic: NullableNumber;
  p_value: NullableNumber;
  q_value: NullableNumber;
  /**
   * Rank-biserial correlation; positive means responders higher.
   */
  effect_size: number | null;
  welch_p: NullableNumber;
  significant_raw: boolean;
  significant_adjusted: boolean;
}
export interface TimeComparison {
  time: NonNegativeInt;
  comparison: Comparison;
}
/**
 * Raw values behind one box in the box plots, with sample identifiers for hover detail.
 */
export interface Distribution {
  population: Population;
  response: Response;
  points: {
    sample: string;
    subject: string;
    time: NonNegativeInt;
    percentage: Percentage;
  }[];
}
export interface BaselineSubset {
  filter: CohortFilter;
  n_samples: NonNegativeInt;
  n_subjects: NonNegativeInt;
  by_project: {
    project: string;
    n_samples: NonNegativeInt;
  }[];
  by_response: {
    response: Response;
    n_subjects: NonNegativeInt;
  }[];
  by_sex: {
    sex: Sex;
    n_subjects: NonNegativeInt;
  }[];
  sample_ids: string[];
}
export interface FormAnswer {
  question: string;
  filter: {
    condition: string;
    sex: Sex;
    response: Response;
    time: NonNegativeInt;
  };
  n_samples: NonNegativeInt;
  n_subjects: NonNegativeInt;
  mean_b_cell: number;
}
export interface RunReport {
  source_sha256: string;
  pipeline_version: string;
  python_version: string;
  library_versions: {
    pandas: string;
    numpy: string;
    scipy: string;
    matplotlib: string;
    jsonschema: string;
  };
  stages: {
    name: string;
    seconds: number;
    rows_in: NonNegativeInt | null;
    rows_out: NonNegativeInt | null;
  }[];
  warnings: string[];
}
