# 🚀 QUICK DEPLOYMENT GUIDE

Your FinSight AI app is ready to deploy to **Streamlit Community Cloud** (FREE)!

## In 5 Minutes:

### 1️⃣ Install Git
- Download: https://git-scm.com/download/win
- Install and restart your terminal

### 2️⃣ Push to GitHub
```powershell
cd "c:\Users\ELLANTHENDRAL\ai for personal finanace"
git init
git add .
git commit -m "FinSight AI - Production Ready"
```

Create repo at https://github.com/new, then:
```powershell
git remote add origin https://github.com/YOUR_USERNAME/finsight-ai.git
git branch -M main
git push -u origin main
```

### 3️⃣ Deploy on Streamlit Cloud
1. Go to https://streamlit.io/cloud
2. Sign in with GitHub
3. Click "New app" → Select your repo → Deploy

### 4️⃣ Add Your Secrets
After deployment, click ⋮ → Settings → Secrets, paste:
```
MONGODB_URI = "your-mongodb-connection-string"
MONGODB_DB_NAME = "finsight"
GOOGLE_API_KEY = "YOUR_KEY_HERE"
NVIDIA_API_KEY = "YOUR_KEY_HERE"
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
NVIDIA_MODEL = "meta/llama-3.1-70b-instruct"
HF_API_KEY = "YOUR_KEY_HERE"
HF_CATEGORIZER_MODEL = "facebook/bart-large-mnli"
GEMINI_MODEL = "gemini-1.5-flash"
APP_SECRET_KEY = "any-random-string"
SESSION_TIMEOUT_MINUTES = 15
```

### ✅ Done!
Your app is live at: `https://finsight-ai.streamlit.app`

---

## 📚 Full Guide
See **DEPLOYMENT.md** for detailed troubleshooting and advanced options.

## 💡 Key Points
- ✅ MongoDB is configured and working locally
- ✅ Login/Register feature added
- ✅ All dependencies in `requirements.txt`
- ✅ `.env` secrets ignored (won't be pushed)
- ✅ Configuration files ready (config.toml, secrets.toml.example)

## 🔄 Updates After Deployment
```powershell
git add .
git commit -m "Your changes"
git push origin main
```
App auto-updates in 1-2 minutes!

---

**Need help?** Check DEPLOYMENT.md → Troubleshooting section
