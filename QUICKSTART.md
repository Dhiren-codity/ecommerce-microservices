# Quick Start Guide

Get the E-Commerce Microservices platform running in 5 minutes!

## Prerequisites

Ensure you have installed:
- Go 1.21+ ([download](https://go.dev/dl/))
- Python 3.11+ ([download](https://www.python.org/downloads/))
- Ruby 3.2+ ([download](https://www.ruby-lang.org/en/downloads/))

## Step 1: Clone the Repository

```bash
git clone <your-repo-url>
cd ecommerce-microservices
```

## Step 2: Run Each Service

### Terminal 1 - Auth Service (Go)
```bash
cd auth-service
go mod download
go run cmd/main.go
```

Expected output:
```
User registered: john@example.com
Login successful! Token: eyJhbGciOiJIUzI1NiIs...
Token validated for user: john@example.com
```

### Terminal 2 - Analytics Service (Python)
```bash
cd analytics-service
pip install -r requirements.txt
python src/main.py
```

Expected output:
```
=== E-Commerce Analytics Service ===

Sales Metrics:
  Total Revenue: $324.49
  Total Orders: 3
  Average Order Value: $108.16

User Metrics:
  Total Users: 3
  Active Users: 2
  Retention Rate: 66.7%

Top Events:
  page_view: 2 times
  add_to_cart: 1 times
```

### Terminal 3 - API Gateway (Ruby)
```bash
cd api-gateway
bundle install
ruby app/gateway.rb
```

Expected output:
```
== Sinatra (v3.1.0) has taken the stage on 4567
```

## Step 3: Test the Setup

### Test Go Service
```bash
cd auth-service
go test -v ./...
```

### Test Python Service
```bash
cd analytics-service
pytest -v
```

### Test Ruby Service
```bash
cd api-gateway
bundle exec rspec
```

## Step 4: Create a Test PR (with Codity)

1. Make a change to any service file
2. Create a new branch:
   ```bash
   git checkout -b feature/my-new-feature
   ```
3. Commit and push:
   ```bash
   git add .
   git commit -m "Add new feature"
   git push origin feature/my-new-feature
   ```
4. Open a Pull Request on GitHub
5. **Watch Codity in action!**
   - Codity will analyze your changes
   - Auto-generate comprehensive unit tests
   - Create a separate PR with tests
   - CI will run automatically
   - Codity will auto-fix any failing tests

## What to Expect from Codity

When you create a PR, you'll see:

1. **Initial Comment**:
   ```
   Generating tests..

   Analyzed project structure
   Found X changed files filtering unit-testable code

   Codity supports: Go, Python, and Ruby
   ```

2. **Test PR Created**:
   ```
   Test generation complete!

   Summary:
   - Languages: GO, PYTHON, RUBY
   - Analyzed X changed files
   - Generated Y test file(s)

   Delivery:
   - Created PR: #123
   ```

3. **CI Status**:
   - If CI is configured: Auto-fix enabled
   - Tests run automatically
   - Failures are fixed (up to 3 attempts)

## Next Steps

- Explore the [README.md](README.md) for architecture details
- Check [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines
- Review CI workflows in `.github/workflows/`

## Troubleshooting

**Go dependencies not found?**
```bash
cd auth-service
go mod tidy
```

**Python modules not found?**
```bash
pip install -r requirements.txt
```

**Ruby gems not found?**
```bash
bundle install
```

Happy coding! 🚀
