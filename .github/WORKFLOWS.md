# GitHub Workflows for LLMDistiller

This directory contains comprehensive GitHub Actions workflows for the LLMDistiller project, providing automated CI/CD, security scanning, quality assurance, and release management.

## 🚀 Workflow Overview

### Core Workflows

| Workflow | Purpose | Triggers | Status |
|-----------|---------|-----------|--------|
| **CI/CD Pipeline** | Continuous integration and testing | Push to main/develop, PRs | ✅ Active |
| **Release** | Automated PyPI publishing | Tags, manual dispatch | ✅ Active |
| **Documentation** | Build and deploy docs | Push to main, PRs, releases | ✅ Active |
| **Performance** | Performance monitoring and benchmarking | Push to main, schedule, manual | ✅ Active |
| **Dependencies** | Dependency management and updates | Daily schedule, manual | ✅ Active |
| **Quality** | Code quality analysis and dashboard | Push, PRs, weekly schedule | ✅ Active |
| **Security** | Comprehensive security scanning | Push, PRs, daily schedule | ✅ Active |

## 📋 Detailed Workflow Descriptions

### 1. CI/CD Pipeline (`ci.yml`)

**Purpose**: Comprehensive testing and validation of code changes.

**Features**:
- ✅ **Multi-Python Testing**: Python 3.9, 3.10, 3.11
- ✅ **Database Testing**: SQLite and PostgreSQL integration
- ✅ **Code Quality**: Black, isort, flake8, mypy
- ✅ **Security Scanning**: Bandit and Safety
- ✅ **Coverage Reporting**: Unit and integration tests with coverage
- ✅ **CLI Testing**: End-to-end CLI command validation
- ✅ **Package Building**: Wheel and source distribution creation

**Jobs**:
- `quality`: Code formatting and linting
- `security`: Security vulnerability scanning
- `test`: Matrix testing across Python versions and databases
- `cli-test`: CLI functionality testing
- `build`: Package creation and validation
- `performance`: Performance benchmarking (main branch only)
- `status`: Overall CI status check

### 2. Release Workflow (`release.yml`)

**Purpose**: Automated release management and PyPI publishing.

**Features**:
- 🏷️ **Version Validation**: Semantic versioning checks
- 📦 **Package Building**: Automated wheel and source distribution
- 🧪 **Release Testing**: Comprehensive testing of release candidates
- 📝 **Changelog Generation**: Automatic changelog from git history
- 🚀 **PyPI Publishing**: Automated publishing to PyPI and Test PyPI
- 🏷️ **GitHub Releases**: Automatic GitHub release creation

**Jobs**:
- `prepare`: Version validation and preparation
- `build`: Package building and validation
- `test-release`: Testing of release candidate
- `github-release`: GitHub release creation
- `publish-pypi`: Production PyPI publishing
- `publish-test-pypi`: Test PyPI publishing (prereleases)
- `notify`: Release status notification

### 3. Documentation Workflow (`docs.yml`)

**Purpose**: Automated documentation building and deployment.

**Features**:
- 📚 **MkDocs Building**: Modern documentation with Material theme
- 🌐 **GitHub Pages Deployment**: Automatic deployment to GitHub Pages
- 🔍 **Link Checking**: Internal link validation
- 📊 **Quality Metrics**: Documentation coverage and statistics
- 🏷️ **Versioned Docs**: Versioned documentation for releases
- 🔧 **API Documentation**: Auto-generated API docs from docstrings

**Jobs**:
- `build`: Documentation building and validation
- `deploy`: GitHub Pages deployment (main branch)
- `deploy-versioned`: Versioned documentation (releases)
- `quality`: Documentation quality checks
- `notify`: Documentation deployment status

### 4. Performance Monitoring (`performance.yml`)

**Purpose**: Performance testing, benchmarking, and regression detection.

**Features**:
- ⚡ **Benchmark Testing**: pytest-benchmark integration
- 📊 **Performance Trends**: Historical performance tracking
- 🔍 **Regression Detection**: Automated performance regression alerts
- 💾 **Memory Profiling**: Memory usage analysis
- 🔄 **Load Testing**: Concurrent operation testing
- 📈 **Performance Reports**: Detailed performance analysis

**Jobs**:
- `performance-tests`: Benchmark execution and profiling
- `load-testing`: Concurrent load testing
- `regression-detection`: Performance regression analysis
- `summary`: Performance summary and recommendations

### 5. Dependency Management (`dependencies.yml`)

**Purpose**: Automated dependency updates and vulnerability management.

**Features**:
- 🔍 **Vulnerability Scanning**: Safety and pip-audit integration
- 🔄 **Automated Updates**: pip-tools based dependency updates
- 📄 **License Compliance**: License analysis and reporting
- 📊 **Health Scoring**: Dependency health assessment
- 🚨 **Security Alerts**: Automated vulnerability notifications

**Jobs**:
- `vulnerability-scan`: Security vulnerability scanning
- `dependency-update`: Automated dependency updates
- `license-check`: License compliance verification
- `health-score`: Dependency health assessment
- `summary`: Dependency management summary

### 6. Code Quality Dashboard (`quality.yml`)

**Purpose**: Comprehensive code quality analysis and reporting.

**Features**:
- 📊 **Complexity Analysis**: Cyclomatic complexity and maintainability
- 🦅 **Dead Code Detection**: Vulture integration for unused code
- 📝 **Documentation Analysis**: Docstring coverage and quality
- 🎯 **Quality Scoring**: Multi-dimensional quality metrics
- 📈 **Trend Tracking**: Quality metrics over time
- 💡 **Recommendations**: Actionable improvement suggestions

**Jobs**:
- `quality-analysis`: Code complexity and quality metrics
- `security-quality`: Security-focused quality analysis
- `test-quality`: Test coverage and quality analysis
- `dashboard`: Comprehensive quality dashboard

### 7. Security Scanning (`security.yml`)

**Purpose**: Comprehensive security vulnerability scanning and analysis.

**Features**:
- 🔍 **SAST**: Static Application Security Testing (Bandit, Semgrep)
- 🔐 **Secrets Detection**: TruffleHog for exposed secrets
- 📦 **Dependency Security**: Safety and pip-audit integration
- 🐳 **Container Security**: Trivy container scanning (if Dockerfile exists)
- 📊 **Security Scoring**: Overall security assessment
- 🚨 **Alerting**: Automated security issue notifications

**Jobs**:
- `sast`: Static application security testing
- `dependency-security`: Dependency vulnerability scanning
- `container-security`: Container security analysis
- `security-score`: Overall security scoring
- `summary`: Security scanning summary

## 🔧 Configuration

### Required Secrets

To enable all workflow features, configure these repository secrets:

| Secret | Purpose | Required For |
|--------|---------|---------------|
| `PYPI_API_TOKEN` | PyPI publishing token | Release workflow |
| `TEST_PYPI_API_TOKEN` | Test PyPI token | Release workflow (prereleases) |
| `CODECOV_TOKEN` | Codecov integration | CI/CD pipeline |
| `GOOGLE_ANALYTICS_KEY` | Documentation analytics | Documentation workflow |

### Environment Variables

Workflows use these environment variables:

- `PYTHON_DEFAULT_VERSION`: Default Python version (3.11)
- `GITHUB_TOKEN`: Automatically provided by GitHub Actions

### Workflow Permissions

Workflows require these permissions:

```yaml
permissions:
  contents: read
  pages: write          # For documentation deployment
  id-token: write       # For PyPI trusted publishing
  actions: read         # For artifact access
  security-events: write # For security reporting
```

## 📊 Monitoring and Reporting

### Status Badges

Add these badges to your README.md:

```markdown
![CI/CD](https://github.com/llm-distiller/LLMDistiller/workflows/CI%2FCD%20Pipeline/badge.svg)
![Security](https://github.com/llm-distiller/LLMDistiller/workflows/Security%20Scanning/badge.svg)
![Code Quality](https://github.com/llm-distiller/LLMDistiller/workflows/Code%20Quality%20Dashboard/badge.svg)
![Documentation](https://github.com/llm-distiller/LLMDistiller/workflows/Documentation/badge.svg)
![Performance](https://github.com/llm-distiller/LLMDistiller/workflows/Performance%20Monitoring/badge.svg)
```

### Artifacts and Reports

Workflows generate these artifacts:

| Workflow | Artifacts | Retention |
|-----------|------------|------------|
| CI/CD | Test results, coverage reports, build artifacts | 30 days |
| Security | Security scan reports, vulnerability data | 30 days |
| Performance | Benchmark results, profiling data | 30 days |
| Quality | Code quality reports, metrics | 30 days |
| Dependencies | Vulnerability reports, license data | 30 days |

### Notifications

Workflows provide notifications through:

- **GitHub Summary**: Detailed reports in Actions tab
- **Pull Request Comments**: Automated PR feedback
- **Issues**: Security issue creation for critical findings
- **Release Notes**: Automated changelog generation

## 🚀 Getting Started

### 1. Enable Workflows

1. Push workflows to `.github/workflows/` directory
2. Configure required secrets
3. Set up repository permissions
4. Enable GitHub Pages (for documentation)

### 2. Configure Environment

```bash
# Set up Python environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or venv\Scripts\activate  # Windows

# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

### 3. Test Workflows

```bash
# Test CI locally
pytest tests/
black --check src/ tests/
isort --check-only src/ tests/
flake8 src/ tests/
mypy src/

# Test security scanning
bandit -r src/
safety check

# Test documentation
mkdocs build
```

## 🔄 Workflow Triggers

### Automatic Triggers

- **Push to main/develop**: CI/CD, security, quality, documentation
- **Pull Requests**: CI/CD, security, quality, documentation
- **Tags**: Release workflow
- **Schedule**: Daily security scans, weekly dependency updates

### Manual Triggers

All workflows support manual dispatch through GitHub Actions UI:

1. Go to Actions tab
2. Select workflow
3. Click "Run workflow"
4. Configure parameters (if applicable)

## 🛠️ Customization

### Adding New Checks

To add new quality checks:

1. Update relevant workflow file
2. Add new job or step
3. Configure artifact upload
4. Update reporting logic

### Modifying Triggers

Change workflow triggers in the `on:` section:

```yaml
on:
  push:
    branches: [ main, develop ]
    paths: ['src/**']  # Only run on src changes
  pull_request:
    branches: [ main ]
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM UTC
  workflow_dispatch:
```

### Environment-Specific Configuration

Use environment-specific configurations:

```yaml
jobs:
  test:
    strategy:
      matrix:
        environment: [dev, staging, prod]
    steps:
      - name: Configure
        run: |
          if [[ "${{ matrix.environment }}" == "prod" ]]; then
            echo "Production configuration"
          fi
```

## 📈 Best Practices

### 1. Workflow Optimization

- Use caching for dependencies
- Parallelize independent jobs
- Use matrix strategies for multiple configurations
- Implement proper error handling

### 2. Security Best Practices

- Regularly update workflow dependencies
- Use least privilege principle for permissions
- Rotate secrets regularly
- Monitor security scan results

### 3. Performance Optimization

- Use self-hosted runners for large builds
- Implement artifact retention policies
- Optimize Docker layer caching
- Monitor workflow execution times

### 4. Maintenance

- Regularly review and update workflows
- Monitor workflow failures and alerts
- Keep dependencies up to date
- Document workflow changes

## 🔗 Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Workflow Syntax Reference](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)
- [Security Hardening for GitHub Actions](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions)
- [Best Practices for GitHub Actions](https://docs.github.com/en/actions/using-workflows/best-practices-for-github-actions)

---

## 📞 Support

For workflow issues:

1. Check workflow logs in Actions tab
2. Review this documentation
3. Search existing GitHub Issues
4. Create new issue with details

*Last updated: December 2024*