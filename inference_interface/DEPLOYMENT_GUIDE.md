# 🚀 Streamlit Cloud Deployment Guide

## 📦 Package Ready

Your app is ready for deployment at:
`/Workspace/Users/muralimenon444@gmail.com/healthcare_policy_assistant_cloud/`

Total size: 0.66 MB (690,682 bytes)

---

## 🎯 DEPLOYMENT STEPS

### Step 1: Download Files from Databricks

1. Navigate to: `/Users/muralimenon444@gmail.com/healthcare_policy_assistant_cloud`
2. Right-click the folder → **"Export"** → **"Download"**
3. Save the ZIP file to your computer
4. Extract the ZIP file

### Step 2: Create GitHub Repository

1. Go to https://github.com and log in
2. Click **"New repository"** (green button)
3. Configure:
   - Name: `healthcare-policy-assistant`
   - Description: `GraphRAG-powered Medicare policy research assistant`
   - Visibility: **Public** (required for free Streamlit hosting)
   - ✅ Add README file
4. Click **"Create repository"**

### Step 3: Upload Files to GitHub

**Option A: GitHub Web Interface (Easiest)**
1. In your new repository, click **"Add file"** → **"Upload files"**
2. Drag and drop ALL files from the extracted folder:
   - app.py
   - requirements.txt
   - README.md
   - .gitignore
   - data/ folder (with all 3 parquet files)
   - .streamlit/secrets.toml.template
3. Commit message: "Initial commit"
4. Click **"Commit changes"**

**Option B: Git Command Line**
```bash
cd /path/to/extracted/folder
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/healthcare-policy-assistant.git
git push -u origin main
```

### Step 4: Deploy on Streamlit Cloud

1. Go to https://share.streamlit.io
2. Sign up/login (use GitHub account)
3. Click **"New app"**
4. Configure:
   - Repository: `YOUR_USERNAME/healthcare-policy-assistant`
   - Branch: `main`
   - Main file path: `app.py`
5. Click **"Deploy!"**

⏳ Deployment takes 2-5 minutes

### Step 5: Configure Secrets (CRITICAL)

After deployment starts:

1. In Streamlit Cloud dashboard, click **"⚙️ Settings"** for your app
2. Go to **"Secrets"** tab
3. Add your credentials:

```toml
# For Databricks (Recommended)
DATABRICKS_TOKEN = "your_personal_access_token_here"
DATABRICKS_HOST = "https://your-workspace.cloud.databricks.com"
MODEL_NAME = "databricks-meta-llama-3-3-70b-instruct"
```

**How to get Databricks token:**
1. In Databricks workspace: **User Settings** → **Developer** → **Access tokens**
2. Click **"Generate new token"**
3. Copy the token (save it securely!)
4. Paste into Streamlit secrets

**Alternative: Use OpenAI**
```toml
OPENAI_API_KEY = "sk-your-openai-api-key-here"
MODEL_NAME = "gpt-4"
```

4. Click **"Save"**
5. App will automatically restart with secrets

---

## ✅ Success!

Your app will be live at: `https://YOUR_APP_NAME.streamlit.app`

Features:
- ✅ No authentication required (fully public)
- ✅ Professional URL
- ✅ Free hosting forever
- ✅ Automatic updates when you push to GitHub
- ✅ Built-in analytics

---

## 🧪 Testing

1. Go to your app URL
2. Try **Standard Search**: "What are lung cancer screening requirements?"
3. Try **Relationship Analysis**: "How are NCDs and contractors connected?"
4. Verify sources display correctly

---

## 🔧 Troubleshooting

**App shows "Error initializing client"**
→ Check that secrets are configured correctly in Settings → Secrets

**"Missing API credentials" error**
→ Add DATABRICKS_TOKEN and DATABRICKS_HOST to secrets

**App loads but queries fail**
→ Check that your Databricks token is valid and has access to serving endpoint

**Knowledge graph errors**
→ Verify all 3 parquet files are in the `data/` folder in GitHub

---

## 📊 Monitoring

- View app logs: Settings → Logs
- Check analytics: Settings → Analytics  
- Monitor usage: Streamlit Cloud dashboard

---

## 🔄 Updating Your App

To make changes:
1. Edit files in GitHub (or push from local)
2. Streamlit Cloud auto-detects changes
3. App redeploys automatically (1-2 min)

---

## 💰 Costs

- Streamlit Cloud: **FREE** (1 public app)
- LLM API calls: 
  - Databricks: Per your workspace pricing
  - OpenAI: ~$0.01-0.03 per query (GPT-4)

⚠️ **Rate limiting is included** (10 queries/5 min) to control costs

---

## 🎉 You're Done!

Your GraphRAG Medicare Policy Assistant is now:
- ✅ Publicly accessible
- ✅ Hosted for free
- ✅ Professional and shareable
- ✅ Auto-updating

Share your URL with anyone! 🚀
