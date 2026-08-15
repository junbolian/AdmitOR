# -*- coding: utf-8 -*-
"""Pytest configuration for the AdmitOR offline test suite.

Puts the repository root and the scripts directory on sys.path so tests can
import the `admitor` package and the experiment-driver modules the same way
the documented commands do.

The whole suite runs offline: nothing here reaches the network and no
credentials are read. Tests that would need a live endpoint are marked
`network` and deselected by default (see pytest.ini).
"""
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(REPO_ROOT, "scripts")

for path in (REPO_ROOT, SCRIPTS_DIR):
    if path not in sys.path:
        sys.path.insert(0, path)
