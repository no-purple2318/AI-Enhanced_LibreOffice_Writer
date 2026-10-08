#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.app import DocxAnalyzerApp

if __name__ == "__main__":
    app = DocxAnalyzerApp()
    app.mainloop()
