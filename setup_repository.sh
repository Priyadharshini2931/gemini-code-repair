#!/bin/bash
set -e # Exit on error

# 1. Create and move to the testbed directory
mkdir -p /testbed
cd /testbed

# 2. Initialize and Clone the repository if it's not already there
if [ ! -d ".git" ]; then
    echo "Cloning OpenLibrary repository..."
    git clone https://github.com/internetarchive/openlibrary.git .
fi

# 3. Setup the specific task state (from task.yaml)
echo "Setting up task state..."
git reset --hard 84cc4ed5697b83a849e9106a09bfed501169cc20
git clean -fd

# 4. Checkout the specific file needed for testing
git checkout c4eebe6677acc4629cb541a98d5e91311444f5d4 -- openlibrary/tests/core/test_imports.py

echo "Environment setup complete."
