#!/bin/bash
set -euo pipefail
mkdir -p /logs/verifier
printf '0.0\n' > /logs/verifier/reward.txt
python /tests/verify.py
