"""Zero-install entry point: `python run.py <command>` == `zontar <command>`.

Works from a fresh clone without `pip install -e .` (adds ./src to sys.path).
    python run.py status
    python run.py run volkswagen_tiguan
    python run.py doctor
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from zontar.cli import main  # noqa: E402

raise SystemExit(main())
