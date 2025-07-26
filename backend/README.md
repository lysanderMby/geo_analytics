# Geo Analytics Backend

Self-hostable dashboard backend for tracking brand mentions in LLM outputs.

## 🚀 Quick Start with Poetry

### Prerequisites
- Python 3.11+
- Poetry (already installed)
- Supabase account for database

### Installation

```bash
# Navigate to backend directory
cd backend

# Install dependencies
poetry install

# Create environment file
cp .env.example .env  # Then configure with your values

# Activate virtual environment
poetry shell

# Start development server
poetry run start
```

### Environment Configuration

Create `.env` file in the backend directory:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key-here

# Security Configuration
SECRET_KEY=your-super-secret-key-for-jwt-tokens-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS Settings (comma-separated list)
ALLOWED_HOSTS=http://localhost:3000,http://127.0.0.1:3000

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60

# Environment
ENVIRONMENT=development

# Logging
LOG_LEVEL=INFO
```

## 📦 Poetry Commands

### Dependency Management
```bash
# Add a new dependency
poetry add package-name

# Add development dependency
poetry add --group dev package-name

# Update dependencies
poetry update

# Show dependency tree
poetry show --tree

# Export requirements (if needed)
poetry export -f requirements.txt --output requirements.txt
```

### Development
```bash
# Install dependencies (including dev)
poetry install

# Install only production dependencies
poetry install --only main

# Activate virtual environment
poetry shell

# Run commands in virtual environment
poetry run python main.py
poetry run uvicorn main:app --reload

# Use predefined scripts
poetry run start      # Development server
poetry run start-prod # Production server
```

### Code Quality
```bash
# Format code
poetry run black .

# Sort imports
poetry run isort .

# Lint code
poetry run flake8 app/

# Type checking
poetry run mypy app/

# Run tests
poetry run pytest

# Run tests with coverage
poetry run coverage run -m pytest
poetry run coverage report
```

## 🛠️ Development Workflow

1. **Setup Environment:**
   ```bash
   poetry install
   poetry shell
   ```

2. **Run Development Server:**
   ```bash
   poetry run start
   ```

3. **Code Quality Checks:**
   ```bash
   poetry run black .
   poetry run isort .
   poetry run flake8 app/
   poetry run mypy app/
   ```

4. **Testing:**
   ```bash
   poetry run pytest
   ```

## 📚 API Documentation

When running the development server, API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🔒 Security Features

- **Client-side API Key Storage**: User API keys are never stored on the server
- **Row Level Security**: Database access isolated per user
- **JWT Authentication**: Secure session management
- **CORS Protection**: Configurable allowed origins
- **Rate Limiting**: API request throttling

## 🗄️ Database Schema

The database schema is defined in `../database/schema.sql`. Apply it to your Supabase instance through the Supabase dashboard SQL editor.

## 📁 Project Structure

```
backend/
├── app/
│   ├── api/           # API route handlers
│   ├── core/          # Core configuration
│   ├── database/      # Database client
│   ├── models/        # Pydantic schemas
│   └── services/      # Business logic services
├── tests/             # Test files
├── main.py           # Application entry point
├── pyproject.toml    # Poetry configuration
└── README.md         # This file
```

## 🔧 Configuration

All configuration is handled through environment variables defined in `.env`. See the environment configuration section above for required variables.

## 🚀 Deployment

For production deployment:

```bash
# Install only production dependencies
poetry install --only main

# Start production server
poetry run start-prod
```

Or use Docker (see root `docker-compose.yml`). 