"""
Config module.
"""
import os

SRC_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_PATH = os.path.join(SRC_DIR, 'var')
REPORT_CSV_PATH = os.path.join(OUTPUT_PATH, 'report_report.csv')

try:
    from .configlocal import *
except ImportError:
    f_path = os.path.join(os.path.dirname(__file__), 'configlocal.py')
    raise ImportError("You need to create a local config file at {f_path}")
