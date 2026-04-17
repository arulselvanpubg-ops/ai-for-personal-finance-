# Deployment Guide - Streamlit Community Cloud

This guide will help you deploy FinSight AI to Streamlit Community Cloud (Free Tier).

## Prerequisites

1. **GitHub Account** - Create a free account at https://github.com
2. **Streamlit Account** - Create a free account at https://streamlit.io/cloud
3. **API Keys** - Have all your API keys ready:
   - MongoDB URI
   - Google API Key
   - NVIDIA API Key
   - (Optional) Hugging Face API Key

## Step-by-Step Deployment

### 1. Push Your Project to GitHub

```bash
# Initialize git repository (if not already done)
git init
git add .
git commit -m "Initial commit: FinSight AI app"

# Create a new repository on GitHub (https://github.com/new)
# Then push:
git remote add origin https://github.com/YOUR_USERNAME/finsight-ai.git
git branch -M main
git push -u origin main
```

### 2. Create a Streamlit Account

1. Go to https://streamlit.io/cloud
2. Click "Sign up"
3. Connect your GitHub account

### 3. Deploy Your App

1. Click "New app" on Streamlit Cloud dashboard
2. Select your GitHub repository
3. Select `main` as branch
4. Set main file path to `app.py`
5. Click "Deploy"

### 4. Add Secrets (CRITICAL!)

Once your app is deployed:

1. Go to your app settings (⋮ menu → Settings)
2. Click on "Secrets" tab
3. Copy the contents from `.streamlit/secrets.toml.example`
4. Paste into the secrets editor
5. **Replace the placeholder values with your actual API keys**
6. Save

Example secrets to add:
```toml
MONGODB_URI = "mongodb+srv://user:password@cluster0.xxxxx.mongodb.net/"
MONGODB_DB_NAME = "finsight"
GOOGLE_API_KEY = "your-actual-google-api-key"
NVIDIA_API_KEY = "your-actual-nvidia-api-key"
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
NVIDIA_MODEL = "meta/llama-3.1-70b-instruct"
HF_API_KEY = "your-actual-huggingface-api-key"
HF_CATEGORIZER_MODEL = "facebook/bart-large-mnli"
GEMINI_MODEL = "gemini-1.5-flash"
APP_SECRET_KEY = "generate-a-random-string-here"
SESSION_TIMEOUT_MINUTES = 15
```

### 5. Verify Your App is Running

1. Your app URL will be: `https://finsight-ai.streamlit.app`
2. Click the link to test your deployed app
3. Register a new account and test the features

## Common Issues & Troubleshooting

### Issue: "ModuleNotFoundError" for a package

**Solution**: Make sure all dependencies are in `requirements.txt`

```bash
# Add missing package to requirements.txt
pip freeze | grep package-name >> requirements.txt
git add requirements.txt
git commit -m "Add missing dependency"
git push
```

Streamlit Cloud will auto-redeploy and install the new package.

### Issue: MongoDB Connection Failed

**Solution**: Verify your MongoDB URI in secrets:
- Check your MongoDB Atlas IP whitelist includes "0.0.0.0/0" (allow all IPs)
- Confirm username and password are correct
- Make sure `.streamlit/secrets.toml` is NOT committed to GitHub (it's auto-generated locally)

### Issue: API Keys Not Loading

**Solution**: 
- Make sure secrets are saved in Streamlit Cloud dashboard
- Restart the app (click ⋮ → Reboot app)
- Check that secret names match exactly in your code

## Environment Variables

The app automatically loads secrets from Streamlit Cloud. In `core/db.py`, the code reads:

```python
MONGODB_URI = os.getenv('MONGODB_URI')
MONGODB_DB_NAME = os.getenv('MONGODB_DB_NAME', 'finsight')
```

Streamlit automatically makes these available in the deployed environment.

## Free Tier Limitations

- **Compute**: 1 vCPU, 1GB RAM
- **Storage**: 1GB
- **Uptime**: App goes to sleep after 7 days of inactivity (restarts when accessed)
- **Timeout**: 1 minute startup limit

These limits are sufficient for personal use and small teams.

## Upgrading to Pro (Optional)

If you need more resources:
- Click on app settings (⋮ → Settings)
- Scroll to "Upgrade to Pro"
- Choose a Pro tier plan

## Additional Resources

- [Streamlit Docs](https://docs.streamlit.io)
- [Streamlit Cloud Docs](https://docs.streamlit.io/streamlit-cloud)
- [MongoDB Connection Guide](https://docs.mongodb.com/manual/reference/connection-string/)

## Support

For issues:
1. Check Streamlit app logs (⋮ → View logs)
2. Check MongoDB connection status
3. Verify all secrets are correctly configured
