"""
Central configuration file including server settings, debug flags, etc.
"""
import os

DEBUG = os.getenv("DEBUG", "true").lower() == "true"
PORT = int(os.getenv("PORT", 8727))
