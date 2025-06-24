# Production Environment Setup

This guide covers setting up environment variables and configuration for production deployment.

## 🚀 Railway (Backend) Environment Variables

Set these variables in your Railway project dashboard:

### Required Variables
```bash
# Environment
ENVIRONMENT=production

# Database (automatically provided by Railway PostgreSQL addon)
DATABASE_URL=postgresql://username:password@host:port/database

# Meta API Configuration
META_ACCESS_TOKEN=your_long_lived_meta_access_token
META_API_VERSION=v23.0

# Security
SECRET_KEY=your-super-secure-secret-key-for-production

# CORS Origins (update with your actual Vercel domain)
ALLOWED_ORIGINS=https://your-app.vercel.app,https://thriveads-platform.vercel.app

# Logging
LOG_LEVEL=INFO

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60

# Data Refresh
DATA_REFRESH_INTERVAL=60

# Default Client
DEFAULT_CLIENT_ID=513010266454814
```

### Optional Variables
```bash
# Meta App Credentials (if needed for advanced features)
META_APP_ID=your_meta_app_id
META_APP_SECRET=your_meta_app_secret

# Additional Security Headers
SECURE_HEADERS_ENABLED=true

# Performance Monitoring
ENABLE_PERFORMANCE_MONITORING=true
```

## 🌐 Vercel (Frontend) Environment Variables

Set these variables in your Vercel project dashboard:

### Required Variables
```bash
# API Configuration
NEXT_PUBLIC_API_URL=https://your-backend.railway.app

# Client Configuration
NEXT_PUBLIC_CLIENT_ID=513010266454814

# Environment
NODE_ENV=production
```

### Optional Variables
```bash
# Analytics (if using)
NEXT_PUBLIC_ANALYTICS_ID=your_analytics_id

# Error Tracking (if using Sentry)
NEXT_PUBLIC_SENTRY_DSN=your_sentry_dsn

# Feature Flags
NEXT_PUBLIC_ENABLE_DEBUG=false
```

## 🔧 Railway Setup Steps

1. **Create Railway Account**
   - Go to [railway.app](https://railway.app)
   - Sign up with GitHub

2. **Create New Project**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your thriveads-platform repository

3. **Add PostgreSQL Database**
   - In your project dashboard, click "New"
   - Select "Database" → "PostgreSQL"
   - Railway will automatically set DATABASE_URL

4. **Configure Environment Variables**
   - Go to your backend service
   - Click "Variables" tab
   - Add all required variables listed above

5. **Set Root Directory**
   - In service settings, set root directory to `thriveads-backend`

## 🎨 Vercel Setup Steps

1. **Create Vercel Account**
   - Go to [vercel.com](https://vercel.com)
   - Sign up with GitHub

2. **Import Project**
   - Click "New Project"
   - Import your thriveads-platform repository

3. **Configure Build Settings**
   - Framework Preset: Next.js
   - Root Directory: `thriveads-client-platform`
   - Build Command: `npm run build`
   - Output Directory: `.next`

4. **Set Environment Variables**
   - In project settings, go to "Environment Variables"
   - Add all required variables listed above

## 🔐 Security Checklist

- [ ] All sensitive data is in environment variables, not code
- [ ] CORS origins are properly configured
- [ ] Database connections use SSL
- [ ] API endpoints have rate limiting
- [ ] Error messages don't expose sensitive information
- [ ] Logging doesn't include sensitive data
- [ ] HTTPS is enforced on all endpoints

## 📊 Monitoring Setup

### Railway Monitoring
- Use Railway's built-in metrics dashboard
- Set up alerts for high CPU/memory usage
- Monitor deployment logs

### Vercel Monitoring
- Use Vercel Analytics for frontend performance
- Monitor build times and deployment success
- Set up error tracking

### Application Monitoring
- Health check endpoint: `https://your-backend.railway.app/health`
- Performance metrics: `https://your-backend.railway.app/api/v1/performance/metrics`
- System status: Monitor both frontend and backend uptime

## 🚨 Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Verify DATABASE_URL is correctly set
   - Check PostgreSQL addon is running
   - Ensure database migrations are applied

2. **CORS Errors**
   - Update ALLOWED_ORIGINS with correct Vercel domain
   - Ensure both HTTP and HTTPS variants are included

3. **Meta API Errors**
   - Verify META_ACCESS_TOKEN is valid and not expired
   - Check META_API_VERSION matches your app configuration
   - Ensure ad account ID is correct

4. **Build Failures**
   - Check all required environment variables are set
   - Verify Node.js/Python versions match requirements
   - Review build logs for specific error messages

### Health Check Commands

```bash
# Check backend health
curl https://your-backend.railway.app/health

# Check frontend
curl https://your-app.vercel.app

# Check API connectivity
curl https://your-backend.railway.app/api/v1/campaigns/summary
```

## 📞 Support

- Railway Documentation: [docs.railway.app](https://docs.railway.app)
- Vercel Documentation: [vercel.com/docs](https://vercel.com/docs)
- Meta API Documentation: [developers.facebook.com](https://developers.facebook.com)

---

**Ready for Production!** 🎉

Once all environment variables are configured and both services are deployed, your ThriveAds platform will be live and ready to serve clients.
