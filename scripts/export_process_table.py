"""
Export the unified process table example to a PSV (pipe-separated values) ready for Google Sheets or copy/paste.
You can adapt this to export a live table (e.g., loaded from a DB) instead of the static sample.
"""
import os
import pandas as pd

SAMPLE_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'process_tables', 'shekina_unified_process_table.csv')


def load_sample_csv(path=SAMPLE_PATH) -> pd.DataFrame:
    # Skip comment lines starting with '#'
    rows = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.lstrip().startswith('#'):
                continue
            rows.append(line)
    from io import StringIO
    # Pipe-delimited
    return pd.read_csv(StringIO(''.join(rows)), sep='|')


essential_columns = [
    'id', 'process_key', 'step', 'class', 'opcode', 'enabled', 'depends_on', 'inputs', 'outputs', 'payload'
]


def export_to_gsheet_psv(out_path: str):
    df = load_sample_csv()
    # Ensure column order, fill missing
    for col in essential_columns:
        if col not in df.columns:
            df[col] = ''
    df = df[essential_columns]
    df.to_csv(out_path, index=False, sep='|')
    print(f"Exported {len(df)} rows to {out_path}")


if __name__ == '__main__':
    out = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'process_tables', 'export_for_gsheet.psv'))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    export_to_gsheet_psv(out)
