# Supabase Migration Guide

Your FinSight AI app has been updated to support **Supabase** as a backend database alongside existing MongoDB and SQLite support.

## Quick Start

### 1. Create a Supabase Project

1. Go to [supabase.com](https://supabase.com) and sign up/log in
2. Click "New Project"
3. Fill in:
   - **Project Name**: `finsight` (or your choice)
   - **Database Password**: Create a strong password
   - **Region**: Choose closest to your location
4. Wait for the project to be created (~2 minutes)

### 2. Get Your API Keys

Once your project is created:
1. Go to **Settings → API** (left sidebar)
2. Copy the following values:
   - **Project URL** → `SUPABASE_URL`
   - **Anon Public** → `SUPABASE_KEY`

### 3. Update `.env` File

Replace the placeholder values in `.env`:

```env
DB_BACKEND=supabase

# Supabase
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-anon-key-here
```

### 4. Create Database Tables

Go to **SQL Editor** in your Supabase dashboard and run this SQL script:

```sql
-- Users table
CREATE TABLE users (
  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  email TEXT NOT NULL UNIQUE,
  password TEXT NOT NULL,
  name TEXT NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  last_login TIMESTAMP WITH TIME ZONE
);

-- Transactions table
CREATE TABLE transactions (
  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  date TIMESTAMP WITH TIME ZONE NOT NULL,
  amount DECIMAL(10, 2) NOT NULL,
  description TEXT NOT NULL,
  category TEXT NOT NULL,
  notes TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Categories table
CREATE TABLE categories (
  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  name TEXT NOT NULL UNIQUE,
  budget DECIMAL(10, 2) DEFAULT 0
);

-- Budgets table
CREATE TABLE budgets (
  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  category_id TEXT NOT NULL,
  month TEXT NOT NULL,
  amount DECIMAL(10, 2) NOT NULL
);

-- Goals table
CREATE TABLE goals (
  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  name TEXT NOT NULL,
  target_amount DECIMAL(10, 2) NOT NULL,
  current_amount DECIMAL(10, 2) NOT NULL,
  target_date TIMESTAMP WITH TIME ZONE NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Investments table
CREATE TABLE investments (
  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  ticker TEXT NOT NULL,
  quantity DECIMAL(10, 4) NOT NULL,
  purchase_price DECIMAL(10, 2) NOT NULL,
  purchase_date TIMESTAMP WITH TIME ZONE NOT NULL
);

-- Chat history table
CREATE TABLE chat_history (
  id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
  user_message TEXT NOT NULL,
  ai_response TEXT NOT NULL,
  timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_transactions_date ON transactions(date);
CREATE INDEX idx_transactions_category ON transactions(category);
CREATE INDEX idx_budgets_month ON budgets(month);
CREATE INDEX idx_chat_history_timestamp ON chat_history(timestamp);

-- Insert default categories
INSERT INTO categories (name, budget) VALUES
('Food & Dining', 0),
('Transportation', 0),
('Shopping', 0),
('Entertainment', 0),
('Bills & Utilities', 0),
('Healthcare', 0),
('Education', 0),
('Travel', 0),
('Other', 0);
```

### 5. Enable Row Level Security (Optional but Recommended)

For production deployment, enable RLS:

```sql
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;
ALTER TABLE categories ENABLE ROW LEVEL SECURITY;
ALTER TABLE budgets ENABLE ROW LEVEL SECURITY;
ALTER TABLE goals ENABLE ROW LEVEL SECURITY;
ALTER TABLE investments ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_history ENABLE ROW LEVEL SECURITY;
```

### 6. Deploy to Streamlit Cloud

1. Commit and push changes to GitHub
2. Go to [Streamlit Cloud](https://share.streamlit.io)
3. Create new app from your repository
4. In **Advanced settings**, add secrets:
   ```
   DB_BACKEND=supabase
   SUPABASE_URL=your-project-url
   SUPABASE_KEY=your-anon-key
   ```
5. Deploy!

## Architecture

The app uses a **multi-backend system**:

```
┌─────────────────────────┐
│   Your Streamlit App    │
└────────────┬────────────┘
             │
    ┌────────┴────────┐
    │                 │
    v                 v
┌─────────┐      ┌──────────┐
│ Supabase│ ──── │ SQLite   │ (Fallback)
└─────────┘      └──────────┘
  (Primary)
```

- **Supabase** = PostgreSQL cloud database (production)
- **SQLite** = Local file database (backup/fallback)
- **MongoDB** = Still supported if configured

### Switching Backends

To switch backends without code changes:

```bash
# Use Supabase
export DB_BACKEND=supabase

# Use SQLite (default)
export DB_BACKEND=sqlite

# Use MongoDB
export DB_BACKEND=mongodb
```

## Data Migration (From MongoDB)

If you want to migrate existing MongoDB data to Supabase:

```python
# This script migrates MongoDB data to Supabase
from pymongo import MongoClient
from supabase import create_client

mongo_uri = "your-mongodb-uri"
mongo_db_name = "finsight"
supabase_url = "your-supabase-url"
supabase_key = "your-supabase-key"

mongo = MongoClient(mongo_uri)
db = mongo[mongo_db_name]
supabase = create_client(supabase_url, supabase_key)

# Migrate users
for user in db.users.find():
    supabase.table("users").insert({
        "email": user["email"],
        "password": user["password"],
        "name": user["name"],
        "created_at": user["created_at"].isoformat(),
        "last_login": user.get("last_login").isoformat() if user.get("last_login") else None
    }).execute()

# Repeat for other collections...
print("Migration complete!")
```

## Troubleshooting

### "supabase-py is not installed"
```bash
pip install supabase
```

### "SUPABASE_URL and SUPABASE_KEY not set"
Ensure your `.env` file has these variables, or set them in Streamlit Secrets for cloud deployment.

### Connection timeout
- Check that your Supabase project is active
- Verify API keys are correct
- Ensure tables exist in the database

### Authentication errors
- Confirm email/password in the app
- Check that the `users` table exists
- Verify column names match the SQL schema

## Performance Tips

1. **Enable Indexes**: Already done in SQL script above
2. **Use Connection Pooling**: Supabase handles this automatically
3. **Optimize Queries**: Avoid large `find()` operations
4. **Add Row Level Security**: Restrict data access per user

## Support

For Supabase help:
- [Supabase Documentation](https://supabase.com/docs)
- [PostgreSQL Docs](https://www.postgresql.org/docs/)

For app issues:
- Check logs in Streamlit Cloud
- Review error messages in the app UI
- Test locally with SQLite first
