from dataclasses import dataclass, asdict
import pandas as pd

@dataclass
class QualityResult:
    dataset: str
    input_rows: int
    output_rows: int
    duplicates_removed: int
    invalid_rows: int
    missing_critical_values: int
    status: str

def quality_result(dataset, input_rows, output_rows, duplicates_removed, invalid_rows, missing_critical_values):
    status = "PASS" if invalid_rows == 0 and missing_critical_values == 0 else "WARN"
    return QualityResult(dataset, input_rows, output_rows, duplicates_removed,
                         invalid_rows, missing_critical_values, status)

def write_quality_report(results, path):
    pd.DataFrame([asdict(r) for r in results]).to_csv(path, index=False)
