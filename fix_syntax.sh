#!/bin/bash
cd frontend

# Find all files with syntax errors
echo "Finding broken files..."
BROKEN_FILES=()
for file in $(find src -name "*.ts" -o -name "*.tsx"); do
  if ! npx prettier --check "$file" >/dev/null 2>&1; then
    echo "Broken: $file"
    BROKEN_FILES+=("$file")
  fi
done

for file in "${BROKEN_FILES[@]}"; do
  echo "Fixing $file..."
  
  # Get all commits for this file
  COMMITS=$(git log --format="%H" -- "$file")
  
  for commit in $COMMITS; do
    git checkout $commit -- "$file"
    if npx prettier --check "$file" >/dev/null 2>&1; then
      echo "Found good version for $file at $commit"
      break
    fi
  done
done
