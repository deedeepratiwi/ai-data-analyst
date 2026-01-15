#!/usr/bin/env python3
"""
Quick Test Runner

Runs integration tests with various options.

Usage:
    python tests/run_tests.py              # Run all tests
    python tests/run_tests.py --fast       # Run fast tests only
    python tests/run_tests.py --critical   # Run critical security tests
    python tests/run_tests.py --verbose    # Verbose output
"""

import sys
import subprocess
from pathlib import Path

def main():
    project_root = Path(__file__).parent.parent
    test_file = project_root / "tests" / "test_integration.py"
    
    # Parse arguments
    args = sys.argv[1:]
    
    # Build pytest command
    cmd = ["pytest", str(test_file)]
    
    if "--fast" in args:
        # Run only fast tests (exclude LLM tests)
        cmd.extend(["-k", "not insight and not llm"])
        print("🚀 Running fast tests (excluding LLM calls)...")
    elif "--critical" in args:
        # Run only critical security tests
        cmd.extend(["-k", "leakage or security"])
        print("🔒 Running critical security tests...")
    else:
        print("🧪 Running all integration tests...")
    
    if "--verbose" in args or "-v" in args:
        cmd.append("-v")
    else:
        cmd.append("-v")  # Always verbose by default
    
    # Add useful options
    cmd.extend([
        "--tb=short",           # Short traceback
        "--color=yes",          # Colored output
        "-ra",                  # Show summary of all test outcomes
    ])
    
    if "--coverage" in args:
        cmd.extend([
            "--cov=services",
            "--cov-report=term-missing",
            "--cov-report=html"
        ])
        print("📊 Coverage reporting enabled")
    
    print(f"Command: {' '.join(cmd)}\n")
    
    # Run tests
    result = subprocess.run(cmd, cwd=project_root)
    
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
