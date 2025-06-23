# Contributing to ThriveAds Platform

Thank you for your interest in contributing to ThriveAds Platform! This document provides guidelines and information for contributors.

## 🚀 Getting Started

### Prerequisites
- Node.js 18+
- Python 3.11+
- PostgreSQL 15+
- Git
- Meta Developer Account (for API testing)

### Development Setup
1. Fork the repository
2. Clone your fork: `git clone https://github.com/your-username/thriveads-platform.git`
3. Run setup script: `./setup-dev.sh`
4. Configure environment variables
5. Start development servers

## 📋 Development Guidelines

### Code Style

#### Python (Backend)
- Follow PEP 8 style guide
- Use Black for code formatting: `black .`
- Use isort for import sorting: `isort .`
- Type hints are required for all functions
- Docstrings required for all public functions

#### TypeScript/React (Frontend)
- Follow ESLint configuration
- Use Prettier for formatting
- Functional components with hooks preferred
- TypeScript strict mode enabled

### Commit Messages
Use conventional commit format:
```
type(scope): description

feat(api): add conversion funnel endpoint
fix(ui): resolve ROAS calculation display issue
docs(readme): update installation instructions
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

### Branch Naming
- Feature branches: `feature/description-of-feature`
- Bug fixes: `fix/description-of-bug`
- Documentation: `docs/description-of-change`

## 🧪 Testing

### Backend Testing
```bash
cd thriveads-backend
source venv/bin/activate
pytest -v
pytest --cov=app tests/
```

### Frontend Testing
```bash
cd thriveads-client-platform
npm test
npm run test:coverage
```

### Integration Testing
- Test Meta API integration with sandbox data
- Verify database migrations work correctly
- Test API endpoints with real data

## 📊 Database Changes

### Migrations
1. Create migration: `alembic revision --autogenerate -m "description"`
2. Review generated migration file
3. Test migration: `alembic upgrade head`
4. Test rollback: `alembic downgrade -1`

### Schema Changes
- Always create migrations for schema changes
- Include both upgrade and downgrade functions
- Test with production-like data volumes
- Document breaking changes

## 🔍 Code Review Process

### Pull Request Requirements
- [ ] All tests pass
- [ ] Code follows style guidelines
- [ ] Documentation updated if needed
- [ ] Migration files included for DB changes
- [ ] Environment variables documented
- [ ] Performance impact considered

### Review Checklist
- Code quality and readability
- Security considerations (especially API keys)
- Performance implications
- Database query efficiency
- Error handling completeness

## 🚀 Deployment

### Staging Environment
- Automatic deployment from `develop` branch
- Test with real Meta API data
- Verify database migrations

### Production Deployment
- Manual deployment from `main` branch
- Requires approval from maintainers
- Database backup before migration
- Rollback plan documented

## 📚 Documentation

### Required Documentation
- API endpoint documentation
- Database schema changes
- Environment variable updates
- Deployment procedure changes

### Documentation Standards
- Clear, concise explanations
- Code examples where helpful
- Screenshots for UI changes
- API response examples

## 🐛 Bug Reports

### Bug Report Template
```markdown
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior.

**Expected behavior**
What you expected to happen.

**Screenshots**
If applicable, add screenshots.

**Environment:**
- OS: [e.g. macOS, Windows]
- Browser: [e.g. Chrome, Safari]
- Version: [e.g. 1.0.0]
```

## 💡 Feature Requests

### Feature Request Template
```markdown
**Is your feature request related to a problem?**
A clear description of what the problem is.

**Describe the solution you'd like**
A clear description of what you want to happen.

**Additional context**
Any other context about the feature request.
```

## 🔒 Security

### Security Guidelines
- Never commit API keys or secrets
- Use environment variables for sensitive data
- Follow OWASP security guidelines
- Report security issues privately

### Reporting Security Issues
Email security issues to: [security@thriveads.com]
Do not create public issues for security vulnerabilities.

## 📞 Getting Help

- Create an issue for bugs or feature requests
- Join our Discord for development discussions
- Check existing issues before creating new ones
- Use clear, descriptive titles

## 📄 License

By contributing, you agree that your contributions will be licensed under the same license as the project.

Thank you for contributing to ThriveAds Platform! 🚀
