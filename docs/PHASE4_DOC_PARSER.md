# Phase 4: Automated Documentation Parser

## Overview

Phase 4 aims to create an AI-powered system that can automatically parse manufacturer documentation (PDFs, web pages, etc.) and extract API command information to populate the Sugartalking database. This will dramatically reduce the manual effort required to add new receiver models.

## Current Status

**STATUS: PLACEHOLDER - NOT YET IMPLEMENTED**

This document describes the planned architecture for future implementation.

## Goals

1. **Automatic Command Extraction**: Parse manufacturer documentation and extract:
   - Command endpoints
   - Command formats
   - Parameter specifications
   - Valid value ranges

2. **Multi-Format Support**: Handle various documentation formats:
   - PDF manuals
   - HTML documentation pages
   - Plain text protocol specifications
   - API reference documents

3. **AI-Assisted Parsing**: Use LLM APIs (Claude, GPT) to intelligently interpret documentation when regex patterns fail

4. **Validation**: Verify extracted commands against test receivers before adding to database

5. **Semi-Automated Workflow**: Human review before finalizing database entries

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                   Documentation Parser                       │
└─────────────────────────────────────────────────────────────┘
                              │
           ┌──────────────────┼──────────────────┐
           │                  │                  │
           ▼                  ▼                  ▼
    ┌────────────┐     ┌────────────┐    ┌────────────┐
    │   PDF      │     │    HTML    │    │  Plain     │
    │  Parser    │     │   Parser   │    │   Text     │
    └────────────┘     └────────────┘    └────────────┘
           │                  │                  │
           └──────────────────┼──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  Text Extractor  │
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  Pattern Matcher │
                    │  (Regex + AI)    │
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │   LLM Assistant  │
                    │ (Claude/GPT API) │
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │ Command Builder  │
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │    Validator     │
                    │  (Test Against   │
                    │   Real Device)   │
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  Human Review    │
                    │   Interface      │
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │   Database       │
                    └──────────────────┘
```

## Implementation Plan

### Step 1: Document Ingestion

**Module**: `app/services/doc_parser/ingestion.py`

- Accept various input formats:
  - PDF files (using `pdfplumber` or `PyPDF2`)
  - URLs to online documentation
  - Plain text files
  - Word documents (`.docx`)

- Extract raw text while preserving structure
- Handle multi-page documents
- Extract tables and code blocks

**Dependencies**:
```python
pdfplumber>=0.10.0
beautifulsoup4>=4.12.0
python-docx>=1.0.0
requests>=2.31.0
```

**Example Usage**:
```python
from app.services.doc_parser import DocumentIngestion

ingestor = DocumentIngestion()
doc = ingestor.load_pdf("denon_protocol.pdf")
# or
doc = ingestor.load_url("https://example.com/api-docs")
```

### Step 2: Pattern Recognition

**Module**: `app/services/doc_parser/patterns.py`

- Define regex patterns for common command structures
- Recognize command tables
- Identify parameter specifications
- Extract endpoint URLs

**Common Patterns**:
```python
PATTERNS = {
    'http_command': r'(GET|POST|PUT)\s+(http://[^\s]+)',
    'command_table': r'\|\s*Command\s*\|\s*Format\s*\|\s*Description\s*\|',
    'parameter': r'Range:\s*(-?\d+)\s*to\s*(-?\d+)',
    'hex_command': r'0x[0-9A-Fa-f]{2,}',
}
```

### Step 3: LLM-Assisted Extraction

**Module**: `app/services/doc_parser/llm_extractor.py`

- Use Claude or GPT API to intelligently parse complex documentation
- Ask targeted questions about command formats
- Handle ambiguous or poorly-formatted documentation

**Example Prompt**:
```python
prompt = f"""
Given this excerpt from a receiver API documentation:

{doc_excerpt}

Please extract the following information:
1. Command endpoint URL
2. HTTP method (GET/POST/PUT)
3. Command format/template
4. Required parameters and their types
5. Valid value ranges

Format the response as JSON.
"""
```

**API Integration**:
```python
import anthropic

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

def extract_with_llm(doc_text):
    message = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=4096,
        messages=[{
            "role": "user",
            "content": prompt
        }]
    )
    return parse_llm_response(message.content)
```

### Step 4: Command Builder

**Module**: `app/services/doc_parser/builder.py`

- Transform extracted data into database models
- Create `Receiver`, `Command`, and `CommandParameter` objects
- Handle edge cases and validation

**Example**:
```python
def build_command(receiver_id, extracted_data):
    command = Command(
        receiver_id=receiver_id,
        action_type=extracted_data['action_type'],
        action_name=extracted_data['action_name'],
        endpoint=extracted_data['endpoint'],
        http_method=extracted_data['method'],
        command_template=extracted_data['template'],
        description=extracted_data['description']
    )
    return command
```

### Step 5: Validator

**Module**: `app/services/doc_parser/validator.py`

- Test extracted commands against a real receiver (if available)
- Verify command format is correct
- Check parameter ranges
- Flag commands that fail validation for human review

**Example**:
```python
def validate_command(command, receiver_ip):
    """Test a command against a real receiver."""
    try:
        executor = CommandExecutor()
        result = executor.execute_command(
            receiver_model=command.receiver.model,
            action_name=command.action_name,
            host=receiver_ip,
            timeout=5
        )
        return result  # True if successful
    except Exception as e:
        logger.error(f"Validation failed: {e}")
        return False
```

### Step 6: Review Interface

**Module**: `app/routes/parser_admin.py`

- Web UI for reviewing extracted commands
- Show confidence scores
- Allow manual editing before database insertion
- Batch approve/reject functionality

**UI Features**:
- Side-by-side view: documentation excerpt vs extracted data
- Confidence score for each extraction
- Test button to try command against real receiver
- Edit mode for corrections
- Bulk import workflow

## Data Flow

1. **User uploads documentation** (PDF, URL, etc.)
2. **System extracts text** and identifies command sections
3. **Pattern matcher** finds obvious command structures
4. **LLM processes** ambiguous sections
5. **Commands are built** into database models
6. **Validator tests** against real receiver (optional)
7. **Human reviews** extractions in web UI
8. **Approved commands** are inserted into database

## Configuration

```yaml
# config/parser_config.yaml

parser:
  enabled: true

  # LLM configuration
  llm:
    provider: "anthropic"  # or "openai"
    model: "claude-3-5-sonnet-20241022"
    api_key_env: "ANTHROPIC_API_KEY"
    max_tokens: 4096

  # Confidence thresholds
  confidence:
    auto_accept: 0.95  # Auto-accept if confidence > 95%
    require_review: 0.70  # Review if confidence < 70%

  # Validation
  validation:
    enabled: false  # Set to true if test receiver available
    test_receiver_ip: "192.168.1.100"
    timeout: 5

  # Supported formats
  formats:
    - pdf
    - html
    - txt
    - docx
```

## API Endpoints

```python
# Upload documentation for parsing
POST /api/parser/upload
Body: multipart/form-data with file

# Or provide URL
POST /api/parser/parse-url
Body: {"url": "https://example.com/docs"}

# Get parsing status
GET /api/parser/status/{job_id}

# Review extracted commands
GET /api/parser/review/{job_id}

# Approve commands
POST /api/parser/approve
Body: {"command_ids": [1, 2, 3]}

# Reject commands
POST /api/parser/reject
Body: {"command_ids": [4, 5]}
```

## Challenges & Solutions

### Challenge 1: Inconsistent Documentation Formats

**Problem**: Every manufacturer formats documentation differently.

**Solution**:
- Use LLM to interpret varied formats
- Build manufacturer-specific pattern libraries
- Allow users to define custom patterns

### Challenge 2: Ambiguous Specifications

**Problem**: Documentation may be unclear or incomplete.

**Solution**:
- Flag low-confidence extractions for review
- Ask LLM targeted clarification questions
- Require human validation for critical commands

### Challenge 3: Testing Without Hardware

**Problem**: Can't validate commands without physical receiver.

**Solution**:
- Make validation optional
- Crowdsource testing from users with hardware
- Maintain a "confidence score" for untested commands

### Challenge 4: API Costs

**Problem**: LLM API calls can be expensive for large documents.

**Solution**:
- Use regex first, LLM only for ambiguous sections
- Cache LLM responses
- Batch process multiple commands in single API call
- Offer manual parsing option

## Future Enhancements

1. **Community Contributions**: Allow users to submit parsed documentation
2. **Learning System**: Improve patterns based on successful/failed extractions
3. **Multi-Language Support**: Parse documentation in various languages
4. **Video Parsing**: Extract commands from tutorial videos (OCR + speech-to-text)
5. **Protocol Sniffing**: Capture network traffic to reverse-engineer protocols

## Dependencies

```txt
# PDF parsing
pdfplumber>=0.10.0
PyPDF2>=3.0.0

# HTML parsing
beautifulsoup4>=4.12.0
lxml>=4.9.0

# Document parsing
python-docx>=1.0.0

# LLM APIs
anthropic>=0.18.0
openai>=1.0.0

# OCR (optional, for scanned PDFs)
pytesseract>=0.3.10
pillow>=10.0.0

# Natural language processing
spacy>=3.7.0
```

## Getting Started (When Implemented)

```bash
# Install dependencies
pip install -r requirements-parser.txt

# Set API key
export ANTHROPIC_API_KEY=your_key_here

# Run parser service
python -m app.services.doc_parser.service

# Access UI
http://localhost:5000/admin/parser
```

## Testing Strategy

1. **Unit Tests**: Test each parser component independently
2. **Integration Tests**: End-to-end parsing of known documentation
3. **Golden Dataset**: Maintain a set of reference documents with known correct outputs
4. **Regression Tests**: Ensure new changes don't break existing parsers

## Cost Estimation

**LLM API Costs** (estimated):
- Claude Sonnet: ~$3 per million input tokens, ~$15 per million output tokens
- Typical receiver manual: ~10,000 tokens
- Cost per manual: ~$0.30 - $0.50 (with caching and batching)

## Timeline (Proposed)

- **Week 1-2**: Document ingestion and basic pattern matching
- **Week 3-4**: LLM integration and extraction logic
- **Week 5**: Validation framework
- **Week 6**: Review UI
- **Week 7-8**: Testing and refinement

## Contributing

If you want to help build this feature:

1. Start with a specific manufacturer's documentation
2. Build patterns for that manufacturer
3. Test extraction accuracy
4. Submit PR with patterns and test cases

## Questions?

For questions or ideas about Phase 4, please:
- Open a GitHub issue
- Tag with `phase-4` and `enhancement`
- Use the Claude context prompt in `CONTEXT_PROMPT.md` to continue development

---

**Last Updated**: 2025-11-08
**Status**: Planning/Architecture Phase
**Target Version**: 3.0.0
