# Design Decisions

Dit document beschrijft de belangrijkste architecturale en technische beslissingen die zijn genomen tijdens het ontwerp van de LLM Distiller. Elke beslissing wordt onderbouwd met de afwegingen en alternatieven die zijn overwogen.

## 📋 Inhoudsopgave

1. [Database Keuzes](#database-keuzes)
2. [Configuratie Management](#configuratie-management)
3. [LLM Provider Architectuur](#llm-provider-architectuur)
4. [Validatie Strategie](#validatie-strategie)
5. [Rate Limiting Aanpak](#rate-limiting-aanpak)
6. [CLI-First Benadering](#cli-first-benadering)
7. [Error Handling Strategie](#error-handling-strategie)
8. [Testing Philosophie](#testing-philosophie)

---

## 🗄️ Database Keuzes

### Beslissing: SQLite als Primaire Database

**Waarom SQLite?**
- **Zero-config**: Geen externe database server nodig
- **Portable**: Eén bestand dat makkelijk te backuppen en delen is
- **Performance**: Uitstekend voor read-heavy workloads
- **ACID compliance**: Volledige transactionele ondersteuning
- **Python integration**: Uitstekende SQLAlchemy ondersteuning

**Overwogen Alternatieven:**
- **PostgreSQL**: Meer features, maar vereist externe setup
- **DuckDB**: Sneller voor analytics, maar minder mature voor OLTP
- **MongoDB**: Flexibeler schema, maar minder geschikt voor gestructureerde data

**Toekomstbestendigheid:**
```python
# SQLAlchemy maakt migratie naar andere databases eenvoudig
class DatabaseConfig(BaseModel):
    url: str = "sqlite:///llm_distiller.db"  # Default SQLite
    # Kan later worden: "postgresql://user:pass@host/db"
```

### Beslissing: Twee-tabel Validatie Strategie

**Waarom aparte `invalid_responses` tabel?**
- **Performance**: Valid responses query blijft snel
- **Debugging**: Gedetailleerde error tracking zonder main tabel te vervuilen
- **Analytics**: Makkelijk analyse van validation patterns
- **Reprocessing**: Failed responses kunnen later opnieuw verwerkt worden

**Alternatief overwogen:**
- **Status veld in responses tabel**: Minder complex, maar minder flexibel voor error details

---

## ⚙️ Configuratie Management

### Beslissing: JSON Configuratie met Environment Variable Fallback

**Waarom JSON?**
- **Human readable**: Makkelijker te lezen dan YAML voor complexe nested structures
- **Standard**: Native support in Python, geen extra dependencies nodig
- **Validation**: Makkelijk te valideren met JSON Schema
- **Version control**: Git-friendly formaat

**Environment Variable Pattern:**
```python
def get_api_key(self, provider_name: str) -> str:
    """Get API key with fallback to environment variables"""
    if self.api_key:
        return self.api_key
    
    env_var = f"{provider_name.upper()}_API_KEY"
    return os.getenv(env_var, "")
```

**Waarom deze fallback strategie?**
- **Security**: Sensitive data niet in config files
- **Flexibility**: Lokale development vs production deployment
- **CI/CD**: Makkelijk integration met deployment pipelines

**Overwogen Alternatieven:**
- **Alleen environment variables**: Minder overzichtelijk voor complexe config
- **Encrypted config files**: Extra complexiteit, beveiligingsrisico's
- **External secret management**: Overkill voor huidige scope

---

## 🤖 LLM Provider Architectuur

### Beslissing: OpenAI-Compatible Interface

**Waarom OpenAI SDK als basis?**
- **Standard**: De facto standard voor LLM APIs
- **Ecosystem**: Meeste providers ondersteunen OpenAI-compatible endpoints
- **Features**: Retry logic, rate limiting, error handling ingebouwd
- **Documentation**: Uitstekende documentatie en community support

**Provider Abstraction:**
```python
class OpenAIProvider(BaseLLMProvider):
    """OpenAI-compatible provider implementation"""
    
    def __init__(self, config: ProviderConfig):
        self.client = AsyncOpenAI(
            api_key=config.get_api_key(),
            base_url=config.base_url
        )
```

**Ondersteunde Providers:**
- **OpenAI Cloud**: Officiële OpenAI API
- **Local Ollama**: Lokale modellen via OpenAI-compatible endpoint
- **Azure OpenAI**: Microsoft's OpenAI offering
- **Custom endpoints**: Elke OpenAI-compatible API

**Overwogen Alternatieven:**
- **Provider-specifieke SDKs**: Meer complexiteit, onderhoud
- **HTTP client met custom logic**: Meer werk, minder features
- **LangChain integration**: Overkill voor huidige requirements

---

## ✅ Validatie Strategie

### Beslissing: JSON Schema Validatie met Error Tracking

**Waarom JSON Schema?**
- **Standard**: Industry standard voor JSON validatie
- **Expressive**: Krachtig genoeg voor complexe structuren
- **Tooling**: Uitstekende Python libraries (jsonschema)
- **Documentation**: Schema dient als documentatie

**Validatie Flow:**
```python
def validate_response(self, response: str, schema: dict) -> ValidationResult:
    try:
        data = json.loads(response)
        jsonschema.validate(data, schema)
        return ValidationResult(valid=True, data=data)
    except json.JSONDecodeError as e:
        return ValidationResult(valid=False, error=f"Invalid JSON: {e}")
    except jsonschema.ValidationError as e:
        return ValidationResult(valid=False, error=f"Schema validation failed: {e.message}")
```

**Waarom gedetailleerde error tracking?**
- **Debugging**: Precieze locatie van validatie fouten
- **Schema improvement**: Inzicht in schema problemen
- **Quality metrics**: Track validation success rates
- **Reprocessing**: Failed responses kunnen later opnieuw verwerkt worden

**Overwogen Alternatieven:**
- **Pydantic validatie**: Meer Python-specific, minder standard
- **Custom validatie**: Meer werk, minder robust
- **Geen validatie**: Risico op corrupte data

---

## 🚦 Rate Limiting Aanpak

### Beslissing: Adaptive Rate Limiting met API Feedback

**Waarom adaptive rate limiting?**
- **API variability**: Verschillende providers hebben verschillende limits
- **Dynamic limits**: API limits kunnen veranderen
- **Efficiency**: Maximaliseer throughput zonder limits te overschrijden
- **Resilience**: Graceful handling van rate limit changes

**Twee-laagse Aanpak:**
```python
class AdaptiveRateLimiter:
    def __init__(self, config_limits: Dict):
        self.config_limits = config_limits  # User-defined maximums
        self.api_limits = {}  # API-derived limits
    
    async def acquire(self, provider_name: str):
        # Check both config and API limits
        config_wait = self._calculate_config_wait(provider_name)
        api_wait = self._calculate_api_wait(provider_name)
        return max(config_wait, api_wait)
```

**Config-based Limits:**
- **Safety**: Voorkomt onverwachte kosten
- **Predictability**: Controleerbare throughput
- **Budget management**: Kostenbeheersing

**API-aware Limits:**
- **Retry-After headers**: Respecteert API feedback
- **429 responses**: Leert van rate limit errors
- **Dynamic adjustment**: Past zich aan aan API conditions

**Overwogen Alternatieven:**
- **Fixed rate limiting**: Simpeler, minder efficient
- **Token bucket algorithm**: Complexer, meer overhead
- **Geen rate limiting**: Risico op API bans

---

## 💻 CLI-First Benadering

### Beslissing: Click Framework voor CLI

**Waarom Click?**
- **Composable**: Makkelijk command nesting en subcommands
- **Type hints**: Automatische type conversie en validatie
- **Help generation**: Automatische help en usage info
- **Testing**: Uitstekende test support
- **Extensibility**: Makkelijk uit te breiden met nieuwe commands

**Command Structuur:**
```bash
llm-distiller import csv --file questions.csv --default-correct null
llm-distiller process --provider openai_main --limit 100
llm-distiller export --format jsonl --output dataset.jsonl
```

**Waarom CLI-first?**
- **Automation**: Makkelijk te integreren in CI/CD pipelines
- **Scripting**: Composeerbare workflows
- **Remote usage**: SSH en remote server support
- **Resource efficiency**: Geen GUI overhead
- **Future-proof**: Kan later uitgebreid worden met web interface

**Overwogen Alternatieven:**
- **argparse**: Meer boilerplate, minder features
- **Web interface eerst**: Meer complexiteit, deployment overhead
- **GUI applicatie**: Platform-specifiek, meer onderhoud

---

## 🛡️ Error Handling Strategie

### Beslissing: Layered Error Handling met Retry Logic

**Waarom layered error handling?**
- **Separation of concerns**: Different layers handle different errors
- **Recovery**: Automatic recovery van transient errors
- **Debugging**: Gedetailleerde error context
- **User experience**: Meaningful error messages

**Error Hierarchy:**
```python
class LLMDistillerError(Exception):
    """Base exception for all LLM Distiller errors"""

class ConfigurationError(LLMDistillerError):
    """Configuration-related errors"""

class APIError(LLMDistillerError):
    """LLM provider API errors"""

class ValidationError(LLMDistillerError):
    """Response validation errors"""
```

**Retry Strategy:**
- **Exponential backoff**: Progressief langere wachttijden
- **Jitter**: Voorkomt thundering herd problems
- **Max retries**: Beperkt aantal pogingen
- **Circuit breaker**: Slaat mislukte providers over

**Overwogen Alternatieven:**
- **Fail fast**: Minder robust, slechte user experience
- **Manual intervention**: Meer overhead, niet scalable
- **Geen error handling**: Risico op data corruption

---

## 🧪 Testing Philosophie

### Beslissing: Pytest met Mocking Strategy

**Waarom Pytest?**
- **Fixtures**: Flexible test setup en teardown
- **Parametrization**: Makkelijk testen met verschillende inputs
- **Plugins**: Rijk ecosysteem voor extra features
- **Async support**: Uitstekende async testing support
- **Coverage**: Geïntegreerde coverage reporting

**Mocking Strategy:**
```python
@pytest.fixture
def mock_openai_client():
    with patch('openai.AsyncOpenAI') as mock:
        mock.return_value.chat.completions.create.return_value = MockResponse(
            content="Test response"
        )
        yield mock
```

**Testing Layers:**
- **Unit tests**: Test individuele componenten in isolatie
- **Integration tests**: Test component interacties
- **End-to-end tests**: Test complete workflows
- **Performance tests**: Test onder load conditions

**Test Data Strategy:**
- **Fixtures**: Reusable test data
- **Factories**: Dynamic test data generation
- **Factories**: Realistische test scenarios
- **Isolation**: Tests niet afhankelijk van externe services

**Overwogen Alternatieven:**
- **Unittest**: Minder features, meer boilerplate
- **Doctest**: Beperkt tot simple cases
- **Geen automated testing**: Hoog risico op regressies

---

## 📈 Impact van Design Decisions

### Positieve Impact
- **Maintainability**: Duidelijke scheiding van verantwoordelijkheden
- **Scalability**: Architectuur ondersteunt groei
- **Flexibility**: Makkelijk uitbreidbaar voor nieuwe features
- **Reliability**: Robuste error handling en recovery
- **Developer Experience**: Goede tooling en documentation

### Trade-offs
- **Complexiteit**: Meer initiële setup dan simpele oplossing
- **Learning Curve**: Nieuwe teamleden moeten architecture leren
- **Dependencies**: Meer externe dependencies dan minimal approach
- **Performance**: Extra abstraction layers kunnen overhead toevoegen

### Mitigation Strategies
- **Documentation**: Uitgebreide documentatie en examples
- **Examples**: Concrete use cases en quick start guides
- **Testing**: Hoge test coverage voor betrouwbaarheid
- **Monitoring**: Performance monitoring en optimization

---

*Deze design decisions zijn gemaakt met oog op de lange termijn: een systeem dat niet alleen voldoet aan de huidige requirements, maar ook meegroeit met toekomstige behoeften en schaalt met groeiend gebruik.*