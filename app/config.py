"""
Central configuration file including server settings, debug flags, etc.
"""
import os

DEBUG = os.getenv("DEBUG", "true").lower() == "true"
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", 8727))
