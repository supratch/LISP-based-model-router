# AI Workload Routing System

A comprehensive enterprise-grade system that implements intelligent routing for AI workloads using LISP (Locator/Identifier Separation Protocol) and DNS-based routing with a modern web interface for monitoring and management.

## 🚀 Features

### Core Routing Capabilities
- **LISP Routing Engine**: Advanced packet routing using EID-to-RLOC mapping for AI workload distribution
- **DNS-Based Load Balancing**: Intelligent service discovery with weighted load balancing and health checking
- **Multi-Model LLM Support**: Smart routing between GPT-4 and Claude-3 models based on query analysis
- **Enterprise Security**: CORS protection, authentication, and structured logging

### Monitoring & Management
- **Real-time Dashboard**: Live monitoring of routing performance and system health
- **Query Interface**: Interactive query submission with routing visualization
- **Model Management**: Dynamic configuration of AI models and routing parameters
- **Metrics & Analytics**: Comprehensive observability with Prometheus-compatible metrics

### Architecture Components
- **Backend**: Python FastAPI with async routing services
- **Frontend**: React TypeScript with Material-UI components
- **Configuration**: YAML-based configuration management
- **Logging**: Structured JSON logging with multiple log levels

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    AI Workload Routing System                    │
├─────────────────────────────────────────────────────────────────┤
│  Frontend (React TypeScript + Material-UI)                     │
│  ├─ Dashboard          ├─ Query Interface                       │
│  ├─ Monitoring         ├─ Model Management                      │
└─────────────────┬───────────────────────────────────────────────┘
                  │ HTTP/REST API
┌─────────────────▼───────────────────────────────────────────────┐
│  Backend (Python FastAPI)                                       │
│  ├─ API Routes         ├─ Authentication                        │
│  ├─ Monitoring Service ├─ Configuration Management              │
└─────────────────┬───────────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────────┐
│  Routing Layer                                                  │
│  ┌─────────────┬─────────────┬─────────────┐                   │
│  │ LISP Router │ DNS Router  │ LLM Router  │                   │
│  │             │             │             │                   │
│  │ ├─ EID Maps │ ├─ Service  │ ├─ Query    │                   │
│  │ ├─ RLOC     │ │   Registry│ │   Analysis│                   │
│  │ ├─ Control  │ ├─ Health   │ ├─ Model    │                   │
│  │ │   Plane   │ │   Checks  │ │   Select. │                   │
│  │ └─ Load Bal.│ └─ Weights  │ └─ Load Bal.│                   │
│  └─────────────┴─────────────┴─────────────┘                   │
└─────────────────┬───────────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────────┐
│  AI Model Endpoints                                             │
│  ├─ GPT-4 Primary      ├─ GPT-4 Secondary                      │
│  ├─ Claude-3 Primary   ├─ Claude-3 Backup                      │
│  └─ GPT-3.5 Fast      └─ [Additional Models...]                │
└─────────────────────────────────────────────────────────────────┘
```

## 📋 Prerequisites

- **Python 3.8+** with pip
- **Node.js 16+** with npm
- **Modern web browser** (Chrome, Firefox, Safari, Edge)
- **Git** for version control

## ⚡ Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd "Network Optimisations for AI"
```

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Install Python dependencies
python3 -m pip install --user -r requirements.txt

# Start the backend server
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

The backend will be available at:
- **API Base**: http://127.0.0.1:8000
- **API Documentation**: http://127.0.0.1:8000/docs
- **Health Check**: http://127.0.0.1:8000/health

### 3. Frontend Setup

```bash
# Navigate to frontend directory (in new terminal)
cd frontend

# Install Node.js dependencies
npm install

# Start the development server
npm start
```

The frontend will be available at:
- **Web Interface**: http://localhost:3000

### 4. Using the Startup Script

Alternatively, use the provided startup script:

```bash
# Make executable and run
chmod +x start_backend.py
python3 start_backend.py
```

## 🔧 Configuration

### System Configuration

Edit `config/config.yaml` to customize:

```yaml
# Server Configuration
server:
  host: "0.0.0.0"
  port: 8000
  debug: true

# LISP Configuration
lisp:
  control_port: 4342
  map_cache_ttl: 3600
  eid_prefixes:
    - "10.1.0.0/16"  # General AI workloads
    - "10.2.0.0/16"  # Fast response workloads
    - "10.3.0.0/16"  # Complex reasoning workloads

# LLM Model Configuration
models:
  gpt-4:
    endpoint: "192.168.1.100:8080"
    rate_limit: 60
    cost_per_token: 0.00003
    max_tokens: 8192
    
  claude-3:
    endpoint: "192.168.2.100:8080"
    rate_limit: 80
    cost_per_token: 0.000015
    max_tokens: 4096
```

### Model Endpoints

To connect actual AI model endpoints:

1. Update the `models` section in `config/config.yaml`
2. Ensure model endpoints are accessible from the backend server
3. Restart the backend service

## 📡 API Usage

### Route a Query

```bash
curl -X POST "http://127.0.0.1:8000/route" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Explain the concept of machine learning",
    "context": {"user_id": "12345", "session": "abc"},
    "priority": "high",
    "source_eid": "10.1.0.5"
  }'
```

### Check System Health

```bash
curl "http://127.0.0.1:8000/health"
```

### Get System Statistics

```bash
curl "http://127.0.0.1:8000/stats"
```

### List Available Models

```bash
curl "http://127.0.0.1:8000/models"
```

## 🖥️ Web Interface

The web interface provides:

### Dashboard
- **System Overview**: Real-time health status of all services
- **Performance Metrics**: Query routing statistics and response times
- **Model Status**: Live view of AI model availability and load

### Query Interface
- **Interactive Query Submission**: Test routing with various query types
- **Routing Visualization**: See how queries are routed through LISP/DNS
- **Response Analysis**: View detailed routing decisions and performance metrics

### Monitoring Dashboard
- **Real-time Charts**: CPU, memory, and network utilization
- **Routing Analytics**: Success rates, error rates, and latency metrics
- **Alert Management**: Configure and view system alerts

### Model Management
- **Model Configuration**: Adjust model parameters and routing weights
- **Load Balancing**: Configure traffic distribution between models
- **Health Monitoring**: View detailed model health and performance

## 🔍 Monitoring & Observability

### Structured Logging

All services use structured JSON logging:

```json
{
  "event": "Query routed successfully",
  "model": "gpt-4",
  "endpoint": "192.168.1.100:8080",
  "method": "LISP + DNS",
  "logger": "app.api.routes",
  "level": "info",
  "timestamp": "2025-11-25T10:30:45.123Z"
}
```

### Prometheus Metrics

Access metrics at `/metrics` endpoint for:
- Query routing statistics
- Model performance metrics
- System resource utilization
- Error rates and latencies

### Health Checks

Multiple health check endpoints:
- `/health` - Overall system health
- `/health/lisp` - LISP router status
- `/health/dns` - DNS router status  
- `/health/models` - AI model availability

## 🔐 Security Features

### CORS Protection
Configurable CORS origins for secure cross-origin requests

### Authentication
JWT-based authentication system (configure secret in config.yaml)

### Input Validation
Comprehensive input validation using Pydantic models

### Rate Limiting
Built-in rate limiting for API endpoints

## 🧪 Testing

### Backend Tests

```bash
cd backend
python3 -m pytest tests/ -v
```

### Frontend Tests

```bash
cd frontend
npm test
```

### Integration Tests

```bash
# Start both backend and frontend
# Then run integration tests
npm run test:integration
```

## 🚀 Production Deployment

### Docker Deployment

```bash
# Build images
docker build -t ai-routing-backend ./backend
docker build -t ai-routing-frontend ./frontend

# Run with docker-compose
docker-compose up -d
```

### Environment Variables

Set these environment variables in production:

```bash
export ENVIRONMENT=production
export JWT_SECRET=your-production-secret
export DATABASE_URL=postgresql://user:pass@host:5432/db
export REDIS_URL=redis://host:6379/0
```

### Load Balancer Configuration

For production, configure a load balancer:
- Backend: Multiple FastAPI instances behind nginx/HAProxy
- Frontend: Serve static React build from CDN
- Database: PostgreSQL with connection pooling
- Cache: Redis for session management

## 🐛 Troubleshooting

### Common Issues

#### Backend Server Won't Start
```bash
# Check Python version
python3 --version  # Should be 3.8+

# Check dependencies
python3 -m pip list | grep fastapi

# Check port availability
lsof -i :8000
```

#### Frontend Build Errors
```bash
# Clear npm cache
npm cache clean --force

# Delete node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Check Node.js version
node --version  # Should be 16+
```

#### Model Connection Errors
- Verify model endpoints in `config/config.yaml`
- Check network connectivity to model servers
- Ensure authentication credentials are correct
- Review logs for specific connection errors

#### LISP Routing Issues
- Verify EID prefix configuration
- Check RLOC endpoint availability
- Review map cache statistics
- Ensure control plane connectivity

### Debug Mode

Enable debug logging:

```yaml
# config/config.yaml
logging:
  level: "DEBUG"
  format: "json"
```

## 📊 Performance Tuning

### Backend Optimization
- Adjust uvicorn worker count: `--workers 4`
- Configure connection pooling for databases
- Implement caching with Redis
- Use async/await for I/O operations

### Frontend Optimization
- Enable React production build: `npm run build`
- Implement code splitting and lazy loading
- Configure CDN for static assets
- Use service workers for caching

### Network Optimization
- Configure DNS caching
- Implement connection keep-alive
- Use HTTP/2 for API communication
- Enable gzip compression

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -am 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Submit a pull request

### Code Style

- **Python**: Follow PEP 8, use Black formatter
- **TypeScript**: Use Prettier, follow TypeScript ESLint rules
- **Documentation**: Use clear, concise language with examples

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙋‍♂️ Support

For questions, issues, or contributions:
- Create an issue in the repository
- Review the troubleshooting section
- Check the API documentation at `/docs`

## 🔗 Related Technologies

- **LISP Protocol**: [RFC 6830](https://tools.ietf.org/html/rfc6830)
- **FastAPI**: [Official Documentation](https://fastapi.tiangolo.com/)
- **React**: [Official Documentation](https://reactjs.org/)
- **Material-UI**: [Component Library](https://mui.com/)
- **Prometheus**: [Monitoring Documentation](https://prometheus.io/docs/)

---

Built with ❤️ for enterprise AI workload optimization