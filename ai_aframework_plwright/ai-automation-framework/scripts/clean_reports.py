#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Utility script to clean all test reports
"""
import shutil
import os
import sys
from pathlib import Path

# Ensure UTF-8 output on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')


def clean_allure_reports():
    """Clean all Allure report directories"""
    # Get project root (parent of scripts directory)
    project_root = Path(__file__).parent.parent
    
    # Directories to clean
    dirs_to_clean = [
        project_root / "reports" / "allure-results",
        project_root / "reports" / "allure-report",
        project_root / "reports" / "screenshots",
        project_root / "reports" / "videos",
        project_root / "reports" / "logs"
    ]
    
    print("=" * 80)
    print("CLEANING TEST REPORTS")
    print("=" * 80)
    
    for directory in dirs_to_clean:
        if directory.exists():
            try:
                # Remove all contents but keep the directory
                for item in directory.iterdir():
                    if item.is_file():
                        item.unlink()
                        print(f"[OK] Deleted file: {item.name}")
                    elif item.is_dir():
                        shutil.rmtree(item)
                        print(f"[OK] Deleted directory: {item.name}")
                
                print(f"[OK] Cleaned: {directory.name}/")
            except Exception as e:
                print(f"[ERROR] Error cleaning {directory.name}/: {e}")
        else:
            print(f"[SKIP] Directory not found: {directory.name}/")
    
    print("-" * 80)
    print("[SUCCESS] All reports cleaned!")
    print("=" * 80)


def clean_allure_only():
    """Clean only Allure directories (keep screenshots, videos, logs)"""
    # Get project root (parent of scripts directory)
    project_root = Path(__file__).parent.parent
    
    dirs_to_clean = [
        project_root / "reports" / "allure-results",
        project_root / "reports" / "allure-report"
    ]
    
    print("=" * 80)
    print("CLEANING ALLURE REPORTS ONLY")
    print("=" * 80)
    
    for directory in dirs_to_clean:
        if directory.exists():
            try:
                for item in directory.iterdir():
                    if item.is_file():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item)
                
                print(f"[OK] Cleaned: {directory.name}/")
            except Exception as e:
                print(f"[ERROR] Error cleaning {directory.name}/: {e}")
    
    print("-" * 80)
    print("[SUCCESS] Allure reports cleaned!")
    print("=" * 80)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--allure-only":
        clean_allure_only()
    else:
        clean_allure_reports()
