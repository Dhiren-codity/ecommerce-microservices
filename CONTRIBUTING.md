# Contributing to E-Commerce Microservices

Thank you for your interest in contributing! This project uses Codity for automated test generation.

## Development Workflow

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Write clean, maintainable code
   - Follow language-specific conventions:
     - **Go**: Follow standard Go formatting (`gofmt`)
     - **Python**: Follow PEP 8 style guide
     - **Ruby**: Follow Ruby style guide

4. **Create a Pull Request**
   - Provide clear description of changes
   - Link to any related issues

5. **Automated Testing**
   - CI will automatically run tests
   - Codity will analyze your PR and may generate additional tests
   - If tests are generated:
     - Review the test PR created by Codity
     - CI will run automatically on the test PR
     - Codity will auto-fix failing tests (up to 3 attempts)

## Code Quality

- All PRs must pass CI checks
- Code coverage should not decrease
- Follow existing patterns and conventions

## Testing Locally

### Go Service
```bash
cd auth-service
go test -v ./...
```

### Python Service
```bash
cd analytics-service
pytest -v
```

### Ruby Service
```bash
cd api-gateway
bundle exec rspec
```

## Questions?

Open an issue for any questions or concerns!
