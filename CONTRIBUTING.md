# Contributing to RECA Deep Scraping Project

## CodeBuddy Orchestra Framework

This project follows the **CodeBuddy Orchestra** framework. All contributions must adhere to this framework.

### 🎭 Persona Activation

Before starting any work, you MUST:
1. Activate the appropriate CodeBuddy persona
2. Follow the persona's specific approach and methodology
3. Document decisions from that persona's perspective

### Phase-to-Persona Mapping

| Phase | Persona | Responsibility |
|-------|---------|----------------|
| 1: CSV Export | Debugger | Fix issues, resolve blockers |
| 2: Email Testing | Implementation Planner | Plan and implement solutions |
| 3: Full Enrichment | Implementation Planner | Execute implementation |
| 4: Data Validation | Validator | Review and validate work |
| 5: Database Ingestion | Project Manager | Coordinate and manage |
| 6: Production Deployment | Architect | Design and architect |

## Development Workflow

### 1. Create an Issue
- Use the `CodeBuddy Task` template
- Specify the active persona
- Define the phase
- Set acceptance criteria

### 2. Create a Branch
```bash
git checkout -b persona/phase-x-brief-description
# Example: git checkout -b debugger/phase-1-csv-export-fix
```

### 3. Implement Changes
- Follow your persona's approach
- Include type hints for all functions
- Add docstrings to public functions
- Follow PEP 8 style guide
- Maintain >80% test coverage

### 4. Commit Messages
Format: `[Persona] Brief description`
```
[Debugger] Add auto-path configuration for CSV export
- Implements cross-platform Downloads folder detection
- Adds Windows registry support for actual Downloads path
- Includes fallback mechanisms for all platforms
```

### 5. Create Pull Request
- Use the PR template
- Include persona decisions
- Document phase impact
- Ensure all checklist items are complete

## Code Standards

### Python Requirements
- **Type Hints**: Required for all function signatures
- **Docstrings**: Required for all public functions
- **Style**: Follow PEP 8
- **Testing**: Maintain >80% coverage

### Non-Destructive Development
- Never delete existing functionality
- Build enhancements alongside existing code
- Maintain backward compatibility
- Use feature flags when necessary

### Security
- Do not commit secrets or API keys
- Validate all inputs in API endpoints
- Follow secure coding practices

## Project Structure

```
q-and-a-orchestra-agent/
├── scripts/           # Implementation scripts
├── integrations/      # External integrations
├── docs/             # Documentation
├── .codebuddy/       # CodeBuddy rules
└── data/             # Data storage (gitignored)
```

## Getting Started

1. Fork the repository
2. Clone your fork
3. Create a virtual environment
4. Install dependencies: `pip install -r requirements.txt`
5. Run tests: `pytest tests/ -v`
6. Check your setup: `python scripts/check_paths.py`

## Submitting Changes

1. Ensure all tests pass
2. Update documentation
3. Follow commit message format
4. Create PR with persona information
5. Request review from appropriate persona

## Code Review Process

Reviews focus on:
- Code quality and standards
- Persona consistency
- Phase alignment
- Non-destructive principles
- Test coverage

## Questions?

- Check the [CodeBuddy Compliance](docs/codebuddy-compliance.md) document
- Review existing issues for persona examples
- Ask in your issue for clarification

---

Thank you for contributing to the RECA Deep Scraping project!