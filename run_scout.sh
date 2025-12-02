#!/bin/bash
cd ~/Adaptheon
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
python3 -m knowledge_scout.main "$@"
