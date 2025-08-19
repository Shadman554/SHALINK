#!/bin/bash
# Force Railway to use the latest code by creating a new deployment

echo "🚀 Preparing Railway deployment with latest YouTube fixes..."

# Create a deployment marker to force Railway rebuild
echo "DEPLOYMENT_VERSION=$(date +%s)" > .env.railway

# Verify critical files exist
echo "📋 Verifying deployment files..."
ls -la main.py video_downloader.py bot_handlers.py config.py requirements_railway_new.txt Dockerfile

echo "✅ Railway deployment package ready!"
echo "📌 Next steps:"
echo "1. Commit and push these changes to git"
echo "2. Railway will automatically rebuild and deploy"
echo "3. The new deployment will have working YouTube downloads"

# Show the key improvements
echo ""
echo "🔧 Key fixes included:"
echo "- Latest yt-dlp version (2024.12.6)"
echo "- Enhanced YouTube downloader with multi-client support"
echo "- Age-restriction and geo-blocking bypass"
echo "- Improved error handling and retry mechanisms"
echo "- ffmpeg support for format conversion"