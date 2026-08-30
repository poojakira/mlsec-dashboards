"""Pytest configuration.

Placing this file at the repository root ensures the root directory is added to
``sys.path`` so tests can import top-level modules such as ``dashboard_server``.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
