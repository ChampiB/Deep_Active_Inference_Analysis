#!/bin/sh

DIRECTORY=$(dirname "$0")
SCRIPT="${DIRECTORY}/train_agent.py"

python3 $SCRIPT $*
