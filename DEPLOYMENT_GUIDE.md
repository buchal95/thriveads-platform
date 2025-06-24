# ThriveAds Platform - Deployment Guide

## 🚀 Quick Start (Local Development)

### Prerequisites
- Python 3.9+
- Node.js 18+
- Meta API Access Token
- Meta Ad Account ID: 513010266454814

### 1. Backend Setup
```bash
cd thriveads-backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set environment variables
export META_ACCESS_TOKEN="your_meta_access_token"
export META_AD_ACCOUNT_ID="513010266454814"

# Run database migrations
alembic upgrade head

# Start backend server
python main.py
# Backend runs on http://localhost:8000
```

### 2. Frontend Setup
```bash
cd thriveads-client-platform
npm install
npm run dev
# Frontend runs on http://localhost:3001
```

### 3. Verify Installation
- Backend API: http://localhost:8000/docs
- Frontend: http://localhost:3001
- Health Check: http://localhost:8000/health

## 🌐 Production Deployment

### Backend (Railway)
1. **Create Railway Project**
   ```bash
   railway login
   railway init
   railway add postgresql
   ```

2. **Set Environment Variables**
   ```bash
   railway variables set META_ACCESS_TOKEN="your_token"
   railway variables set META_AD_ACCOUNT_ID="513010266454814"
   railway variables set DATABASE_URL="postgresql://..."
   railway variables set ENVIRONMENT="production"
   ```

3. **Deploy**
   ```bash
   railway up
   ```

### Frontend (Vercel)
1. **Connect Repository**
   - Link GitHub repository to Vercel
   - Set build command: `npm run build`
   - Set output directory: `.next`

2. **Environment Variables**
   ```
   NEXT_PUBLIC_API_URL=https://your-backend.railway.app
   ```

3. **Deploy**
   ```bash
   vercel --prod
   ```

## 🔧 Configuration

### Environment Variables

#### Backend (.env)
```env
# Meta API
META_ACCESS_TOKEN=your_meta_access_token
META_AD_ACCOUNT_ID=513010266454814

# Database
DATABASE_URL=postgresql://user:pass@host:port/db

# Application
ENVIRONMENT=production
LOG_LEVEL=INFO
CORS_ORIGINS=["https://your-frontend.vercel.app"]
```

#### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=https://your-backend.railway.app
NEXT_PUBLIC_CLIENT_ID=513010266454814
```

## 📊 Testing & Validation

### Run Tests
```bash
# Backend tests
cd thriveads-backend
source venv/bin/activate
pytest tests/ -v --cov=app

# System tests
python tests/system_test.py

# Performance benchmarks
curl -X POST "http://localhost:8000/api/v1/performance/benchmark/queries"
```

### Integration Tests (with real Meta API)
```bash
# Set real credentials
export META_ACCESS_TOKEN="your_real_token"
export META_AD_ACCOUNT_ID="513010266454814"

# Run integration tests
pytest tests/integration/ -v -m integration
```

## 🔍 Monitoring & Maintenance

### Health Checks
- Backend: `GET /health`
- Performance: `GET /api/v1/performance/health`
- Database: `GET /api/v1/performance/database-analysis`

### Data Sync
```bash
# Manual daily sync
curl -X POST "http://localhost:8000/api/v1/sync/daily?client_id=513010266454814"

# Weekly aggregation
curl -X POST "http://localhost:8000/api/v1/sync/aggregate/weekly?client_id=513010266454814&week_start=2024-01-01"

# Check sync status
curl "http://localhost:8000/api/v1/sync/status?client_id=513010266454814"
```

### Performance Monitoring
```bash
# Get performance summary
curl "http://localhost:8000/api/v1/performance/summary"

# Run benchmarks
curl -X POST "http://localhost:8000/api/v1/performance/benchmark/queries"

# Database analysis
curl "http://localhost:8000/api/v1/performance/database-analysis"
```

## 🛠️ Troubleshooting

### Common Issues

#### Meta API Connection
```bash
# Test Meta API connectivity
curl "http://localhost:8000/api/v1/ads/top-performing?client_id=513010266454814&period=last_week&limit=1"
```

#### Database Issues
```bash
# Check database connection
curl "http://localhost:8000/api/v1/performance/database-analysis"

# Reset database (development only)
rm thriveads.db
alembic upgrade head
```

#### Performance Issues
```bash
# Check system performance
curl "http://localhost:8000/api/v1/performance/health"

# Clear old metrics
curl -X DELETE "http://localhost:8000/api/v1/performance/metrics/cleanup?hours=24"
```

## 📈 Scaling Considerations

### Database Optimization
- Add indexes for frequently queried columns
- Implement data archiving for old metrics
- Consider read replicas for analytics queries

### API Performance
- Implement Redis caching for Meta API responses
- Add rate limiting for client requests
- Use background jobs for heavy processing

### Monitoring
- Set up application performance monitoring (APM)
- Configure alerts for system health
- Implement log aggregation

## 🔐 Security

### Production Security Checklist
- [ ] Environment variables secured
- [ ] Database connections encrypted
- [ ] API endpoints protected
- [ ] CORS properly configured
- [ ] Rate limiting implemented
- [ ] Error messages sanitized
- [ ] Logging configured (no sensitive data)

## 📞 Support

### Logs Location
- Backend: Check Railway logs or local console
- Frontend: Check Vercel logs or browser console
- Database: Check PostgreSQL logs

### Key Metrics to Monitor
- API response times
- Database query performance
- Meta API rate limits
- Memory and CPU usage
- Error rates

---

**Ready for Production!** 🎉

The ThriveAds Platform is fully configured and ready for deployment with real Meta API credentials.
