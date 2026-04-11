# Deployment Checklist - Streamlit Cloud

## ✅ Pre-Deployment Checklist

### 1. Data Setup (Databricks)
- [ ] Delta tables created (`research_catalog.healthcare.graphrag_*`)
- [ ] Tables populated with data (run migration notebook)
- [ ] SQL Warehouse is running and accessible
- [ ] Permissions granted to user/service principal

### 2. Credentials & Secrets
- [ ] Personal Access Token (PAT) created in Databricks
- [ ] Token saved securely (you won't see it again!)
- [ ] SQL Warehouse ID copied
- [ ] Workspace URL copied (without https://)

### 3. Code Repository (GitHub)
- [ ] Fixed app.py pushed to GitHub
- [ ] requirements.txt updated with databricks-sql-connector
- [ ] .gitignore includes `.streamlit/secrets.toml`
- [ ] No hardcoded credentials in code

### 4. Streamlit Cloud Configuration
- [ ] App connected to GitHub repository
- [ ] Main file path set to `app.py`
- [ ] Python version: 3.9 or higher
- [ ] Secrets configured in Streamlit Cloud dashboard

### 5. Testing
- [ ] Test connection locally first (see below)
- [ ] Deploy to Streamlit Cloud
- [ ] Verify data loads without errors
- [ ] Test search functionality
- [ ] Check entity extraction and visualization

---

## 🧪 Local Testing (Before Deploying)

### Step 1: Create Local Secrets File

Create `.streamlit/secrets.toml`:
```toml
DATABRICKS_HOST = "your-workspace.cloud.databricks.com"
DATABRICKS_TOKEN = "dapi..."
DATABRICKS_WAREHOUSE_ID = "..."
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Test Connection
Run the test script (see test_connection.py):
```bash
python test_connection.py
```

### Step 4: Run App Locally
```bash
streamlit run app.py
```

Expected behavior:
- ✅ "Loading knowledge graph from Databricks..." spinner
- ✅ "Loaded X entities, Y relationships, Z text units" success message
- ✅ Landing page with search box appears
- ✅ Guided discovery buttons work
- ✅ Search returns results

---

## 🚀 Streamlit Cloud Deployment

### Step 1: Push to GitHub
```bash
git add app.py requirements.txt
git commit -m "Fix: SQL-only data loading for Streamlit Cloud"
git push origin main
```

### Step 2: Create/Update App on Streamlit Cloud
1. Go to https://share.streamlit.io/
2. Click "New app" or select existing app
3. Connect to your GitHub repository
4. Set main file: `app.py`
5. Set Python version: 3.9+

### Step 3: Configure Secrets
1. In app settings → Secrets
2. Add TOML configuration:
```toml
DATABRICKS_HOST = "your-workspace.cloud.databricks.com"
DATABRICKS_TOKEN = "dapi..."
DATABRICKS_WAREHOUSE_ID = "..."
```
3. Click "Save"

### Step 4: Deploy
1. Click "Deploy"
2. Wait for build to complete (~2-3 minutes)
3. Monitor logs for errors

### Step 5: Verify Deployment
- [ ] App loads without errors
- [ ] Knowledge graph loads successfully
- [ ] Metrics show in sidebar
- [ ] Search returns results
- [ ] Graph visualization works

---

## 🐛 Troubleshooting Common Issues

### Issue 1: "Cannot find GraphRAG data files"
**Cause:** Old app.py with local path checks  
**Fix:** Ensure you're using the SQL-only version (no `os.path.exists`)

### Issue 2: "Missing secret: DATABRICKS_HOST"
**Cause:** Secrets not configured  
**Fix:** Add secrets in Streamlit Cloud → App Settings → Secrets

### Issue 3: "Failed to connect to Databricks"
**Causes:**
- Invalid token (expired or wrong)
- Wrong DATABRICKS_HOST format (should not include https://)
- SQL Warehouse stopped
- Network issues

**Fix:**
1. Verify token in Databricks (create new if needed)
2. Check DATABRICKS_HOST format: `workspace.cloud.databricks.com`
3. Ensure SQL Warehouse is running
4. Test connection locally first

### Issue 4: "Table not found: research_catalog.healthcare.graphrag_entities"
**Causes:**
- Tables not created
- Wrong catalog/schema name
- Missing permissions

**Fix:**
1. Run setup_delta_tables.sql
2. Run migrate_to_v3.4.ipynb
3. Grant SELECT permissions
4. Verify table names match exactly

### Issue 5: Empty DataFrames / No data
**Cause:** Tables exist but are empty  
**Fix:** Run migration notebook to populate tables

### Issue 6: "Module 'databricks' has no attribute 'sql'"
**Cause:** Missing databricks-sql-connector  
**Fix:** Add to requirements.txt and redeploy

---

## 📊 Monitoring & Maintenance

### Check App Health
- Monitor Streamlit Cloud logs for errors
- Set up uptime monitoring (e.g., UptimeRobot)
- Review error reports weekly

### Update Databricks Token
1. Generate new PAT before old one expires
2. Update secret in Streamlit Cloud
3. Redeploy app (may auto-redeploy)

### Update Knowledge Graph Data
1. Run backend GraphRAG pipeline in Databricks
2. Data automatically available (cached for 1 hour)
3. Clear cache if needed: Restart app in Streamlit Cloud

### Performance Optimization
- Monitor cache hit rates
- Adjust TTL if data updates frequently
- Consider upgrading SQL Warehouse size if slow

---

## 🔒 Security Checklist

- [ ] Token has minimum required permissions (SELECT only)
- [ ] Token expiration set (90 days recommended)
- [ ] Service principal used (not personal account)
- [ ] Secrets never committed to GitHub
- [ ] Rate limiting enabled in app
- [ ] HTTPS enforced (Streamlit Cloud default)

---

## 📞 Support Resources

**Documentation:**
- Streamlit Cloud: https://docs.streamlit.io/streamlit-community-cloud
- Databricks SQL: https://docs.databricks.com/sql/
- SQL Connector: https://docs.databricks.com/dev-tools/python-sql-connector.html

**Common Commands:**
```bash
# Test locally
streamlit run app.py

# Check logs
streamlit logs

# Clear cache
# In app: Hamburger menu → Clear cache
```
