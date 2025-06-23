#!/bin/bash

# ThriveAds Platform Development Setup Script

echo "🚀 Setting up ThriveAds Platform for development..."

# Check if Python 3.11+ is installed
echo "📋 Checking Python version..."
python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
if [[ $(echo "$python_version >= 3.11" | bc -l) -eq 1 ]]; then
    echo "✅ Python $python_version is installed"
else
    echo "❌ Python 3.11+ is required. Please install Python 3.11 or higher."
    exit 1
fi

# Check if Node.js is installed
echo "📋 Checking Node.js version..."
if command -v node &> /dev/null; then
    node_version=$(node --version)
    echo "✅ Node.js $node_version is installed"
else
    echo "❌ Node.js is required. Please install Node.js 18+."
    exit 1
fi

# Setup backend
echo "🐍 Setting up Python backend..."
cd thriveads-backend

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Copy environment file
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please update .env file with your Meta API credentials"
fi

cd ..

# Setup frontend
echo "⚛️  Setting up Next.js frontend..."
cd thriveads-client-platform

# Install Node.js dependencies
echo "Installing Node.js dependencies..."
npm install

cd ..

echo "✅ Development setup complete!"
echo ""
echo "📝 Next steps:"
echo "1. Update thriveads-backend/.env with your Meta API credentials"
echo "2. Set up PostgreSQL database:"
echo "   - Install PostgreSQL"
echo "   - Create database: createdb thriveads"
echo "   - Update DATABASE_URL in .env file"
echo "3. Initialize database:"
echo "   - cd thriveads-backend && source venv/bin/activate"
echo "   - python seed_database.py"
echo "4. Start development servers:"
echo "   - Backend: uvicorn main:app --reload"
echo "   - Frontend: cd ../thriveads-client-platform && npm run dev"
echo ""
echo "🌐 URLs:"
echo "   - Frontend: http://localhost:3000"
echo "   - Backend API: http://localhost:8000"
echo "   - API Docs: http://localhost:8000/docs"
echo ""
echo "📊 Database Features:"
echo "   - ✅ Daily metrics storage (kept forever)"
echo "   - ✅ Pre-calculated weekly/monthly aggregations"
echo "   - ✅ Performance indexes for fast queries"
echo "   - ✅ Data sync tracking and error handling"
echo "   - ✅ Mimilátky CZ client pre-configured"
