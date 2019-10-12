import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ble_flask import app as application
