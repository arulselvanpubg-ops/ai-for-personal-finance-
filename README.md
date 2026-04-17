# FinSight AI

Personal AI Finance Assistant built with Python and Streamlit.

## Features

- 🤖 AI-powered expense categorization
- 💬 Conversational financial chatbot (FinSight Chat)
- 📊 Interactive dashboard with financial insights
- 🎯 Budget planning and tracking
- 📈 Investment portfolio monitoring
- 🎯 Savings goals management
- 📄 PDF report generation

## Technology Stack

- **UI Framework**: Streamlit
- **AI APIs**: NVIDIA NIM, Hugging Face, Google AI Studio
- **Database**: MongoDB Atlas
- **Data Processing**: Pandas
- **Visualization**: Plotly
- **Authentication**: Bcrypt password hashing

## Setup

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables in `.env` file
4. Run the app: `streamlit run app.py`

## Environment Variables

Create a `.env` file with your API keys:

```
NVIDIA_API_KEY=your_nvidia_key
HF_API_KEY=your_huggingface_key
GOOGLE_API_KEY=your_google_key
```

## Usage

- Start the dashboard to view your financial overview
- Import transactions via CSV/PDF upload
- Chat with FinSight AI for personalized advice
- Set budgets and track progress
- Generate monthly reports

## 🚀 Deploy to Streamlit Cloud (Free Tier)

Quick deployment to cloud:

```bash
# 1. Push to GitHub
git push origin main

# 2. Go to https://streamlit.io/cloud
# 3. Click "New app" → Select this repo → Deploy

# 4. Add secrets in app settings (⋮ → Secrets)
# Copy from .streamlit/secrets.toml.example
```

Your app will be live at: `https://finsight-ai.streamlit.app`

For detailed deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md)

## License

MIT License