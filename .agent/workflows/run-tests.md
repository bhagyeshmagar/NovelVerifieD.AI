---
description: Run the full test suite for the NovelVerified.AI project
---

# Run Tests

## Prerequisites
- Python virtual environment should be activated

## Steps

1. Activate the virtual environment:
```bash
source .venv/bin/activate
```

// turbo
2. Run all tests:
```bash
python3 -m pytest tests/ -v
```

// turbo
3. Run tests with coverage:
```bash
python3 -m pytest tests/ -v --cov=agents --cov=flask_api --cov-report=term-missing
```

// turbo
4. Run only unit tests:
```bash
python3 -m pytest tests/ -v -m unit
```

// turbo
5. Run only integration tests:
```bash
python3 -m pytest tests/ -v -m integration
```

## Expected Output
- All 68 tests should pass
- Coverage report shows percentage of code covered
