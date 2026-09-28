"""run every definition on the synthetic example data.

usage: python examples/run_example.py
"""

from pathlib import Path

import pandas as pd

from casedefs import apply

here = Path(__file__).parent
tables = {name: pd.read_csv(here / f"{name}.csv", dtype=str)
          for name in ["claims", "hospital", "people", "procedures", "drugs"]}

cases = apply("all", **tables)
print(cases.sort_values(["definition_id", "case_date"]).to_string(index=False))
