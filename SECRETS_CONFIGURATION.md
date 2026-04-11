# Streamlit Cloud Secrets Configuration

## Required Secrets for Databricks SQL Warehouse Connection

Add these secrets to your Streamlit Cloud app:

### In Streamlit Cloud Dashboard:
1. Go to your app settings
2. Click on "Secrets" in the left menu
3. Add the following TOML configuration:

```toml
# Databricks Connection
DATABRICKS_HOST = "your-workspace.cloud.databricks.com"
DATABRICKS_TOKEN = "dapi1234567890abcdef..."
DATABRICKS_WAREHOUSE_ID = "1a2b3c4d5e6f7890"
```

## How to Get These Values:

### 1. DATABRICKS_HOST
- Your Databricks workspace URL without "https://"
- Example: `dbc-a1b2c3d4-e5f6.cloud.databricks.com`
- Find it in your browser address bar when logged into Databricks

### 2. DATABRICKS_TOKEN
- Personal Access Token (PAT) or Service Principal token
- **To create a PAT:**
  1. In Databricks workspace, click your user icon → Settings
  2. Go to "Developer" → "Access tokens"
  3. Click "Generate new token"
  4. Copy the token (starts with "dapi...")
  5. **Important:** Save it immediately - you can't see it again!

### 3. DATABRICKS_WAREHOUSE_ID
- SQL Warehouse ID from Databricks SQL
- **To find it:**
  1. Go to "SQL Warehouses" in Databricks
  2. Click on your warehouse
  3. In the URL, the ID is after `/sql/warehouses/`
  4. Example URL: `.../sql/warehouses/1a2b3c4d5e6f7890`
  5. Copy: `1a2b3c4d5e6f7890`

## Security Best Practices:

✅ **DO:**
- Use a dedicated service principal token (not personal)
- Set token expiration to reasonable period (90 days)
- Restrict token permissions to READ ONLY on required tables
- Rotate tokens regularly

❌ **DON'T:**
- Commit secrets to GitHub
- Share tokens via email/Slack
- Use admin tokens for production apps
- Leave tokens without expiration

## Grant Required Permissions:

Run this SQL in Databricks to grant read access:

```sql
-- For personal access token user
GRANT SELECT ON CATALOG research_catalog TO `your-email@company.com`;

-- OR for service principal
GRANT SELECT ON CATALOG research_catalog TO `service-principal-name`;

-- Grant on specific schema
GRANT SELECT ON SCHEMA research_catalog.healthcare TO `user-or-sp`;

-- Grant on specific tables (optional - more restrictive)
GRANT SELECT ON TABLE research_catalog.healthcare.graphrag_entities TO `user-or-sp`;
GRANT SELECT ON TABLE research_catalog.healthcare.graphrag_relationships TO `user-or-sp`;
GRANT SELECT ON TABLE research_catalog.healthcare.graphrag_text_units TO `user-or-sp`;
GRANT SELECT ON TABLE research_catalog.healthcare.graphrag_common_qas TO `user-or-sp`;
```

## Testing Connection Locally:

Before deploying, test locally with a `.streamlit/secrets.toml` file:

```toml
# .streamlit/secrets.toml (DO NOT COMMIT!)
DATABRICKS_HOST = "your-workspace.cloud.databricks.com"
DATABRICKS_TOKEN = "dapi..."
DATABRICKS_WAREHOUSE_ID = "..."
```

Add to `.gitignore`:
```
.streamlit/secrets.toml
```

Run locally:
```bash
streamlit run app.py
```

## Troubleshooting:

### Error: "Missing secret: DATABRICKS_HOST"
- Check secret name spelling (case-sensitive)
- Ensure secrets are saved in Streamlit Cloud

### Error: "Failed to connect to Databricks"
- Verify DATABRICKS_HOST format (no https://)
- Check token is valid and not expired
- Ensure SQL Warehouse is running
- Verify WAREHOUSE_ID is correct

### Error: "Table not found"
- Check table names: `research_catalog.healthcare.graphrag_*`
- Verify user/token has SELECT permissions
- Ensure tables exist (run migration notebook)

### Error: "Token expired"
- Generate new PAT in Databricks
- Update secret in Streamlit Cloud
- Redeploy app
