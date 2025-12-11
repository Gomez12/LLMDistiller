#git fetch origin
#git reset --hard origin/main
uv pip install -r requirements.txt
uv pip uninstall llm-distiller
uv pip install -e .
rm -f dataset.jsonl
llm-distiller init
llm-distiller import -t csv questions.csv --default-correct true
llm-distiller process --limit 20 --provider openai_main
#llm-distiller export --validated-only --output dataset.jsonl
llm-distiller export-training -o datasetclassification.jsonl --category classification
