# Data Importers

Dit document beschrijft de data import modules van de LLM Distiller, inclusief ondersteunde formaten, mapping configuratie en extensie mogelijkheden.

## 📋 Overzicht

De import system is ontworpen voor:
- **Flexibiliteit**: Ondersteuning voor diverse data formaten
- **Validatie**: Data validatie en error handling
- **Performance**: Batch processing voor grote datasets
- **Extensibility**: Makkelijk uitbreidbaar met nieuwe importers

## 🏗️ Importer Architecture

### Base Importer Interface
```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

class ImportResult:
    """Result of import operation"""
    
    def __init__(self):
        self.total_processed = 0
        self.success_count = 0
        self.error_count = 0
        self.errors = []
        self.warnings = []
        self.duplicates = []
    
    def add_success(self):
        self.success_count += 1
        self.total_processed += 1
    
    def add_error(self, error: str, row_data: Dict = None):
        self.error_count += 1
        self.total_processed += 1
        self.errors.append({
            'error': error,
            'row_data': row_data,
            'timestamp': datetime.now()
        })
    
    def add_warning(self, warning: str):
        self.warnings.append({
            'warning': warning,
            'timestamp': datetime.now()
        })
    
    def add_duplicate(self, identifier: str):
        self.duplicates.append(identifier)
    
    @property
    def success_rate(self) -> float:
        if self.total_processed == 0:
            return 0.0
        return self.success_count / self.total_processed

@dataclass
class QuestionData:
    """Normalized question data structure"""
    json_id: Optional[str] = None
    category: str = ""
    question_text: str = ""
    golden_answer: Optional[str] = None
    answer_schema: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class BaseImporter(ABC):
    """Abstract base class for all data importers"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.result = ImportResult()
    
    @abstractmethod
    async def validate_source(self, source: str) -> bool:
        """Validate if source is accessible and valid"""
        pass
    
    @abstractmethod
    async def extract_data(self, source: str) -> List[QuestionData]:
        """Extract and normalize data from source"""
        pass
    
    @abstractmethod
    async def store_data(self, data: List[QuestionData]) -> ImportResult:
        """Store extracted data in database"""
        pass
    
    async def import_data(self, source: str, dry_run: bool = False) -> ImportResult:
        """Complete import workflow"""
        # Validate source
        if not await self.validate_source(source):
            self.result.add_error(f"Invalid source: {source}")
            return self.result
        
        # Extract data
        try:
            data = await self.extract_data(source)
        except Exception as e:
            self.result.add_error(f"Data extraction failed: {e}")
            return self.result
        
        # Store data (unless dry run)
        if not dry_run:
            await self.store_data(data)
        else:
            self.result.success_count = len(data)
            self.result.total_processed = len(data)
        
        return self.result
    
    def normalize_field(self, value: Any, field_name: str) -> Any:
        """Normalize field value according to type"""
        if value is None:
            return None
        
        # Strip whitespace for string fields
        if isinstance(value, str):
            value = value.strip()
            if value == "":
                return None
        
        # JSON validation for schema fields
        if field_name == 'answer_schema' and value:
            try:
                json.loads(value)
            except json.JSONDecodeError:
                self.result.add_warning(f"Invalid JSON in answer_schema: {value}")
                return None
        
        return value
```

## 📄 CSV Importer

### CSV Importer Implementation
```python
import csv
import io
from typing import List, Dict, Optional
import chardet

class CSVImporter(BaseImporter):
    """Import questions from CSV files"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.delimiter = config.get('delimiter', ',')
        self.encoding = config.get('encoding', 'utf-8')
        self.field_mapping = config.get('mapping', {})
        self.default_correct = config.get('default_correct', None)
        self.batch_size = config.get('batch_size', 1000)
    
    async def validate_source(self, source: str) -> bool:
        """Validate CSV file accessibility and format"""
        try:
            # Check if file exists and is readable
            with open(source, 'rb') as f:
                # Detect encoding
                raw_data = f.read(10000)
                detected = chardet.detect(raw_data)
                self.encoding = detected.get('encoding', 'utf-8')
            
            # Validate CSV structure
            with open(source, 'r', encoding=self.encoding) as f:
                reader = csv.reader(f, delimiter=self.delimiter)
                headers = next(reader, [])
                
                # Check required columns
                required_columns = ['question', 'category']
                mapped_columns = [self.field_mapping.get(col, col) for col in headers]
                
                for required in required_columns:
                    if required not in mapped_columns:
                        self.result.add_error(f"Missing required column: {required}")
                        return False
            
            return True
            
        except Exception as e:
            self.result.add_error(f"CSV validation failed: {e}")
            return False
    
    async def extract_data(self, source: str) -> List[QuestionData]:
        """Extract and normalize data from CSV"""
        questions = []
        
        try:
            with open(source, 'r', encoding=self.encoding) as f:
                reader = csv.DictReader(f, delimiter=self.delimiter)
                
                for row_num, row in enumerate(reader, start=2):  # Start at 2 for CSV line numbers
                    try:
                        question_data = self._process_csv_row(row)
                        if question_data:
                            questions.append(question_data)
                    except Exception as e:
                        self.result.add_error(f"Row {row_num}: {e}", row)
                        continue
        
        except Exception as e:
            self.result.add_error(f"CSV reading failed: {e}")
        
        return questions
    
    def _process_csv_row(self, row: Dict[str, str]) -> Optional[QuestionData]:
        """Process single CSV row into QuestionData"""
        # Apply field mapping
        mapped_row = {}
        for csv_field, value in row.items():
            mapped_field = self.field_mapping.get(csv_field, csv_field)
            mapped_row[mapped_field] = value
        
        # Extract required fields
        question_text = self.normalize_field(mapped_row.get('question'), 'question_text')
        category = self.normalize_field(mapped_row.get('category'), 'category')
        
        if not question_text or not category:
            raise ValueError("Missing required fields: question or category")
        
        # Extract optional fields
        json_id = self.normalize_field(mapped_row.get('json_id'), 'json_id')
        golden_answer = self.normalize_field(mapped_row.get('golden_answer'), 'golden_answer')
        answer_schema = self.normalize_field(mapped_row.get('answer_schema'), 'answer_schema')
        
        return QuestionData(
            json_id=json_id,
            category=category,
            question_text=question_text,
            golden_answer=golden_answer,
            answer_schema=answer_schema,
            metadata={'source_row': row}
        )
    
    async def store_data(self, data: List[QuestionData]) -> ImportResult:
        """Store data in database with batch processing"""
        from src.database.connection import get_db_session
        from src.database.models import Question
        
        with get_db_session() as db:
            # Process in batches
            for i in range(0, len(data), self.batch_size):
                batch = data[i:i + self.batch_size]
                
                for question_data in batch:
                    try:
                        # Check for duplicates
                        existing = None
                        if question_data.json_id:
                            existing = db.query(Question).filter(
                                Question.json_id == question_data.json_id
                            ).first()
                        
                        if existing:
                            self.result.add_duplicate(question_data.json_id)
                            continue
                        
                        # Create new question
                        question = Question(
                            json_id=question_data.json_id,
                            category=question_data.category,
                            question_text=question_data.question_text,
                            golden_answer=question_data.golden_answer,
                            answer_schema=question_data.answer_schema
                        )
                        
                        db.add(question)
                        self.result.add_success()
                        
                    except Exception as e:
                        self.result.add_error(f"Database error: {e}", question_data.__dict__)
                        continue
        
        return self.result
```

### CSV Mapping Configuration
```json
{
  "json_id": "external_id",
  "category": "type",
  "question": "prompt",
  "golden_answer": "reference_answer",
  "answer_schema": "response_schema"
}
```

### CSV Format Examples

#### Standard Format
```csv
json_id,category,question,golden_answer,answer_schema
1,math,"What is 2+2?","4","{\"type\": \"object\", \"properties\": {\"answer\": {\"type\": \"number\"}}}"
2,science,"What is H2O?","Water","{\"type\": \"object\", \"properties\": {\"answer\": {\"type\": \"string\"}}}"
```

#### Custom Format with Mapping
```csv
external_id,type,prompt,reference_answer,response_schema
1,math,"Calculate: 2+2","4","{\"answer\": \"number\"}"
2,science,"Identify H2O","Water","{\"answer\": \"string\"}"
```

## 📄 JSON Importer

### JSON Importer Implementation
```python
import json
from jsonpath_ng import parse
from typing import List, Dict, Any

class JSONImporter(BaseImporter):
    """Import questions from JSON files"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.json_path = config.get('path', '$.questions')
        self.default_correct = config.get('default_correct', None)
        self.batch_size = config.get('batch_size', 1000)
    
    async def validate_source(self, source: str) -> bool:
        """Validate JSON file accessibility and structure"""
        try:
            with open(source, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Test JSONPath
            jsonpath_expr = parse(self.json_path)
            matches = jsonpath_expr.find(data)
            
            if not matches:
                self.result.add_error(f"No items found at JSONPath: {self.json_path}")
                return False
            
            # Validate structure of first match
            first_item = matches[0].value
            if not isinstance(first_item, dict):
                self.result.add_error("JSON items must be objects")
                return False
            
            # Check required fields
            required_fields = ['question', 'category']
            for field in required_fields:
                if field not in first_item:
                    self.result.add_error(f"Missing required field: {field}")
                    return False
            
            return True
            
        except json.JSONDecodeError as e:
            self.result.add_error(f"Invalid JSON: {e}")
            return False
        except Exception as e:
            self.result.add_error(f"JSON validation failed: {e}")
            return False
    
    async def extract_data(self, source: str) -> List[QuestionData]:
        """Extract questions from JSON using JSONPath"""
        questions = []
        
        try:
            with open(source, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Extract items using JSONPath
            jsonpath_expr = parse(self.json_path)
            matches = jsonpath_expr.find(data)
            
            for idx, match in enumerate(matches):
                try:
                    item_data = match.value
                    question_data = self._process_json_item(item_data, idx)
                    if question_data:
                        questions.append(question_data)
                except Exception as e:
                    self.result.add_error(f"Item {idx}: {e}", item_data)
                    continue
        
        except Exception as e:
            self.result.add_error(f"JSON processing failed: {e}")
        
        return questions
    
    def _process_json_item(self, item: Dict[str, Any], index: int) -> Optional[QuestionData]:
        """Process single JSON item into QuestionData"""
        # Extract required fields
        question_text = self.normalize_field(item.get('question'), 'question_text')
        category = self.normalize_field(item.get('category'), 'category')
        
        if not question_text or not category:
            raise ValueError("Missing required fields: question or category")
        
        # Extract optional fields
        json_id = self.normalize_field(item.get('json_id'), 'json_id')
        golden_answer = self.normalize_field(item.get('golden_answer'), 'golden_answer')
        answer_schema = self.normalize_field(item.get('answer_schema'), 'answer_schema')
        
        # Handle nested schema
        if answer_schema and isinstance(answer_schema, dict):
            answer_schema = json.dumps(answer_schema)
        
        return QuestionData(
            json_id=json_id,
            category=category,
            question_text=question_text,
            golden_answer=golden_answer,
            answer_schema=answer_schema,
            metadata={'source_index': index, 'source_item': item}
        )
```

### JSON Format Examples

#### Standard Format
```json
{
  "questions": [
    {
      "json_id": "1",
      "category": "math",
      "question": "What is 2+2?",
      "golden_answer": "4",
      "answer_schema": {
        "type": "object",
        "properties": {
          "answer": {"type": "number"}
        }
      }
    }
  ]
}
```

#### Nested Structure
```json
{
  "dataset": {
    "metadata": {
      "name": "Math Questions",
      "version": "1.0"
    },
    "data": {
      "questions": [
        {
          "id": "1",
          "type": "math",
          "prompt": "Calculate: 2+2",
          "reference": "4",
          "schema": {"answer": "number"}
        }
      ]
    }
  }
}
```

#### Custom JSONPath
```bash
# For nested structure above
llm-distiller import json data.json --path "$.dataset.data.questions"
```

## 📄 XML Importer

### XML Importer Implementation
```python
import xml.etree.ElementTree as ET
from lxml import etree
from typing import List, Dict, Any

class XMLImporter(BaseImporter):
    """Import questions from XML files"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.xpath = config.get('xpath', '//question')
        self.default_correct = config.get('default_correct', None)
        self.batch_size = config.get('batch_size', 1000)
        self.namespace = config.get('namespace', None)
    
    async def validate_source(self, source: str) -> bool:
        """Validate XML file accessibility and structure"""
        try:
            # Parse XML
            parser = etree.XMLParser(remove_blank_text=True)
            tree = etree.parse(source, parser)
            root = tree.getroot()
            
            # Test XPath
            if self.namespace:
                ns_map = {'ns': self.namespace}
                elements = root.xpath(self.xpath, namespaces=ns_map)
            else:
                elements = root.xpath(self.xpath)
            
            if not elements:
                self.result.add_error(f"No elements found at XPath: {self.xpath}")
                return False
            
            # Validate structure of first element
            first_element = elements[0]
            required_fields = ['question', 'category']
            
            for field in required_fields:
                field_element = first_element.find(f'.//{field}')
                if field_element is None or field_element.text is None:
                    self.result.add_error(f"Missing required field: {field}")
                    return False
            
            return True
            
        except etree.XMLSyntaxError as e:
            self.result.add_error(f"Invalid XML: {e}")
            return False
        except Exception as e:
            self.result.add_error(f"XML validation failed: {e}")
            return False
    
    async def extract_data(self, source: str) -> List[QuestionData]:
        """Extract questions from XML using XPath"""
        questions = []
        
        try:
            parser = etree.XMLParser(remove_blank_text=True)
            tree = etree.parse(source, parser)
            root = tree.getroot()
            
            # Extract elements using XPath
            if self.namespace:
                ns_map = {'ns': self.namespace}
                elements = root.xpath(self.xpath, namespaces=ns_map)
            else:
                elements = root.xpath(self.xpath)
            
            for idx, element in enumerate(elements):
                try:
                    question_data = self._process_xml_element(element, idx)
                    if question_data:
                        questions.append(question_data)
                except Exception as e:
                    self.result.add_error(f"Element {idx}: {e}", etree.tostring(element))
                    continue
        
        except Exception as e:
            self.result.add_error(f"XML processing failed: {e}")
        
        return questions
    
    def _process_xml_element(self, element: etree.Element, index: int) -> Optional[QuestionData]:
        """Process single XML element into QuestionData"""
        # Helper function to get text content
        def get_text(field_name: str) -> Optional[str]:
            field_element = element.find(f'.//{field_name}')
            if field_element is not None and field_element.text:
                return field_element.text.strip()
            return None
        
        # Extract required fields
        question_text = self.normalize_field(get_text('question'), 'question_text')
        category = self.normalize_field(get_text('category'), 'category')
        
        if not question_text or not category:
            raise ValueError("Missing required fields: question or category")
        
        # Extract optional fields
        json_id = self.normalize_field(get_text('json_id'), 'json_id')
        golden_answer = self.normalize_field(get_text('golden_answer'), 'golden_answer')
        answer_schema = self.normalize_field(get_text('answer_schema'), 'answer_schema')
        
        return QuestionData(
            json_id=json_id,
            category=category,
            question_text=question_text,
            golden_answer=golden_answer,
            answer_schema=answer_schema,
            metadata={'source_index': index, 'source_element': etree.tostring(element)}
        )
```

### XML Format Examples

#### Standard Format
```xml
<?xml version="1.0" encoding="UTF-8"?>
<questions>
  <question>
    <json_id>1</json_id>
    <category>math</category>
    <question_text>What is 2+2?</question_text>
    <golden_answer>4</golden_answer>
    <answer_schema>{"type": "object", "properties": {"answer": {"type": "number"}}}</answer_schema>
  </question>
  <question>
    <json_id>2</json_id>
    <category>science</category>
    <question_text>What is H2O?</question_text>
    <golden_answer>Water</golden_answer>
    <answer_schema>{"type": "object", "properties": {"answer": {"type": "string"}}}</answer_schema>
  </question>
</questions>
```

#### Nested Format with Namespace
```xml
<?xml version="1.0" encoding="UTF-8"?>
<dataset xmlns="http://example.com/dataset">
  <metadata>
    <name>Math Questions</name>
    <version>1.0</version>
  </metadata>
  <data>
    <questions>
      <question>
        <id>1</id>
        <type>math</type>
        <prompt>Calculate: 2+2</prompt>
        <reference>4</reference>
        <schema>{"answer": "number"}</schema>
      </question>
    </questions>
  </data>
</dataset>
```

#### Custom XPath
```bash
# For nested XML with namespace
llm-distiller import xml data.xml --xpath "//ns:question" --namespace "http://example.com/dataset"
```

## 🗄️ Database Importer

### Database Importer Implementation
```python
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from typing import List, Dict, Any

class DatabaseImporter(BaseImporter):
    """Import questions from external databases"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.connection_string = config.get('connection_string')
        self.query = config.get('query')
        self.field_mapping = config.get('mapping', {})
        self.default_correct = config.get('default_correct', None)
        self.batch_size = config.get('batch_size', 1000)
    
    async def validate_source(self, source: str) -> bool:
        """Validate database connection and query"""
        try:
            # Test connection
            engine = create_engine(source)
            with engine.connect() as conn:
                # Test query
                result = conn.execute(text("SELECT 1"))
                result.fetchone()
                
                # Validate custom query if provided
                if self.query:
                    test_result = conn.execute(text(f"SELECT * FROM ({self.query}) LIMIT 1"))
                    row = test_result.fetchone()
                    
                    if not row:
                        self.result.add_error("Query returned no results")
                        return False
                    
                    # Check required columns
                    columns = result.keys()
                    required_columns = ['question', 'category']
                    mapped_columns = [self.field_mapping.get(col, col) for col in columns]
                    
                    for required in required_columns:
                        if required not in mapped_columns:
                            self.result.add_error(f"Missing required column: {required}")
                            return False
            
            return True
            
        except Exception as e:
            self.result.add_error(f"Database validation failed: {e}")
            return False
    
    async def extract_data(self, source: str) -> List[QuestionData]:
        """Extract questions from database"""
        questions = []
        
        try:
            engine = create_engine(source)
            
            with engine.connect() as conn:
                # Use custom query or default
                if self.query:
                    result = conn.execute(text(self.query))
                else:
                    result = conn.execute(text("SELECT * FROM questions"))
                
                for row_num, row in enumerate(result, start=1):
                    try:
                        question_data = self._process_db_row(row)
                        if question_data:
                            questions.append(question_data)
                    except Exception as e:
                        self.result.add_error(f"Row {row_num}: {e}", dict(row))
                        continue
        
        except Exception as e:
            self.result.add_error(f"Database extraction failed: {e}")
        
        return questions
    
    def _process_db_row(self, row) -> Optional[QuestionData]:
        """Process single database row into QuestionData"""
        # Convert row to dictionary
        row_dict = dict(row)
        
        # Apply field mapping
        mapped_row = {}
        for db_field, value in row_dict.items():
            mapped_field = self.field_mapping.get(db_field, db_field)
            mapped_row[mapped_field] = value
        
        # Extract required fields
        question_text = self.normalize_field(mapped_row.get('question'), 'question_text')
        category = self.normalize_field(mapped_row.get('category'), 'category')
        
        if not question_text or not category:
            raise ValueError("Missing required fields: question or category")
        
        # Extract optional fields
        json_id = self.normalize_field(mapped_row.get('json_id'), 'json_id')
        golden_answer = self.normalize_field(mapped_row.get('golden_answer'), 'golden_answer')
        answer_schema = self.normalize_field(mapped_row.get('answer_schema'), 'answer_schema')
        
        return QuestionData(
            json_id=json_id,
            category=category,
            question_text=question_text,
            golden_answer=golden_answer,
            answer_schema=answer_schema,
            metadata={'source_row': row_dict}
        )
```

### Database Connection Examples

#### PostgreSQL
```bash
llm-distiller import db "postgresql://user:password@localhost:5432/dbname" --query "SELECT id as json_id, category, question_text FROM questions"
```

#### MySQL
```bash
llm-distiller import db "mysql://user:password@localhost:3306/dbname" --query "SELECT * FROM questions WHERE active = 1"
```

#### SQL Server
```bash
llm-distiller import db "mssql://user:password@localhost:1433/dbname" --query "SELECT id, category, question FROM dbo.questions"
```

#### SQLite
```bash
llm-distiller import db "sqlite:///path/to/database.db" --query "SELECT * FROM questions"
```

## 🔧 Custom Importers

### Creating Custom Importers
```python
class CustomImporter(BaseImporter):
    """Example custom importer for Excel files"""
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.sheet_name = config.get('sheet_name', 0)
        self.field_mapping = config.get('mapping', {})
    
    async def validate_source(self, source: str) -> bool:
        """Validate Excel file"""
        try:
            import pandas as pd
            df = pd.read_excel(source, sheet_name=self.sheet_name)
            
            # Check required columns
            required_columns = ['question', 'category']
            mapped_columns = [self.field_mapping.get(col, col) for col in df.columns]
            
            for required in required_columns:
                if required not in mapped_columns:
                    self.result.add_error(f"Missing required column: {required}")
                    return False
            
            return True
            
        except Exception as e:
            self.result.add_error(f"Excel validation failed: {e}")
            return False
    
    async def extract_data(self, source: str) -> List[QuestionData]:
        """Extract from Excel"""
        import pandas as pd
        
        questions = []
        df = pd.read_excel(source, sheet_name=self.sheet_name)
        
        for idx, row in df.iterrows():
            try:
                question_data = self._process_excel_row(row)
                if question_data:
                    questions.append(question_data)
            except Exception as e:
                self.result.add_error(f"Row {idx}: {e}", row.to_dict())
                continue
        
        return questions
    
    def _process_excel_row(self, row) -> Optional[QuestionData]:
        """Process Excel row"""
        # Implementation similar to other importers
        pass
    
    async def store_data(self, data: List[QuestionData]) -> ImportResult:
        """Reuse base storage logic"""
        return await super().store_data(data)
```

### Registering Custom Importers
```python
# src/data_import/__init__.py
from .csv_importer import CSVImporter
from .json_importer import JSONImporter
from .xml_importer import XMLImporter
from .db_importer import DatabaseImporter
from .custom_importer import CustomImporter

IMPORTERS = {
    'csv': CSVImporter,
    'json': JSONImporter,
    'xml': XMLImporter,
    'database': DatabaseImporter,
    'excel': CustomImporter,
}

def get_importer(importer_type: str, config: Dict[str, Any] = None) -> BaseImporter:
    """Get importer instance by type"""
    if importer_type not in IMPORTERS:
        raise ValueError(f"Unknown importer type: {importer_type}")
    
    return IMPORTERS[importer_type](config)
```

## 📊 Import Performance

### Batch Processing
```python
class BatchProcessor:
    """Handle batch processing for large imports"""
    
    def __init__(self, batch_size: int = 1000):
        self.batch_size = batch_size
    
    async def process_in_batches(self, data: List[QuestionData], processor):
        """Process data in batches"""
        results = []
        
        for i in range(0, len(data), self.batch_size):
            batch = data[i:i + self.batch_size]
            batch_result = await processor(batch)
            results.append(batch_result)
            
            # Progress reporting
            progress = min(i + self.batch_size, len(data))
            print(f"Processed {progress}/{len(data)} items")
        
        return results
```

### Memory Optimization
```python
class StreamingImporter(BaseImporter):
    """Memory-efficient streaming importer for large files"""
    
    async def extract_data_stream(self, source: str):
        """Stream data instead of loading all at once"""
        # Implementation depends on file format
        # For CSV: use csv.reader with generator
        # For JSON: use ijson for streaming JSON parsing
        pass
```

---

*Deze import modules bieden een flexibel en uitbreidbaar systeem voor het importeren van data uit diverse bronnen, met robuuste error handling en performance optimalisatie.*