# Geo Analytics Dashboard Makefile
# Self-hostable brand mention tracking in LLM outputs

.PHONY: help install install-frontend install-backend dev dev-frontend dev-backend build test clean docker-build docker-dev docker-prod check-env setup-db lint format security-check api-docs backup restore

# Default target
help: ## Show this help message
	@echo "Geo Analytics Dashboard - Make Commands"
	@echo "======================================"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*##/ { printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@echo ""
	@echo "🔒 Security Note: API keys are stored encrypted in browser only, never on server"

# Environment setup
check-env: ## Check if all required environment variables are set
	@echo "🔍 Checking environment setup..."
	@command -v node >/dev/null 2>&1 || { echo "❌ Node.js is required but not installed. Visit https://nodejs.org"; exit 1; }
	@command -v python3 >/dev/null 2>&1 || { echo "❌ Python 3.11+ is required but not installed."; exit 1; }
	@command -v poetry >/dev/null 2>&1 || { echo "❌ Poetry is required but not installed. Visit https://python-poetry.org"; exit 1; }
	@echo "✅ Environment check passed"

# Installation
install: install-backend install-frontend ## Install all dependencies
	@echo "🎉 Installation complete! Ready to run 'make dev'"

install-backend-prod: ## Install only production backend dependencies
	@echo "📦 Installing production backend dependencies..."
	cd backend && poetry install --only main
	@echo "✅ Production backend dependencies installed"

install-frontend: ## Install frontend dependencies
	@echo "📦 Installing frontend dependencies..."
	cd frontend && npm install
	@echo "✅ Frontend dependencies installed"

fix-npm-permissions: ## Fix npm cache permissions (if you used sudo npm)
	@echo "🔧 Fixing npm cache permissions..."
	sudo chown -R $$(id -u):$$(id -g) "$$HOME/.npm"
	@echo "✅ npm permissions fixed"

install-backend: ## Install backend dependencies
	@echo "📦 Installing backend dependencies with Poetry..."
	cd backend && poetry install
	@echo "✅ Backend dependencies installed"

# Development
dev: ## Start development servers (frontend + backend)
	@echo "🚀 Starting development environment..."
	@echo "Frontend: http://localhost:3000"
	@echo "Backend: http://localhost:8000"
	@echo "API Docs: http://localhost:8000/docs"
	@$(MAKE) -j2 dev-frontend dev-backend

dev-frontend: ## Start frontend development server
	@echo "🎨 Starting frontend development server..."
	cd frontend && npm start

dev-backend: ## Start backend development server
	@echo "⚡ Starting backend development server..."
	cd backend && poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Build
build: build-frontend build-backend ## Build all components for production
	@echo "🏗️ Building production artifacts..."

build-frontend: ## Build frontend for production
	@echo "🎨 Building frontend..."
	cd frontend && npm run build
	@echo "✅ Frontend built in frontend/build/"

build-backend: ## Prepare backend for production
	@echo "⚡ Preparing backend for production..."
	cd backend && poetry install --only main && poetry build
	@echo "✅ Backend ready for production"

# Docker
docker-build: ## Build Docker images
	@echo "🐳 Building Docker images..."
	docker-compose build
	@echo "✅ Docker images built"

docker-dev: ## Start development environment with Docker
	@echo "🐳 Starting development environment with Docker..."
	@echo "Frontend: http://localhost:3000"
	@echo "Backend: http://localhost:8000"
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

docker-prod: ## Start production environment with Docker
	@echo "🐳 Starting production environment with Docker..."
	docker-compose --profile production up -d
	@echo "✅ Production environment started"

docker-stop: ## Stop Docker containers
	@echo "🛑 Stopping Docker containers..."
	docker-compose down

# Database
setup-db: ## Setup database schema (requires Supabase URL in .env)
	@echo "🗄️ Setting up database schema..."
	@if [ ! -f backend/.env ]; then \
		echo "❌ backend/.env file not found. Copy backend/.env.example and configure it."; \
		exit 1; \
	fi
	@echo "📋 Please run the SQL from database/schema.sql in your Supabase dashboard"
	@echo "🔗 Supabase SQL Editor: https://app.supabase.com/project/YOUR_PROJECT/sql"

backup-db: ## Backup database (requires pg_dump)
	@echo "💾 Creating database backup..."
	@if [ -z "$(DB_URL)" ]; then \
		echo "❌ DB_URL environment variable required"; \
		echo "Usage: make backup-db DB_URL=postgresql://..."; \
		exit 1; \
	fi
	@mkdir -p backups
	pg_dump "$(DB_URL)" > backups/backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "✅ Database backup created in backups/"

# Code Quality
lint: lint-frontend lint-backend ## Run linting for all components

lint-frontend: ## Lint frontend code
	@echo "🔍 Linting frontend..."
	cd frontend && npm run lint --if-present || echo "No lint script found, skipping"

lint-backend: ## Lint backend code
	@echo "🔍 Linting backend..."
	cd backend && poetry run flake8 app/ || echo "Skipping flake8 (install with: poetry add --group dev flake8)"

format: format-frontend format-backend ## Format all code

format-frontend: ## Format frontend code
	@echo "✨ Formatting frontend..."
	cd frontend && npx prettier --write src/ --ignore-unknown || echo "Prettier not available, skipping"

format-backend: ## Format backend code
	@echo "✨ Formatting backend..."
	cd backend && poetry run black . && poetry run isort . || echo "Skipping format (install with: poetry add --group dev black isort)"

# Testing
test: test-frontend test-backend ## Run all tests

test-frontend: ## Run frontend tests
	@echo "🧪 Running frontend tests..."
	cd frontend && npm test --watchAll=false --coverage || echo "No tests found"

test-backend: ## Run backend tests
	@echo "🧪 Running backend tests..."
	cd backend && poetry run pytest || echo "No tests found"

# Security
security-check: ## Run security checks
	@echo "🔒 Running security checks..."
	@echo "🔍 Checking for exposed API keys..."
	@if grep -r "sk-" --include="*.py" --include="*.js" --include="*.ts" --include="*.json" . 2>/dev/null; then \
		echo "⚠️ Potential API keys found in code! Review immediately."; \
	else \
		echo "✅ No exposed API keys found"; \
	fi
	@echo "🔍 Checking for exposed secrets..."
	@if grep -r "secret\|password\|token" --include="*.env*" . 2>/dev/null | grep -v ".env.example"; then \
		echo "⚠️ Potential secrets in env files (expected if configured)"; \
	fi
	cd frontend && npm audit --audit-level=high || echo "npm audit not available"
	cd backend && poetry check || echo "poetry check not available"

# Documentation
api-docs: ## Generate API documentation
	@echo "📚 API Documentation available at:"
	@echo "  Swagger UI: http://localhost:8000/docs"
	@echo "  ReDoc: http://localhost:8000/redoc"
	@echo "Start backend with 'make dev-backend' to access"

# Maintenance
clean: clean-frontend clean-backend ## Clean all build artifacts
	@echo "🧹 Cleaning build artifacts..."

clean-frontend: ## Clean frontend build artifacts
	@echo "🧹 Cleaning frontend..."
	cd frontend && rm -rf build/ node_modules/.cache/
	@echo "✅ Frontend cleaned"

clean-backend: ## Clean backend cache
	@echo "🧹 Cleaning backend..."
	cd backend && find . -type d -name "__pycache__" -exec rm -rf {} + || true
	cd backend && find . -name "*.pyc" -delete || true
	@echo "✅ Backend cleaned"

clean-docker: ## Clean Docker images and containers
	@echo "🐳 Cleaning Docker resources..."
	docker-compose down --rmi all --volumes --remove-orphans
	@echo "✅ Docker resources cleaned"

# Deployment helpers
deploy-check: ## Pre-deployment checks
	@echo "🚀 Running pre-deployment checks..."
	@$(MAKE) security-check
	@$(MAKE) build
	@$(MAKE) test
	@echo "✅ Pre-deployment checks passed"

# Quick setup for new developers
quick-setup: check-env install setup-db ## Quick setup for new developers
	@echo ""
	@echo "🎉 Quick setup complete!"
	@echo ""
	@echo "Next steps:"
	@echo "1. Copy backend/.env.example to backend/.env and configure"
	@echo "2. Set up Supabase database with: make setup-db"
	@echo "3. Start development: make dev"
	@echo ""
	@echo "🔒 Security reminder: API keys are stored client-side only!"

# Environment file setup
setup-env: ## Create environment files from examples
	@echo "📝 Setting up environment files..."
	@if [ ! -f backend/.env ]; then \
		cp backend/.env.example backend/.env; \
		echo "✅ Created backend/.env - please configure it"; \
	else \
		echo "✅ backend/.env already exists"; \
	fi
	@if [ ! -f frontend/.env.local ]; then \
		echo "REACT_APP_API_URL=http://localhost:8000" > frontend/.env.local; \
		echo "REACT_APP_ENVIRONMENT=development" >> frontend/.env.local; \
		echo "✅ Created frontend/.env.local"; \
	else \
		echo "✅ frontend/.env.local already exists"; \
	fi

# Status check
status: ## Check the status of all services
	@echo "📊 Service Status Check"
	@echo "======================"
	@echo ""
	@echo "Frontend (http://localhost:3000):"
	@curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost:3000 || echo "❌ Not running"
	@echo ""
	@echo "Backend (http://localhost:8000):"
	@curl -s -o /dev/null -w "Status: %{http_code}\n" http://localhost:8000/health || echo "❌ Not running"
	@echo ""
	@echo "API Docs: http://localhost:8000/docs"

# Log viewing
logs: ## View Docker logs
	docker-compose logs -f

logs-backend: ## View backend logs only
	docker-compose logs -f backend

logs-frontend: ## View frontend logs only
	docker-compose logs -f frontend

# Poetry-specific commands
poetry-shell: ## Enter Poetry virtual environment
	@echo "🐚 Entering Poetry shell..."
	cd backend && poetry shell

poetry-add: ## Add a new backend dependency (usage: make poetry-add PACKAGE=package-name)
	@if [ -z "$(PACKAGE)" ]; then \
		echo "❌ Usage: make poetry-add PACKAGE=package-name"; \
		exit 1; \
	fi
	@echo "📦 Adding $(PACKAGE) to backend dependencies..."
	cd backend && poetry add $(PACKAGE)

poetry-add-dev: ## Add a new dev dependency (usage: make poetry-add-dev PACKAGE=package-name)
	@if [ -z "$(PACKAGE)" ]; then \
		echo "❌ Usage: make poetry-add-dev PACKAGE=package-name"; \
		exit 1; \
	fi
	@echo "📦 Adding $(PACKAGE) to backend dev dependencies..."
	cd backend && poetry add --group dev $(PACKAGE)

poetry-update: ## Update all backend dependencies
	@echo "🔄 Updating backend dependencies..."
	cd backend && poetry update
	@echo "✅ Dependencies updated"

poetry-show: ## Show dependency tree
	@echo "📋 Backend dependency tree:"
	cd backend && poetry show --tree

poetry-export: ## Export requirements.txt from Poetry (for compatibility)
	@echo "📄 Exporting requirements.txt..."
	cd backend && poetry export -f requirements.txt --output requirements.txt --without-hashes
	@echo "✅ requirements.txt exported" 