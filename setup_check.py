#!/usr/bin/env python3
"""
Setup verification script for SproutsAI Candidate Recommendation Engine
Run this script to verify your environment is properly configured.
"""

import sys
import os
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} - Compatible")
    return True

def check_dependencies():
    """Check if all required dependencies are installed"""
    required_packages = [
        'fastapi', 'uvicorn', 'sentence_transformers', 'torch',
        'numpy', 'sklearn', 'fitz', 'docx', 'requests', 'pydantic'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} - Installed")
        except ImportError:
            print(f"❌ {package} - Missing")
            missing_packages.append(package)
    
    return len(missing_packages) == 0, missing_packages

def check_project_structure():
    """Check if all required files and directories exist"""
    required_paths = [
        'main.py', 'requirements.txt', 'README.md',
        'models/', 'services/', 'static/', 'templates/', 'screenshots/',
        'test_data/', '.gitignore', '.env.example'
    ]
    
    missing_paths = []
    for path in required_paths:
        if not Path(path).exists():
            print(f"❌ {path} - Missing")
            missing_paths.append(path)
        else:
            print(f"✅ {path} - Present")
    
    return len(missing_paths) == 0, missing_paths

def check_test_data():
    """Check if sample test data is available"""
    test_files = [
        'test_data/job_descriptions/data_scientist.txt',
        'test_data/resumes/sarah_data_scientist.txt'
    ]
    
    available = 0
    for file_path in test_files:
        if Path(file_path).exists():
            available += 1
            print(f"✅ {file_path} - Available")
        else:
            print(f"❌ {file_path} - Missing")
    
    return available > 0

def main():
    print("🚀 SproutsAI Candidate Recommendation Engine - Setup Check")
    print("=" * 60)
    
    # Check Python version
    print("\n📋 Checking Python Version...")
    python_ok = check_python_version()
    
    # Check dependencies
    print("\n📦 Checking Dependencies...")
    deps_ok, missing_deps = check_dependencies()
    
    # Check project structure
    print("\n📁 Checking Project Structure...")
    structure_ok, missing_paths = check_project_structure()
    
    # Check test data
    print("\n📄 Checking Test Data...")
    test_data_ok = check_test_data()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SETUP VERIFICATION SUMMARY")
    print("=" * 60)
    
    if python_ok and deps_ok and structure_ok:
        print("🎉 SUCCESS: Your environment is ready!")
        print("\nNext steps:")
        print("1. Run: python main.py")
        print("2. Open: http://localhost:8000")
        print("3. Upload job description and resume files")
        if test_data_ok:
            print("4. Use sample files from test_data/ folder")
        print("\n💡 For AI insights, configure an AI provider in the web interface")
        return 0
    else:
        print("❌ ISSUES FOUND:")
        if not python_ok:
            print("   - Upgrade to Python 3.8+")
        if not deps_ok:
            print(f"   - Install missing packages: {', '.join(missing_deps)}")
            print("   - Run: pip install -r requirements.txt")
        if not structure_ok:
            print(f"   - Missing files/directories: {', '.join(missing_paths)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())