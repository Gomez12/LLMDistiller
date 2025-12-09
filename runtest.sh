git pull
uv pip install -r requirements.txt
uv pip uninstall llm-distiller
uv pip install -e .
rm dataset.jsonl
llm-distiller init
llm-distiller import csv questions.csv --default-correct null
llm-distiller process --limit 2
llm-distiller export --correct-only --output dataset.jsonl

