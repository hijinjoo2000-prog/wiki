#!/bin/bash
echo "=== Git Remote Sync ==="
echo "1. Pulling and merging from remote repository..."
git pull origin main --allow-unrelated-histories --no-rebase

echo "2. Pushing local changes to remote repository..."
git push origin main

echo "=== Sync Complete! ==="
