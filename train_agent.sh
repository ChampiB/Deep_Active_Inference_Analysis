#!/bin/sh

source "$1/venv/bin/activate"

python3 "$1/train_agent.py" '$2' '$3'
