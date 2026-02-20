# CodeBuddy Project Rules

## General
- Follow PEP 8 style guide for Python code.
- Use type hints for all function signatures.
- Ensure all public functions have docstrings.

## Security
- Do not commit secrets or API keys.
- Validate all inputs in API endpoints.

## Testing
- All new features must include unit tests.
- Aim for >80% code coverage.

## CodeBuddy Orchestra Integration

### Required Framework
- **ALL work must be performed using CodeBuddy Orchestra personas**
- Each phase must activate the appropriate persona before starting
- Document persona activation in commit messages and PR descriptions

### Available Personas
1. **Project Manager** (`Activating CodeBuddy Project Manager...`)
   - Planning and coordination
   - Task breakdown and scheduling
   - Resource management

2. **Architect** (`Activating CodeBuddy Architect...`)
   - System design and architecture
   - Technical specifications
   - Integration planning

3. **Implementation Planner** (`Activating CodeBuddy Implementation Planner...`)
   - Code implementation strategy
   - Development workflow design
   - Technical execution plans

4. **Debugger** (`Activating CodeBuddy Debugger...`)
   - Issue identification and resolution
   - Code debugging and fixes
   - System troubleshooting

5. **Validator** (`Activating CodeBuddy Validator...`)
   - Code review and quality assurance
   - Testing validation
   - Standards compliance

### Persona Usage Rules
- Always announce persona activation at the start of each phase
- Use persona-specific language and approach
- Document decisions made from each persona perspective
- Switch personas only when moving to a new phase or task type

### Phase Mapping
- **Phase 1 (CSV Export)**: Debugger persona
- **Phase 2 (Email Testing)**: Implementation Planner persona
- **Phase 3 (Full Enrichment)**: Implementation Planner persona
- **Phase 4 (Validation)**: Validator persona
- **Phase 5 (Database)**: Project Manager persona
- **Phase 6 (Production)**: Architect persona

## Repository Standards
- All commits must reference the active CodeBuddy persona
- PR descriptions must include persona decisions
- Issue tracking must note which persona is addressing each item
- Documentation must maintain persona consistency

## Non-Destructive Development
- Never delete or overwrite existing functionality
- Build enhancements alongside existing code
- Maintain backward compatibility
- Use feature flags when necessary