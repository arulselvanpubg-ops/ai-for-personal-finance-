# FinSight AI

Personal AI finance assistant built with Python and Streamlit.

## Features

- AI-powered expense categorization
- Conversational financial chatbot
- Interactive dashboard with financial insights
- Budget planning and tracking
- Investment and goals placeholders for future expansion
- PDF and CSV transaction import support

## Technology Stack

- UI Framework: Streamlit
- AI APIs: NVIDIA NIM, Hugging Face, Google AI Studio
- Database: SQLite fallback with optional MongoDB Atlas
- Data Processing: Pandas
- Visualization: Plotly
- Authentication: Bcrypt password hashing

## Setup

1. Clone the repository.
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env`
4. Add your rotated local secrets.
5. Run the app: `streamlit run app.py`

## Environment Variables

Recommended local starter configuration:

```env
DB_BACKEND=sqlite
SQLITE_DB_PATH=data/finsight.db
NVIDIA_API_KEY=your_nvidia_key
HF_API_KEY=your_huggingface_key
GOOGLE_API_KEY=your_google_key
SESSION_TIMEOUT_MINUTES=15
```

## Production Notes

- Rotate any real secrets immediately if they were ever committed, pasted, or shared.
- For the quickest reliable Streamlit Cloud deployment, use `DB_BACKEND=sqlite`.
- SQLite is good for launch and demos, but it is not the best long-term persistent store on Streamlit Cloud.
- The app logs operational events to standard output so you can inspect them in Streamlit Cloud logs.
- When you want durable production data, move to a managed database.

## Deploy To Streamlit Cloud

1. Push the repo to GitHub.
2. Create a new app in Streamlit Cloud using `app.py`.
3. Add secrets from `.streamlit/secrets.toml.example`.
4. Reboot the app after saving secrets.

For the most stable first deploy, use:

```toml
DB_BACKEND = "sqlite"
SQLITE_DB_PATH = "data/finsight.db"
SESSION_TIMEOUT_MINUTES = 15
```

## Hardening Included

- SQLite fallback when MongoDB is unavailable
- Session timeout handling
- Safer login and registration validation
- Cleaner import and chat error handling
- Basic operational logging for app events
- Safer example config files with placeholder secrets

## License

MIT License
