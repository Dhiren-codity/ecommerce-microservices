# E-Commerce Microservices Platform

A modern microservices architecture demonstrating polyglot development with Go, Python, and Ruby.

## Architecture Overview

This project implements a scalable e-commerce platform using three microservices:

- **Auth Service (Go)** - User authentication and JWT token management
- **Analytics Service (Python)** - Real-time analytics and reporting
- **API Gateway (Ruby)** - Request routing and API orchestration

## Services

### 🔐 Auth Service (Go)
Handles user authentication, registration, and token management.

**Tech Stack:**
- Go 1.21+
- JWT for authentication
- Bcrypt for password hashing

**Features:**
- User registration with email validation
- Login with JWT token generation
- Token validation middleware
- Password reset functionality

### 📊 Analytics Service (Python)
Processes and analyzes user behavior and sales data.

**Tech Stack:**
- Python 3.11+
- FastAPI framework
- Pandas for data processing

**Features:**
- Sales metrics calculation
- User behavior tracking
- Real-time dashboard data
- Report generation

### 🌐 API Gateway (Ruby)
Central entry point for all client requests.

**Tech Stack:**
- Ruby 3.2+
- Sinatra framework
- HTTP client for service communication

**Features:**
- Request routing to microservices
- Rate limiting
- Request logging
- Error handling

## Getting Started

### Prerequisites

- Go 1.21+
- Python 3.11+
- Ruby 3.2+
- Git

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd ecommerce-microservices
```

2. Set up each service:

**Auth Service (Go):**
```bash
cd auth-service
go mod download
go run cmd/main.go
```

**Analytics Service (Python):**
```bash
cd analytics-service
pip install -r requirements.txt
python src/main.py
```

**API Gateway (Ruby):**
```bash
cd api-gateway
bundle install
ruby app/gateway.rb
```

## Running Tests

Each service has its own test suite with CI/CD integration:

**Go Tests:**
```bash
cd auth-service
go test -v ./...
```

**Python Tests:**
```bash
cd analytics-service
pytest -v
```

**Ruby Tests:**
```bash
cd api-gateway
bundle exec rspec
```

## CI/CD

GitHub Actions workflows automatically run tests on every PR:

- `.github/workflows/go-tests.yml` - Auth service tests
- `.github/workflows/python-tests.yml` - Analytics service tests
- `.github/workflows/ruby-tests.yml` - API Gateway tests

All workflows trigger on:
- New pull requests
- New commits to PRs
- Reopened pull requests

## API Endpoints

### Auth Service (Port 8080)
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - User login
- `POST /api/auth/validate` - Validate JWT token

### Analytics Service (Port 8000)
- `GET /api/analytics/sales` - Get sales metrics
- `GET /api/analytics/users` - Get user statistics
- `POST /api/analytics/track` - Track user event

### API Gateway (Port 3000)
- `/*` - Routes to appropriate service

## Development

### Adding New Features

1. Create a feature branch
2. Implement your changes
3. Write tests (Codity can auto-generate tests)
4. Create a PR
5. CI will automatically run tests
6. Merge when all checks pass

### Code Quality

- Go: Uses `gofmt` and `golint`
- Python: Uses `pytest` and `black` formatter
- Ruby: Uses `rubocop` and `rspec`

## Testing with Codity

This repository is configured to work with Codity's automated test generation:

1. Make code changes and create a PR
2. Codity analyzes changes and generates tests
3. Tests are committed to a separate PR
4. CI runs automatically
5. Codity auto-fixes failing tests (up to 3 attempts)

## Project Structure

```
ecommerce-microservices/
├── .github/
│   └── workflows/          # CI/CD workflows
├── auth-service/           # Go authentication service
│   ├── cmd/
│   ├── internal/
│   └── go.mod
├── analytics-service/      # Python analytics service
│   ├── src/
│   ├── tests/
│   └── requirements.txt
├── api-gateway/            # Ruby API gateway
│   ├── app/
│   ├── spec/
│   └── Gemfile
└── README.md
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

MIT License - see LICENSE file for details
