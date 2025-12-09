git fetch origin
git reset --hard origin/main
uv pip install -r requirements.txt
uv pip uninstall llm-distiller
uv pip install -e .
rm -f dataset.jsonl
llm-distiller init
llm-distiller import csv questions.csv
llm-distiller process --limit 2
llm-distiller export --validated-only --output dataset.jsonl

