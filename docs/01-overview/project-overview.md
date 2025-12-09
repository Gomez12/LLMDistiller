# Project Overview

## 🎯 Project Doelen

De LLM Distiller is ontworpen om high-quality datasets te creëren voor het fine-tunen van kleinere taalmodellen. Het systeem distilleert kennis van grote LLMs (zoals GPT-4) naar gestructureerde datasets die gebruikt kunnen worden voor training van gespecialiseerde, kleinere modellen.

## 📋 Scope en Functionaliteiten

### Core Functionaliteiten
1. **Data Import**: Importeer vragen uit diverse bronnen (CSV, JSON, XML, databases)
2. **LLM Processing**: Verwerk vragen met meerdere LLM providers
3. **Response Validatie**: Valideer antwoorden tegen JSON schemas
4. **Quality Control**: Handmatige validatie van antwoordkwaliteit
5. **Dataset Export**: Exporteer datasets voor fine-tuning doeleinden

### Ondersteunde Data Formaten
- **Input**: CSV, JSON, XML, SQL databases
- **Output**: JSONL, CSV, JSON (voor fine-tuning)
- **Validation**: JSON schema validatie

### Target Gebruikers
- **ML Engineers**: Die datasets nodig hebben voor model training
- **Data Scientists**: Die knowledge distillation willen toepassen
- **Researchers**: Die gespecialiseerde modellen willen trainen
- **Development Teams**: Die domain-specifieke chatbots bouwen

## 🏗️ Systeem Architectuur

### Hoofdcomponenten
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Import   │───▶│   Database      │───▶│   LLM Client    │
│   Modules       │    │   (SQLite)      │    │   (Multi-Provider)│
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Validation    │    │   Rate Limiting │    │   Export        │
│   Engine        │    │   System        │    │   Modules       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Data Flow
1. **Import**: Vragen worden geïmporteerd uit diverse bronnen
2. **Storage**: Vragen worden opgeslagen in SQLite database
3. **Processing**: Onbeantwoorde vragen worden naar LLM providers gestuurd
4. **Validation**: Antwoorden worden gevalideerd tegen JSON schemas
5. **Quality Control**: Handmatige validatie via `is_correct` veld
6. **Export**: Geldige antwoorden worden geëxporteerd als training dataset

## 🔧 Technologie Stack

### Backend
- **Python 3.9+**: Hoofdaal programmeertaal
- **SQLAlchemy**: ORM voor database abstractie
- **Alembic**: Database migrations
- **Pydantic**: Data validatie en settings management

### Database
- **SQLite**: Primaire database (lichtgewicht, portable)
- **Future-ready**: Ondersteuning voor PostgreSQL, SQL Server

### LLM Integration
- **OpenAI SDK**: Primaire LLM client
- **Multi-provider**: Ondersteuning voor diverse OpenAI-compatible endpoints
- **Rate Limiting**: Configurable throttling met API-aware logic

### CLI & Interface
- **Click**: Command-line interface framework
- **Future**: Gradio web interface voor validatie

## 📊 Data Model

### Core Entities
- **Questions**: De vragen die verwerkt moeten worden
- **Responses**: LLM antwoorden met metadata
- **Invalid Responses**: Antwoorden die schema validatie faalden
- **Validation**: Handmatige validatie resultaten

### Key Velden
- **json_id**: Externe identifier voor traceerbaarheid
- **category**: Vraag categorisatie
- **golden_answer**: Referentie antwoord (optioneel)
- **answer_schema**: JSON schema voor response validatie
- **is_correct**: Handmatige validatie flag (NULL = niet gevalideerd)

## 🎯 Use Cases

### 1. Domain-Specific Chatbots
Train gespecialiseerde chatbots voor specifieke domeinen:
- Medische vraagbaak
- Juridische assistent
- Technische support bot

### 2. Model Compression
Creëer kleinere, snellere modellen:
- Mobile deployment
- Edge computing
- Cost reduction

### 3. Knowledge Distillation
Breng kennis over van grote naar kleine modellen:
- Teacher-student training
- Multi-model learning
- Performance optimization

## 🚀 Toekomstige Ontwikkeling

### Fase 1: Core Implementation
- [x] Database schema en models
- [x] Multi-provider LLM support
- [x] JSON schema validatie
- [x] CLI interface
- [x] Processing engine met queue management
- [x] Rate limiting en retry logic
- [x] Parallel processing capabilities

### Fase 2: Enhanced Features
- [ ] Gradio web interface
- [ ] Advanced analytics
- [x] Batch optimization
- [ ] Custom model support

### Fase 3: Enterprise Features
- [ ] Multi-user support
- [ ] Role-based access
- [ ] API endpoints
- [ ] Cloud deployment

## 📈 Success Metrics

### KPI's
- **Dataset Quality**: Percentage correct gevalideerde antwoorden
- **Processing Speed**: Vragen per minuut verwerkt
- **Cost Efficiency**: Kosten per verwerkte vraag
- **Model Performance**: Verbetering in fine-tuned modellen

### Monitoring
- Response validation rates
- API usage en costs
- Processing bottlenecks
- Error rates en recovery

---

*Dit document dient als leidraad voor het begrijpen van het project, zijn doelen en de technische architectuur.*