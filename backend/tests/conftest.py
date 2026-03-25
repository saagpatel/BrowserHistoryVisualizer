"""Test configuration."""

import warnings

import pandas as pd

pd.set_option("mode.copy_on_write", True)

# Suppress pandas CoW chained assignment warnings — we always work on copies
warnings.filterwarnings("ignore", message=".*ChainedAssignment.*", category=FutureWarning)
warnings.filterwarnings("ignore", message=".*ChainedAssignment.*")
