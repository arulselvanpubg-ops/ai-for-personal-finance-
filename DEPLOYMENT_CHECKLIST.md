# Streamlit Cloud Deployment Checklist

Follow these steps to deploy your FinSight AI app to Streamlit Community Cloud.

## ✅ Pre-Deployment Checklist

- [ ] All dependencies listed in `requirements.txt`
- [ ] `.env` file NOT committed to git (check `.gitignore`)
- [ ] API keys working locally on `http://localhost:8501`
- [ ] MongoDB connection string verified
- [ ] Latest code committed to GitHub

## 📋 Step-by-Step Instructions

### Step 1: Install Git (if not installed)

**Download from**: https://git-scm.com/download/win

Run the installer and restart your terminal.

### Step 2: Initialize Git Repository

```powershell
cd "c:\Users\ELLANTHENDRAL\ai for personal finanace"
git init
git add .
git commit -m "Initial commit: FinSight AI with MongoDB and Login"
```

### Step 3: Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `finsight-ai`
3. Description: "AI-powered personal finance assistant"
4. Choose **Public** (for Streamlit Cloud free tier)
5. Click "Create repository"

### Step 4: Push Code to GitHub

After creating the repository on GitHub, you'll see commands like:

```powershell
git remote add origin https://github.com/YOUR_USERNAME/finsight-ai.git
git branch -M main
git push -u origin main
```

Copy and run these commands in your project folder.

### Step 5: Deploy on Streamlit Cloud

1. Go to https://streamlit.io/cloud
2. Sign up with GitHub (authorize app access)
3. Click "New app" button
4. Select:
   - **Repository**: YOUR_USERNAME/finsight-ai
   - **Branch**: main
   - **Main file path**: app.py
5. Click "Deploy"

⏳ Wait 2-3 minutes for deployment to complete.

### Step 6: Add Secrets

Once your app is deployed:

1. Click the **⋮** (three dots) menu in top right
2. Select **Settings**
3. Click **Secrets** tab on left sidebar
4. In the text area, copy ALL of this (replace placeholders):

```toml
MONGODB_URI = "mongodb+srv://arulselvanpubg_db_user:9a4fU5e0BhIi2VvX@cluster0.p9w5o2n.mongodb.net/"
MONGODB_DB_NAME = "finsight"
GOOGLE_API_KEY = "YOUR_ACTUAL_GOOGLE_API_KEY"
NVIDIA_API_KEY = "YOUR_ACTUAL_NVIDIA_API_KEY"
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
NVIDIA_MODEL = "meta/llama-3.1-70b-instruct"
HF_API_KEY = "YOUR_ACTUAL_HUGGINGFACE_API_KEY"
HF_CATEGORIZER_MODEL = "facebook/bart-large-mnli"
GEMINI_MODEL = "gemini-1.5-flash"
APP_SECRET_KEY = "your-secret-key-12345"
SESSION_TIMEOUT_MINUTES = 15
```

5. Click **Save** button

### Step 7: Test Your App

Your app is now live at:
```
https://finsight-ai.streamlit.app
```

(Replace `finsight-ai` with your actual repository name if different)

Test:
- [ ] Login page loads
- [ ] Can register new account
- [ ] Can login successfully
- [ ] Dashboard displays
- [ ] Can add transactions
- [ ] MongoDB is storing data

## 🔄 Making Updates

After you make changes locally:

```powershell
cd "c:\Users\ELLANTHENDRAL\ai for personal finanace"
git add .
git commit -m "Your description of changes"
git push origin main
```

Streamlit Cloud will automatically redeploy your app within 1-2 minutes!

## 🆘 Troubleshooting

### App won't deploy
- Check build logs (click ⋮ → View logs)
- Verify all packages in `requirements.txt`
- Make sure no syntax errors in Python files

### API keys not working
- Verify secrets are added in Streamlit Cloud settings
- Check secret names match your code exactly
- Restart app (⋮ → Reboot app)

### MongoDB connection fails
- Verify MongoDB URI is correct
- Check MongoDB Atlas allows connections from all IPs (0.0.0.0/0)
- Test connection string locally first

### App runs slow
- Normal for free tier (1 vCPU, 1GB RAM)
- App sleeps after 7 days of inactivity (wakes on access)
- May take 30-60 seconds to start up

## 📚 Resources

- Streamlit Cloud Docs: https://docs.streamlit.io/streamlit-cloud
- MongoDB Atlas: https://www.mongodb.com/products/platform/atlas
- GitHub Help: https://docs.github.com

## ✨ Success!

Once deployed, you have a live AI finance app accessible from anywhere! 🎉

Share your app URL with friends and family to help them manage their finances with AI.
