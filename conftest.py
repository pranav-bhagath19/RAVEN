
"""
Pytest configuration and root path configuration for RAVEN test suite.
"""

import sys
from pathlib import Path

# Insert project root into sys.path
root_dir = Path(__file__).resolve().parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))
