# Project Summary: E-Commerce Microservices

## 🎯 Purpose

This repository demonstrates a realistic microservices architecture designed to showcase **Codity's automated test generation** capabilities across Go, Python, and Ruby.

## 📁 Repository Structure

```
ecommerce-microservices/
├── .github/workflows/          # CI/CD Configuration
│   ├── go-tests.yml           # Go service tests
│   ├── python-tests.yml       # Python service tests
│   └── ruby-tests.yml         # Ruby service tests
│
├── auth-service/              # 🔐 Go Authentication Service
│   ├── cmd/main.go           # Entry point
│   ├── internal/
│   │   ├── handlers/         # JWT token management
│   │   │   └── auth.go       # Auth handlers (Register, Login, Validate)
│   │   └── models/           # Data models
│   │       └── user.go       # User model with validation
│   └── go.mod                # Go dependencies
│
├── analytics-service/         # 📊 Python Analytics Service
│   ├── src/
│   │   ├── main.py           # Entry point
│   │   ├── models/           # Data models
│   │   │   └── metrics.py    # Sales & user metrics
│   │   └── services/         # Business logic
│   │       └── analytics.py  # Analytics processing
│   └── requirements.txt      # Python dependencies
│
├── api-gateway/              # 🌐 Ruby API Gateway
│   ├── app/
│   │   ├── gateway.rb        # Main Sinatra app
│   │   ├── controllers/      # Request handlers
│   │   │   ├── router.rb     # Service routing logic
│   │   │   └── rate_limiter.rb # Rate limiting
│   │   └── models/           # Data models
│   │       └── request_logger.rb # Request logging
│   └── Gemfile               # Ruby dependencies
│
├── README.md                  # Main documentation
├── QUICKSTART.md             # Quick start guide
├── CONTRIBUTING.md           # Contribution guidelines
├── LICENSE                   # MIT License
├── verify-setup.sh           # Setup verification script
└── .gitignore                # Git ignore rules
```

## 🏗️ Architecture

### Auth Service (Go)
**Port:** 8080
**Responsibility:** User authentication and JWT token management

**Key Features:**
- Email validation with regex
- Password strength validation (8+ chars, uppercase, lowercase, numbers)
- Bcrypt password hashing
- JWT token generation and validation
- In-memory user storage

**Functions to Test:**
- `ValidateEmail()` - Email format validation
- `ValidatePassword()` - Password strength checks
- `HashPassword()` - Password hashing
- `CheckPasswordHash()` - Password verification
- `NewUser()` - User creation with validation
- `Register()` - User registration flow
- `Login()` - Authentication and token generation
- `ValidateToken()` - JWT token validation

### Analytics Service (Python)
**Port:** 8000
**Responsibility:** Sales and user metrics processing

**Key Features:**
- Sales tracking and metrics calculation
- User registration and activity tracking
- Event tracking system
- Growth rate calculations
- Metrics aggregation

**Functions to Test:**
- `calculate_average()` - Average calculation
- `calculate_growth_rate()` - Growth percentage
- `filter_by_date_range()` - Date filtering
- `track_sale()` - Sales recording
- `get_sales_metrics()` - Sales aggregation
- `register_user()` - User registration
- `get_user_metrics()` - User statistics
- `track_event()` - Event logging
- `get_top_events()` - Event ranking
- `calculate_revenue_growth()` - Revenue trends

### API Gateway (Ruby)
**Port:** 3000
**Responsibility:** Request routing and rate limiting

**Key Features:**
- Dynamic service routing
- Per-client rate limiting (100 req/min)
- Request logging with metrics
- Error handling
- Health check endpoint

**Functions to Test:**
- `Router#route()` - Service routing
- `Router#determine_service()` - Path parsing
- `Router#build_url()` - URL construction
- `Router#validate_path()` - Path validation
- `RateLimiter#allow?()` - Rate limit checking
- `RateLimiter#remaining_requests()` - Quota checking
- `RateLimiter#reset_time()` - Reset time calculation
- `RequestLogger#log_request()` - Request logging
- `RequestLogger#get_error_logs()` - Error filtering
- `RequestLogger#get_average_response_time()` - Performance metrics

## 🧪 Testing with Codity

### Expected Workflow

1. **Make a code change** to any service
2. **Create a PR** on GitHub
3. **Codity analyzes** the PR and detects:
   - Changed Go files → Generates Go tests with testify
   - Changed Python files → Generates pytest tests
   - Changed Ruby files → Generates RSpec tests

4. **Codity creates a test PR** with:
   - Comprehensive unit tests (10-20+ per file)
   - Edge cases and error conditions
   - Language-specific best practices

5. **CI runs automatically**:
   - GitHub Actions executes test suites
   - Codity monitors CI status
   - Auto-fixes failing tests (up to 3 attempts)

6. **Review and merge**:
   - Review generated tests
   - Merge when CI passes

### Example Test Scenarios

**Go (auth-service):**
- Valid email formats
- Invalid email formats
- Password strength validation
- JWT token generation
- Token expiration
- Bcrypt hashing

**Python (analytics-service):**
- Sales metrics calculation
- Zero sales edge case
- User retention rate
- Growth rate with zero previous
- Date range filtering
- Event tracking

**Ruby (api-gateway):**
- Route matching patterns
- Rate limit enforcement
- Request logging
- Error handling
- Health check endpoint
- Client quota tracking

## 🚀 Quick Start

```bash
# Verify setup
./verify-setup.sh

# Run services (in separate terminals)
cd auth-service && go run cmd/main.go
cd analytics-service && python src/main.py
cd api-gateway && ruby app/gateway.rb

# Run tests
cd auth-service && go test -v ./...
cd analytics-service && pytest -v
cd api-gateway && bundle exec rspec
```

## 📊 CI/CD Configuration

All three workflows are configured to run on:
- `pull_request.opened`
- `pull_request.synchronize`
- `pull_request.reopened`

Each workflow:
- ✅ Runs on Ubuntu latest
- ✅ Sets up language environment
- ✅ Installs dependencies
- ✅ Runs tests with verbose output
- ✅ Generates coverage reports

## 💡 Why This Repository?

This project demonstrates:

1. **Realistic codebase** - Not just "hello world", but actual business logic
2. **Multi-language** - Tests Go, Python, and Ruby support
3. **Complex functions** - Validation, calculations, business rules
4. **Edge cases** - Empty inputs, invalid data, boundary conditions
5. **CI integration** - Production-ready GitHub Actions workflows
6. **Codity showcase** - Perfect for demonstrating automated test generation

## 📈 Metrics

- **10 source files** across 3 languages
- **30+ functions** to test
- **3 CI workflows** for automated testing
- **Comprehensive documentation** (README, QUICKSTART, CONTRIBUTING)

## 🎯 Next Steps

1. **Push to GitHub** and set up Codity integration
2. **Create a feature branch** with code changes
3. **Open a PR** and watch Codity generate tests
4. **Monitor CI** as tests run automatically
5. **Observe auto-fix** handling any failures

---

**Ready to see Codity in action!** 🚀
