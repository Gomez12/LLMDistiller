# CLI Reference

Dit document beschrijft het complete command-line interface van de LLM Distiller, inclusief alle commands, opties en voorbeelden.

## 📋 Overzicht

De CLI is opgebouwd met Click en volgt een hiërarchische structuur:

```bash
llm-distiller [GLOBAL_OPTIONS] COMMAND [SUBCOMMAND] [OPTIONS]
```

### Global Options
```bash
--config PATH        Pad naar configuratie bestand (default: ./config/config.json)
--verbose, -v        Uitgebreide logging
--quiet, -q          Minimale output
--help, -h           Toon help bericht
--version            Toon versie informatie
```

## 🏠 Init Command

Initialiseer een nieuwe LLM Distiller omgeving.

```bash
llm-distiller init [OPTIONS]
```

### Options
```bash
--config-path PATH    Configuratie directory (default: ./config)
--database-url URL    Database URL (default: sqlite:///llm_distiller.db)
--force               Overschrijf bestaande configuratie
--example-config      Genereer voorbeeld configuratie
```

### Voorbeelden
```bash
# Initialiseer met defaults
llm-distiller init

# Initialiseer met custom pad
llm-distiller init --config-path ./my-config

# Initialiseer met PostgreSQL
llm-distiller init --database-url "postgresql://user:pass@host/db"

# Genereer voorbeeld configuratie
llm-distiller init --example-config
```

### Output
```
✓ Created config directory: ./config
✓ Generated configuration file: ./config/config.json
✓ Initialized database: sqlite:///llm_distiller.db
✓ Created logs directory: ./logs
✓ Setup complete! Run 'llm-distiller import --help' to get started.
```

## 📥 Import Commands

Importeer data uit diverse bronnen.

### CSV Import
```bash
llm-distiller import csv [OPTIONS] FILE_PATH
```

#### Options
```bash
--mapping PATH        JSON mapping file voor kolom namen
--delimiter CHAR      CSV delimiter (default: ,)
--encoding TEXT       File encoding (default: utf-8)
--default-correct TEXT  Default waarde voor is_correct (null/true/false)
--batch-size INTEGER  Batch size voor import (default: 1000)
--dry-run             Toon wat geïmporteerd zou worden
```

#### Voorbeeld CSV Format
```csv
json_id,category,question,golden_answer,answer_schema
1,math,"What is 2+2?","4","{\"type\": \"object\", \"properties\": {\"answer\": {\"type\": \"number\"}}}"
2,science,"What is H2O?","Water","{\"type\": \"object\", \"properties\": {\"answer\": {\"type\": \"string\"}}}"
```

#### Custom Mapping File
```json
{
  "json_id": "external_id",
  "category": "type",
  "question": "prompt",
  "golden_answer": "reference",
  "answer_schema": "schema"
}
```

#### Voorbeelden
```bash
# Basis CSV import
llm-distiller import csv questions.csv

# Import met custom mapping
llm-distiller import csv questions.csv --mapping mapping.json

# Import met default correct=true
llm-distiller import csv questions.csv --default-correct true

# Dry run om te testen
llm-distiller import csv questions.csv --dry-run
```

### JSON Import
```bash
llm-distiller import json [OPTIONS] FILE_PATH
```

#### Options
```bash
--path TEXT          JSONPath naar vragen array (default: $.questions)
--default-correct TEXT  Default waarde voor is_correct
--batch-size INTEGER  Batch size (default: 1000)
--dry-run             Toon preview
```

#### Voorbeeld JSON Format
```json
{
  "questions": [
    {
      "json_id": "1",
      "category": "math",
      "question": "What is 2+2?",
      "golden_answer": "4",
      "answer_schema": "{\"type\": \"object\", \"properties\": {\"answer\": {\"type\": \"number\"}}}"
    }
  ]
}
```

#### Voorbeelden
```bash
# Basis JSON import
llm-distiller import json questions.json

# Import met custom JSONPath
llm-distiller import json data.json --path "$.data.questions"

# Import met default correct=null
llm-distiller import json questions.json --default-correct null
```

### XML Import
```bash
llm-distiller import xml [OPTIONS] FILE_PATH
```

#### Options
```bash
--xpath TEXT         XPath naar vraag elements (default: //question)
--default-correct TEXT  Default waarde voor is_correct
--batch-size INTEGER  Batch size (default: 1000)
--dry-run             Toon preview
```

#### Voorbeeld XML Format
```xml
<questions>
  <question>
    <json_id>1</json_id>
    <category>math</category>
    <question_text>What is 2+2?</question_text>
    <golden_answer>4</golden_answer>
    <answer_schema>{"type": "object", "properties": {"answer": {"type": "number"}}}</answer_schema>
  </question>
</questions>
```

#### Voorbeelden
```bash
# Basis XML import
llm-distiller import xml questions.xml

# Import met custom XPath
llm-distiller import xml data.xml --xpath "//data/question"
```

### Database Import
```bash
llm-distiller import db [OPTIONS] CONNECTION_STRING
```

#### Options
```bash
--query TEXT          SQL query om data te selecteren
--mapping PATH        Column mapping file
--default-correct TEXT  Default waarde voor is_correct
--batch-size INTEGER  Batch size (default: 1000)
--dry-run             Toon preview
```

#### Voorbeelden
```bash
# Import uit PostgreSQL
llm-distiller import db "postgresql://user:pass@host/db" --query "SELECT * FROM questions"

# Import met mapping
llm-distiller import db "mysql://user:pass@host/db" --mapping db_mapping.json

# Import uit SQL Server
llm-distiller import db "mssql://user:pass@host/db" --query "SELECT id as json_id, category, question_text FROM questions"
```

## 🤖 Process Commands

Verwerk vragen met LLM providers.

### Process Questions
```bash
llm-distiller process [OPTIONS]
```

#### Options
```bash
--category TEXT       Filter by category
--limit INTEGER       Number of questions to process (default: 10)
--provider TEXT       LLM provider to use
```

#### Voorbeelden
```bash
# Verwerk 10 vragen met default settings
llm-distiller process --limit 10

# Verwerk specifieke categorie
llm-distiller process --category math

# Verwerk met specifieke provider
llm-distiller process --provider openai --limit 5

# Combineer filters
llm-distiller process --category science --limit 20 --provider gpt4
```

#### Processing Features
- **Parallel Processing**: Verwerkt vragen in batches (configurable batch size)
- **Rate Limiting**: Respecteert API rate limits per provider
- **Retry Logic**: Automatische retries met exponential backoff
- **Multi-Provider Support**: Failover tussen providers
- **JSON Schema Validation**: Valideert responses tegen schema
- **Progress Tracking**: Real-time voortgang en statistieken
- **Error Handling**: Gedetailleerde error reporting
- **Provider Logging**: Volledige logging van provider selectie en gebruik op INFO niveau

#### Output Example
```
Processing 10 questions...
Using provider: openai_main
✅ Processing completed successfully!
📊 Results:
   Total questions: 10
   Processed: 10
   Successful: 8
   Failed: 2
   Invalid: 1
   Processing time: 15.2s
   Speed: 0.7 questions/sec
   Total tokens: 12,450
   Avg tokens/question: 1,245
```

#### Provider Logging
De process command toont gedetailleerde logging over provider selectie en gebruik:

**CLI Output:**
- `Using provider: [provider]` - Wanneer specifieke provider is opgegeven
- `No provider specified, will use load balancing across: [providers]` - Wanneer geen provider is opgegeven
- `Warning: No providers configured` - Wanneer er geen providers zijn geconfigureerd

**Log Output (INFO niveau):**
- `Using specified provider: [provider]` - Provider selectie in engine
- `No provider specified, will use load balancing across: [providers]` - Load balancing actief
- `Processing question [id] with provider: [provider]` - Start verwerking
- `Successfully generated response using provider: [provider] (model: [model])` - Succesvolle response
- `Provider [provider] failed: [error]` - Provider fout
- `All providers failed. Last error: [error]` - Alle providers gefaald

**Voorbeeld met logging:**
```
Processing 1 questions...
Using provider: local_ollama
2025-12-09 13:45:04,618 - src.processing.engine - INFO - Using specified provider: local_ollama
2025-12-09 13:45:04,720 - src.processing.manager - INFO - Successfully generated response using provider: local_ollama (model: llama2)
2025-12-09 13:45:04,721 - src.processing.worker - INFO - Processing question 1 with provider: local_ollama
2025-12-09 13:45:04,722 - src.processing.worker - INFO - Successfully processed question 1 with provider local_ollama
```

### Process Status
```bash
llm-distiller process status [OPTIONS]
```

#### Options
```bash
--provider TEXT       Filter op provider
--category TEXT       Filter op categorie
--format TEXT         Output format (table/json/csv)
```

#### Voorbeelden
```bash
# Toon verwerkingsstatus
llm-distiller process status

# Status per provider
llm-distiller process status --provider openai_main

# Status in JSON format
llm-distiller process status --format json

# Status per categorie
llm-distiller process status --category math
```

## ✅ Validate Commands

Valideer en beoordeel antwoorden.

### Set Validation
```bash
llm-distiller validate set [OPTIONS] QUESTION_ID
```

#### Options
```bash
--correct             Markeer als correct
--incorrect           Markeer als incorrect
--response-id INTEGER Specifieke response ID
--model TEXT          Filter op model
--reason TEXT         Reden voor beoordeling
```

#### Voorbeelden
```bash
# Markeer vraag als correct
llm-distiller validate set 123 --correct

# Markeer specifieke response als incorrect
llm-distiller validate set 123 --incorrect --response-id 456

# Markeer met reden
llm-distiller validate set 123 --correct --reason "Perfect answer"

# Valideer alle responses van model
llm-distiller validate set 123 --correct --model gpt-4
```

### Batch Validation
```bash
llm-distiller validate batch [OPTIONS] FILE_PATH
```

#### Options
```bash
--format TEXT         Input format (csv/json)
--delimiter CHAR      CSV delimiter (default: ,)
--dry-run             Toon preview
```

#### Voorbeeld CSV Format
```csv
question_id,response_id,is_correct,reason
123,456,true,"Good answer"
124,457,false,"Incorrect calculation"
```

#### Voorbeelden
```bash
# Valideer batch uit CSV
llm-distiller validate batch validations.csv

# Valideer batch uit JSON
llm-distiller validate batch validations.json --format json

# Dry run
llm-distiller validate batch validations.csv --dry-run
```

### Validation Report
```bash
llm-distiller validate report [OPTIONS]
```

#### Options
```bash
--provider TEXT       Filter op provider
--category TEXT       Filter op categorie
--format TEXT         Output format (table/json/csv)
--output PATH         Schrijf naar bestand
```

#### Voorbeelden
```bash
# Toon validatie rapport
llm-distiller validate report

# Rapport per provider
llm-distiller validate report --provider openai_main

# Exporteer naar CSV
llm-distiller validate report --format csv --output validation_report.csv
```

## 📤 Export Commands

Exporteer datasets voor fine-tuning.

### Export Dataset
```bash
llm-distiller export [OPTIONS]
```

#### Options
```bash
--format TEXT         Output format (jsonl/csv/json) (default: jsonl)
--output PATH         Output bestand (default: stdout)
--validated-only      Exporteer alleen gevalideerde antwoorden
--category TEXT       Filter op categorie
```

#### Voorbeelden
```bash
# Exporteer alle gevalideerde antwoorden als JSONL
llm-distiller export --validated-only --output dataset.jsonl

# Exporteer per categorie
llm-distiller export --category math --format csv --output math_dataset.csv

# Exporteer alle data
llm-distiller export --output all_data.jsonl
```

### Export Invalid Responses
```bash
llm-distiller export invalid [OPTIONS]
```

#### Options
```bash
--format TEXT         Output format (jsonl/csv/json) (default: jsonl)
--output PATH         Output bestand
--error-type TEXT     Filter op error type
--provider TEXT       Filter op provider
--category TEXT       Filter op categorie
```

#### Voorbeelden
```bash
# Exporteer alle invalid responses
llm-distiller export invalid --output invalid_responses.jsonl

# Exporteer specifieke error types
llm-distiller export invalid --error-type SCHEMA_VALIDATION_ERROR

# Exporteer per provider
llm-distiller export invalid --provider openai_main --format csv
```

## 📊 Stats Commands

Toon statistieken en rapporten.

### Database Statistics
```bash
llm-distiller stats db [OPTIONS]
```

#### Options
```bash
--format TEXT         Output format (table/json)
--category TEXT       Filter op categorie
```

#### Voorbeelden
```bash
# Toon database statistieken
llm-distiller stats db

# Statistieken per categorie
llm-distiller stats db --category math

# JSON output
llm-distiller stats db --format json
```

### Model Performance
```bash
llm-distiller stats model [OPTIONS]
```

#### Options
```bash
--provider TEXT       Filter op provider
--model TEXT          Filter op model
--category TEXT       Filter op categorie
--format TEXT         Output format (table/json/csv)
```

#### Voorbeelden
```bash
# Model performance overzicht
llm-distiller stats model

# Performance per provider
llm-distiller stats model --provider openai_main

# Exporteer naar CSV
llm-distiller stats model --format csv --output model_stats.csv
```

### Validation Statistics
```bash
llm-distiller stats validation [OPTIONS]
```

#### Options
```bash
--provider TEXT       Filter op provider
--category TEXT       Filter op categorie
--format TEXT         Output format (table/json)
```

#### Voorbeelden
```bash
# Validatie statistieken
llm-distiller stats validation

# Per provider
llm-distiller stats validation --provider openai_main
```

## 🔧 Config Commands

Beheer configuratie.

### Show Config
```bash
llm-distiller config show [OPTIONS]
```

#### Options
```bash
--provider TEXT       Toon specifieke provider
--mask-secrets        Maskeer API keys
--format TEXT         Output format (json/yaml)
```

#### Voorbeelden
```bash
# Toon volledige configuratie
llm-distiller config show

# Toon specifieke provider
llm-distiller config show --provider openai_main

# Maskeer sensitive data
llm-distiller config show --mask-secrets

# YAML output
llm-distiller config show --format yaml
```

### Test Config
```bash
llm-distiller config test [OPTIONS]
```

#### Options
```bash
--provider TEXT       Test specifieke provider
--connection-only     Test alleen database connectie
```

#### Voorbeelden
```bash
# Test complete configuratie
llm-distiller config test

# Test specifieke provider
llm-distiller config test --provider openai_main

# Test alleen database
llm-distiller config test --connection-only
```

## 🧹 Maintenance Commands

Database onderhoud en cleanup.

### Cleanup
```bash
llm-distiller maintenance cleanup [OPTIONS]
```

#### Options
```bash
--invalid-older-than DAYS  Verwijder oude invalid responses (default: 30)
--dry-run             Toon wat verwijderd zou worden
--confirm             Bevestig verwijdering
```

#### Voorbeelden
```bash
# Verwijder oude invalid responses
llm-distiller maintenance cleanup --invalid-older-than 30

# Dry run
llm-distiller maintenance cleanup --dry-run

# Met bevestiging
llm-distiller maintenance cleanup --confirm
```

### Vacuum Database
```bash
llm-distiller maintenance vacuum [OPTIONS]
```

#### Options
```bash
--analyze             Voer ANALYZE uit na VACUUM
--full                Full vacuum (exclusieve lock)
```

#### Voorbeelden
```bash
# Basis vacuum
llm-distiller maintenance vacuum

# Vacuum met analyze
llm-distiller maintenance vacuum --analyze

# Full vacuum
llm-distiller maintenance vacuum --full
```

## 🔍 Search Commands

Zoek in vragen en antwoorden.

### Search Questions
```bash
llm-distiller search questions [OPTIONS] QUERY
```

#### Options
```bash
--category TEXT       Filter op categorie
--has-schema          Alleen vragen met schema
--limit INTEGER       Maximum resultaten (default: 20)
--format TEXT         Output format (table/json)
```

#### Voorbeelden
```bash
# Zoek vragen
llm-distiller search questions "mathematics"

# Zoek in categorie
llm-distiller search questions "calculus" --category math

# Alleen vragen met schema
llm-distiller search questions "JSON" --has-schema
```

### Search Responses
```bash
llm-distiller search responses [OPTIONS] QUERY
```

#### Options
```bash
--provider TEXT       Filter op provider
--model TEXT          Filter op model
--correct-only        Alleen correcte antwoorden
--limit INTEGER       Maximum resultaten (default: 20)
--format TEXT         Output format (table/json)
```

#### Voorbeelden
```bash
# Zoek antwoorden
llm-distiller search responses "derivative"

# Zoek correcte antwoorden
llm-distiller search responses "integral" --correct-only

# Per provider
llm-distiller search responses "theorem" --provider openai_main
```

## 🚨 Error Codes

De CLI gebruikt de volgende exit codes:

| Code | Betekenis |
|------|-----------|
| 0    | Success |
| 1    | General error |
| 2    | Configuration error |
| 3    | Database error |
| 4    | API error |
| 5    | Validation error |
| 6    | File not found |
| 7    | Permission denied |
| 8    | Network error |

## 📝 Output Formats

### Table Format
```
┌─────┬─────────────┬──────────┬─────────────┐
│ ID  │ Category    │ Question │ Responses  │
├─────┼─────────────┼──────────┼─────────────┤
│ 1   │ math        │ 2+2=?    │ 3          │
│ 2   │ science     │ H2O=?    │ 2          │
└─────┴─────────────┴──────────┴─────────────┘
```

### JSON Format
```json
{
  "total": 2,
  "items": [
    {
      "id": 1,
      "category": "math",
      "question": "What is 2+2?",
      "response_count": 3
    }
  ]
}
```

### CSV Format
```csv
id,category,question,response_count
1,math,"What is 2+2?",3
2,science,"What is H2O?",2
```

---

*Deze CLI reference biedt een compleet overzicht van alle beschikbare commands en opties in de LLM Distiller.*