# JSON Schema Validation

Dit document beschrijft het JSON schema validatie systeem van de LLM Distiller, inclusief validatie strategie, error handling en schema management.

## 📋 Overzicht

Het validatie systeem is ontworpen voor:
- **Schema validatie**: Valideer LLM antwoorden tegen JSON schemas
- **Error tracking**: Gedetailleerde foutanalyse en rapportage
- **Schema management**: Versiebeheer en evolutie van schemas
- **Quality control**: Automatische en handmatige validatie workflows

## 🏗️ Validatie Architecture

### Core Validator
```python
import json
import jsonschema
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum

class ValidationErrorType(str, Enum):
    """Types of validation errors"""
    JSON_PARSE_ERROR = "JSON_PARSE_ERROR"
    SCHEMA_VALIDATION_ERROR = "SCHEMA_VALIDATION_ERROR"
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    INVALID_DATA_TYPE = "INVALID_DATA_TYPE"
    CONSTRAINT_VIOLATION = "CONSTRAINT_VIOLATION"
    ADDITIONAL_PROPERTIES = "ADDITIONAL_PROPERTIES"

@dataclass
class ValidationResult:
    """Result of schema validation"""
    is_valid: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    error_type: Optional[ValidationErrorType] = None
    error_path: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None

class SchemaValidator:
    """JSON schema validation with detailed error reporting"""
    
    def __init__(self):
        self.validator_class = jsonschema.Draft7Validator
        self.format_checker = jsonschema.draft7_format_checker
    
    def validate_response(self, response: str, schema: str) -> ValidationResult:
        """Validate response against JSON schema"""
        try:
            # Parse response JSON
            response_data = json.loads(response)
        except json.JSONDecodeError as e:
            return ValidationResult(
                is_valid=False,
                error=f"Invalid JSON: {e.msg}",
                error_type=ValidationErrorType.JSON_PARSE_ERROR,
                error_details={
                    "line": e.lineno,
                    "column": e.colno,
                    "position": e.pos
                }
            )
        
        try:
            # Parse schema
            schema_data = json.loads(schema)
        except json.JSONDecodeError as e:
            return ValidationResult(
                is_valid=False,
                error=f"Invalid schema JSON: {e.msg}",
                error_type=ValidationErrorType.JSON_PARSE_ERROR,
                error_details={
                    "line": e.lineno,
                    "column": e.colno,
                    "position": e.pos
                }
            )
        
        # Validate response against schema
        return self._validate_against_schema(response_data, schema_data)
    
    def _validate_against_schema(self, data: Dict[str, Any], 
                                schema: Dict[str, Any]) -> ValidationResult:
        """Validate data against schema with detailed error reporting"""
        try:
            validator = self.validator_class(
                schema, 
                format_checker=self.format_checker
            )
            
            # Perform validation
            validator.validate(data)
            
            return ValidationResult(
                is_valid=True,
                data=data
            )
            
        except jsonschema.ValidationError as e:
            return self._create_validation_error(e)
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                error=f"Validation error: {str(e)}",
                error_type=ValidationErrorType.SCHEMA_VALIDATION_ERROR
            )
    
    def _create_validation_error(self, error: jsonschema.ValidationError) -> ValidationResult:
        """Create detailed validation error from jsonschema error"""
        error_path = " -> ".join(str(p) for p in error.absolute_path) if error.absolute_path else "root"
        
        # Determine error type
        error_type = self._classify_error(error)
        
        # Create detailed error message
        error_message = self._format_error_message(error)
        
        return ValidationResult(
            is_valid=False,
            error=error_message,
            error_type=error_type,
            error_path=error_path,
            error_details={
                "validator": error.validator,
                "validator_value": error.validator_value,
                "failed_value": error.instance,
                "schema_path": " -> ".join(str(p) for p in error.schema_path) if error.schema_path else None
            }
        )
    
    def _classify_error(self, error: jsonschema.ValidationError) -> ValidationErrorType:
        """Classify validation error type"""
        validator = error.validator
        
        if validator == "required":
            return ValidationErrorType.MISSING_REQUIRED_FIELD
        elif validator == "type":
            return ValidationErrorType.INVALID_DATA_TYPE
        elif validator == "additionalProperties":
            return ValidationErrorType.ADDITIONAL_PROPERTIES
        elif validator in ["minimum", "maximum", "minLength", "maxLength", "pattern"]:
            return ValidationErrorType.CONSTRAINT_VIOLATION
        else:
            return ValidationErrorType.SCHEMA_VALIDATION_ERROR
    
    def _format_error_message(self, error: jsonschema.ValidationError) -> str:
        """Format user-friendly error message"""
        validator = error.validator
        
        if validator == "required":
            missing_props = error.validator_value
            return f"Missing required field(s): {', '.join(missing_props)}"
        
        elif validator == "type":
            expected_type = error.validator_value
            actual_type = type(error.instance).__name__
            return f"Expected type '{expected_type}', got '{actual_type}'"
        
        elif validator == "additionalProperties":
            unexpected = error.validator_value
            return f"Unexpected additional property: {unexpected}"
        
        elif validator == "minimum":
            return f"Value {error.instance} is less than minimum {error.validator_value}"
        
        elif validator == "maximum":
            return f"Value {error.instance} is greater than maximum {error.validator_value}"
        
        elif validator == "minLength":
            return f"String length {len(error.instance)} is less than minimum {error.validator_value}"
        
        elif validator == "maxLength":
            return f"String length {len(error.instance)} is greater than maximum {error.validator_value}"
        
        elif validator == "pattern":
            return f"Value '{error.instance}' does not match pattern '{error.validator_value}'"
        
        else:
            return f"Validation failed: {error.message}"
```

## 🔍 Advanced Validation Features

### Schema Preprocessing
```python
class SchemaProcessor:
    """Process and optimize schemas for validation"""
    
    @staticmethod
    def normalize_schema(schema: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize schema for consistent validation"""
        # Deep copy to avoid mutation
        normalized = json.loads(json.dumps(schema))
        
        # Add default values
        if "$schema" not in normalized:
            normalized["$schema"] = "http://json-schema.org/draft-07/schema#"
        
        # Ensure proper type definitions
        SchemaProcessor._ensure_type_definitions(normalized)
        
        # Optimize for performance
        SchemaProcessor._optimize_for_performance(normalized)
        
        return normalized
    
    @staticmethod
    def _ensure_type_definitions(schema: Dict[str, Any]):
        """Ensure proper type definitions"""
        if "type" in schema and isinstance(schema["type"], str):
            # Convert string type to array for consistency
            schema["type"] = [schema["type"]]
        
        # Recursively process nested schemas
        for key, value in schema.items():
            if isinstance(value, dict):
                SchemaProcessor._ensure_type_definitions(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        SchemaProcessor._ensure_type_definitions(item)
    
    @staticmethod
    def _optimize_for_performance(schema: Dict[str, Any]):
        """Optimize schema for better validation performance"""
        # Add format checks only if needed
        if "format" in schema:
            # Ensure format checker is available
            pass
        
        # Optimize array validation
        if schema.get("type") == "array" and "items" in schema:
            items_schema = schema["items"]
            if isinstance(items_schema, dict):
                # Add minItems for better error messages
                if "minItems" not in schema and "required" in items_schema:
                    required_count = len(items_schema.get("required", []))
                    schema["minItems"] = required_count
    
    @staticmethod
    def extract_required_fields(schema: Dict[str, Any]) -> List[str]:
        """Extract all required fields from schema"""
        required_fields = []
        
        def extract_from_obj(obj, path=""):
            if isinstance(obj, dict):
                if "required" in obj:
                    for field in obj["required"]:
                        full_path = f"{path}.{field}" if path else field
                        required_fields.append(full_path)
                
                # Recursively check nested objects
                for key, value in obj.items():
                    if key == "properties" and isinstance(value, dict):
                        for prop_key, prop_value in value.items():
                            extract_from_obj(prop_value, f"{path}.{prop_key}" if path else prop_key)
                    elif isinstance(value, (dict, list)):
                        extract_from_obj(value, path)
        
        extract_from_obj(schema)
        return required_fields
```

### Response Preprocessing
```python
class ResponseProcessor:
    """Process LLM responses before validation"""
    
    @staticmethod
    def extract_json_from_text(text: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract JSON from text that might contain explanations"""
        import re
        
        # Try to find JSON blocks
        json_patterns = [
            r'```json\s*(.*?)\s*```',  # JSON code blocks
            r'```\s*(.*?)\s*```',       # Generic code blocks
            r'\{.*\}',                  # Brute force JSON object
            r'\[.*\]'                   # Brute force JSON array
        ]
        
        for pattern in json_patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            for match in matches:
                try:
                    # Validate that it's valid JSON
                    json.loads(match.strip())
                    return match.strip(), None
                except json.JSONDecodeError:
                    continue
        
        # If no JSON found, try to parse the entire text
        try:
            json.loads(text.strip())
            return text.strip(), None
        except json.JSONDecodeError:
            return None, "No valid JSON found in response"
    
    @staticmethod
    def clean_response(text: str) -> str:
        """Clean response text for better JSON parsing"""
        # Remove common prefixes
        prefixes_to_remove = [
            "Here's the JSON response:",
            "The JSON response is:",
            "Response:",
            "Answer:",
        ]
        
        for prefix in prefixes_to_remove:
            if text.startswith(prefix):
                text = text[len(prefix):].strip()
        
        # Remove markdown formatting
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*$', '', text)
        
        # Remove explanatory text after JSON
        json_end = text.rfind('}')
        if json_end != -1:
            text = text[:json_end + 1]
        
        return text.strip()
    
    @staticmethod
    def fix_common_issues(text: str) -> str:
        """Fix common JSON formatting issues"""
        # Fix trailing commas
        text = re.sub(r',(\s*[}\]])', r'\1', text)
        
        # Fix quotes around property names
        text = re.sub(r'(\w+)\s*:', r'"\1":', text)
        
        # Fix single quotes
        text = re.sub(r"'([^']*)'", r'"\1"', text)
        
        # Fix unescaped newlines in strings
        text = re.sub(r'\n(?=[^,\}\]\s]*")', r'\\n', text)
        
        return text
```

## 📊 Validation Pipeline

### Complete Validation Pipeline
```python
class ValidationPipeline:
    """Complete validation pipeline with preprocessing and error analysis"""
    
    def __init__(self):
        self.schema_processor = SchemaProcessor()
        self.response_processor = ResponseProcessor()
        self.validator = SchemaValidator()
        self.error_analyzer = ValidationErrorAnalyzer()
    
    def validate_response_pipeline(self, response: str, schema: str) -> ValidationResult:
        """Complete validation pipeline with preprocessing"""
        # Step 1: Extract JSON from response
        json_content, extract_error = self.response_processor.extract_json_from_text(response)
        
        if extract_error:
            return ValidationResult(
                is_valid=False,
                error=extract_error,
                error_type=ValidationErrorType.JSON_PARSE_ERROR
            )
        
        # Step 2: Clean and fix JSON
        cleaned_json = self.response_processor.clean_response(json_content)
        fixed_json = self.response_processor.fix_common_issues(cleaned_json)
        
        # Step 3: Normalize schema
        try:
            schema_data = json.loads(schema)
            normalized_schema = self.schema_processor.normalize_schema(schema_data)
            normalized_schema_str = json.dumps(normalized_schema)
        except json.JSONDecodeError as e:
            return ValidationResult(
                is_valid=False,
                error=f"Invalid schema: {e.msg}",
                error_type=ValidationErrorType.JSON_PARSE_ERROR
            )
        
        # Step 4: Validate
        result = self.validator.validate_response(fixed_json, normalized_schema_str)
        
        # Step 5: Analyze errors if validation failed
        if not result.is_valid:
            analysis = self.error_analyzer.analyze_error(result, fixed_json, normalized_schema)
            result.error_details.update(analysis)
        
        return result
```

### Error Analysis
```python
class ValidationErrorAnalyzer:
    """Analyze validation errors and provide suggestions"""
    
    def analyze_error(self, result: ValidationResult, response: str, 
                     schema: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze validation error and provide suggestions"""
        analysis = {
            "suggestions": [],
            "severity": "error",
            "auto_fixable": False,
            "schema_issues": []
        }
        
        if result.error_type == ValidationErrorType.MISSING_REQUIRED_FIELD:
            analysis.update(self._analyze_missing_fields(result, response, schema))
        
        elif result.error_type == ValidationErrorType.INVALID_DATA_TYPE:
            analysis.update(self._analyze_type_mismatch(result, response, schema))
        
        elif result.error_type == ValidationErrorType.ADDITIONAL_PROPERTIES:
            analysis.update(self._analyze_additional_properties(result, response, schema))
        
        elif result.error_type == ValidationErrorType.CONSTRAINT_VIOLATION:
            analysis.update(self._analyze_constraint_violation(result, response, schema))
        
        return analysis
    
    def _analyze_missing_fields(self, result: ValidationResult, response: str, 
                               schema: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze missing required fields"""
        suggestions = []
        
        try:
            response_data = json.loads(response)
            missing_fields = []
            
            # Find missing required fields
            if "required" in schema:
                for field in schema["required"]:
                    if field not in response_data:
                        missing_fields.append(field)
                        suggestions.append(f"Add missing required field: {field}")
            
            # Check if similar fields exist (typo detection)
            for missing in missing_fields:
                similar = self._find_similar_fields(missing, response_data.keys())
                if similar:
                    suggestions.append(f"Did you mean '{similar}' instead of '{missing}'?")
            
            return {
                "suggestions": suggestions,
                "severity": "error",
                "auto_fixable": False,
                "missing_fields": missing_fields
            }
            
        except json.JSONDecodeError:
            return {"suggestions": ["Fix JSON syntax first"], "severity": "error"}
    
    def _analyze_type_mismatch(self, result: ValidationResult, response: str, 
                               schema: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze type mismatch errors"""
        suggestions = []
        
        try:
            response_data = json.loads(response)
            error_path = result.error_path.split(".") if result.error_path else []
            
            # Navigate to the problematic field
            current_data = response_data
            current_schema = schema
            
            for path_part in error_path:
                if path_part.isdigit():  # Array index
                    path_part = int(path_part)
                    if isinstance(current_data, list) and path_part < len(current_data):
                        current_data = current_data[path_part]
                    if isinstance(current_schema, dict) and "items" in current_schema:
                        current_schema = current_schema["items"]
                else:  # Object property
                    if isinstance(current_data, dict) and path_part in current_data:
                        current_data = current_data[path_part]
                    if isinstance(current_schema, dict) and "properties" in current_schema:
                        current_schema = current_schema["properties"].get(path_part, {})
            
            # Analyze the type mismatch
            expected_type = current_schema.get("type")
            actual_value = current_data
            actual_type = type(actual_value).__name__
            
            if expected_type == "string" and isinstance(actual_value, (int, float)):
                suggestions.append(f"Convert number {actual_value} to string: \"{actual_value}\"")
            elif expected_type == "number" and isinstance(actual_value, str):
                try:
                    float(actual_value)
                    suggestions.append(f"Convert string '{actual_value}' to number")
                except ValueError:
                    suggestions.append(f"String '{actual_value}' cannot be converted to number")
            elif expected_type == "array" and isinstance(actual_value, str):
                suggestions.append(f"Convert string '{actual_value}' to JSON array")
            elif expected_type == "object" and isinstance(actual_value, str):
                suggestions.append(f"Convert string '{actual_value}' to JSON object")
            
            return {
                "suggestions": suggestions,
                "severity": "error",
                "auto_fixable": len(suggestions) > 0,
                "expected_type": expected_type,
                "actual_type": actual_type,
                "actual_value": actual_value
            }
            
        except Exception:
            return {"suggestions": ["Unable to analyze type mismatch"], "severity": "error"}
    
    def _find_similar_fields(self, target: str, candidates: List[str]) -> Optional[str]:
        """Find similar field names using Levenshtein distance"""
        from difflib import get_close_matches
        
        matches = get_close_matches(target, candidates, n=1, cutoff=0.6)
        return matches[0] if matches else None
    
    def _analyze_additional_properties(self, result: ValidationResult, response: str, 
                                      schema: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze additional properties error"""
        suggestions = []
        
        try:
            response_data = json.loads(response)
            
            # Find additional properties
            allowed_properties = set(schema.get("properties", {}).keys())
            actual_properties = set(response_data.keys())
            additional = actual_properties - allowed_properties
            
            for prop in additional:
                suggestions.append(f"Remove additional property: {prop}")
            
            # Check if schema should allow additional properties
            if not schema.get("additionalProperties", True):
                suggestions.append("Consider adding 'additionalProperties': true to schema if extra fields are acceptable")
            
            return {
                "suggestions": suggestions,
                "severity": "warning",
                "auto_fixable": True,
                "additional_properties": list(additional)
            }
            
        except Exception:
            return {"suggestions": ["Unable to analyze additional properties"], "severity": "error"}
    
    def _analyze_constraint_violation(self, result: ValidationResult, response: str, 
                                      schema: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze constraint violations"""
        suggestions = []
        
        error_details = result.error_details or {}
        validator = error_details.get("validator")
        validator_value = error_details.get("validator_value")
        failed_value = error_details.get("failed_value")
        
        if validator == "minimum":
            suggestions.append(f"Value must be at least {validator_value}, got {failed_value}")
        elif validator == "maximum":
            suggestions.append(f"Value must be at most {validator_value}, got {failed_value}")
        elif validator == "minLength":
            suggestions.append(f"String must be at least {validator_value} characters, got {len(str(failed_value))}")
        elif validator == "maxLength":
            suggestions.append(f"String must be at most {validator_value} characters, got {len(str(failed_value))}")
        elif validator == "pattern":
            suggestions.append(f"Value must match pattern: {validator_value}")
        
        return {
            "suggestions": suggestions,
            "severity": "error",
            "auto_fixable": False,
            "constraint": validator,
            "constraint_value": validator_value,
            "actual_value": failed_value
        }
```

## 📈 Schema Management

### Schema Evolution
```python
class SchemaManager:
    """Manage schema versions and evolution"""
    
    def __init__(self):
        self.schemas = {}  # schema_id -> schema_data
        self.versions = {}  # schema_id -> version_history
    
    def register_schema(self, schema_id: str, schema: Dict[str, Any], 
                       version: str = "1.0.0") -> str:
        """Register a new schema version"""
        if schema_id not in self.schemas:
            self.schemas[schema_id] = {}
            self.versions[schema_id] = []
        
        # Validate schema
        self._validate_schema_structure(schema)
        
        # Store version
        version_data = {
            "version": version,
            "schema": schema,
            "timestamp": datetime.now().isoformat(),
            "changes": self._analyze_changes(schema_id, schema)
        }
        
        self.schemas[schema_id][version] = schema
        self.versions[schema_id].append(version_data)
        
        return version
    
    def get_latest_schema(self, schema_id: str) -> Optional[Dict[str, Any]]:
        """Get latest version of a schema"""
        if schema_id not in self.schemas:
            return None
        
        latest_version = max(self.schemas[schema_id].keys())
        return self.schemas[schema_id][latest_version]
    
    def validate_with_version(self, response: str, schema_id: str, 
                             version: Optional[str] = None) -> ValidationResult:
        """Validate response against specific schema version"""
        if schema_id not in self.schemas:
            return ValidationResult(
                is_valid=False,
                error=f"Schema not found: {schema_id}",
                error_type=ValidationErrorType.SCHEMA_VALIDATION_ERROR
            )
        
        if version is None:
            schema = self.get_latest_schema(schema_id)
        else:
            schema = self.schemas[schema_id].get(version)
        
        if not schema:
            return ValidationResult(
                is_valid=False,
                error=f"Schema version not found: {schema_id}:{version}",
                error_type=ValidationErrorType.SCHEMA_VALIDATION_ERROR
            )
        
        validator = SchemaValidator()
        return validator.validate_response(response, json.dumps(schema))
    
    def _validate_schema_structure(self, schema: Dict[str, Any]):
        """Validate that schema follows expected structure"""
        required_fields = ["type"]
        for field in required_fields:
            if field not in schema:
                raise ValueError(f"Schema missing required field: {field}")
    
    def _analyze_changes(self, schema_id: str, new_schema: Dict[str, Any]) -> List[str]:
        """Analyze changes compared to previous version"""
        changes = []
        
        if schema_id in self.schemas and self.schemas[schema_id]:
            latest_schema = self.get_latest_schema(schema_id)
            
            # Compare required fields
            old_required = set(latest_schema.get("required", []))
            new_required = set(new_schema.get("required", []))
            
            added_required = new_required - old_required
            removed_required = old_required - new_required
            
            if added_required:
                changes.append(f"Added required fields: {', '.join(added_required)}")
            if removed_required:
                changes.append(f"Removed required fields: {', '.join(removed_required)}")
        
        return changes
```

## 🔧 Integration Examples

### Database Integration
```python
class DatabaseValidator:
    """Integrate validation with database operations"""
    
    def __init__(self, db_session, schema_manager: SchemaManager):
        self.db = db_session
        self.schema_manager = schema_manager
        self.pipeline = ValidationPipeline()
    
    def validate_and_store_response(self, question_id: int, response: str, 
                                   model_config: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate response and store in appropriate table"""
        # Get question and schema
        question = self.db.query(Question).filter(Question.id == question_id).first()
        if not question:
            return False, "Question not found"
        
        # Validate if schema exists
        if question.answer_schema:
            validation_result = self.pipeline.validate_response_pipeline(
                response, question.answer_schema
            )
            
            if validation_result.is_valid:
                # Store in valid responses table
                self._store_valid_response(question_id, response, model_config, validation_result)
                return True, "Response validated and stored"
            else:
                # Store in invalid responses table
                self._store_invalid_response(question_id, response, model_config, validation_result)
                return False, f"Validation failed: {validation_result.error}"
        else:
            # No schema to validate against, store as valid
            self._store_valid_response(question_id, response, model_config, None)
            return True, "Response stored (no schema to validate)"
    
    def _store_valid_response(self, question_id: int, response: str, 
                             model_config: Dict[str, Any], validation_result: Optional[ValidationResult]):
        """Store response in valid responses table"""
        response_record = Response(
            question_id=question_id,
            model_name=model_config.get("model", "unknown"),
            model_config=json.dumps(model_config),
            answer=response,
            is_correct=None  # To be manually validated
        )
        
        self.db.add(response_record)
        self.db.commit()
    
    def _store_invalid_response(self, question_id: int, response: str, 
                               model_config: Dict[str, Any], validation_result: ValidationResult):
        """Store response in invalid responses table"""
        invalid_record = InvalidResponse(
            question_id=question_id,
            model_name=model_config.get("model", "unknown"),
            model_config=json.dumps(model_config),
            answer=response,
            validation_error=validation_result.error,
            error_type=validation_result.error_type.value
        )
        
        self.db.add(invalid_record)
        self.db.commit()
```

---

*Dit validatie systeem biedt robuuste JSON schema validatie met gedetailleerde error reporting, preprocessing en schema management capabilities.*