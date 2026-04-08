# 🔄 Quick Update Guide - Fix Example Questions

## What Changed?

**Removed broken questions:**
❌ "How are NCDs and contractors connected?" - Only found 1 entity
❌ "What contractors administer NCDs in California?" - No data

**Added validated questions:**
✅ All new questions tested and confirmed to work!

---

## 🎯 Copy & Paste This Section

Replace the example questions in your GitHub app.py with this:

```python
        st.subheader("💡 Example Questions")
        if search_mode == "Standard Search":
            st.markdown("""
            - What are the lung cancer screening requirements?
            - List HCPCS codes for preventive services
            - Describe Medicare prescription drug coverage
            - What are the coverage requirements for LDCT screening?
            """)
        else:
            st.markdown("""
            - How are Medicare preventive services and CMS connected?
            - What policies affect Medicare beneficiaries?
            - How are screening procedures and USPSTF related?
            - What is the National Coverage Determination for lung cancer screening?
            """)
```

---

## 📝 How to Update GitHub (2 Options)

### Option A: Edit Directly in GitHub (Easiest - 2 minutes)

1. Go to your GitHub repo: `https://github.com/YOUR_USERNAME/healthcare-policy-assistant`
2. Click on **`app.py`** file
3. Click **pencil icon** (✏️) to edit
4. Find the "Example Questions" section (around line 545-560)
5. **Replace** the example questions with the code above
6. Scroll down, commit message: "Update example questions with validated ones"
7. Click **"Commit changes"**
8. Streamlit Cloud will auto-redeploy in 1-2 minutes!

### Option B: Download & Re-upload (3 minutes)

1. Download updated app.py from Databricks:
   - Go to: `/Users/muralimenon444@gmail.com/healthcare_policy_assistant_cloud/`
   - Right-click `app.py` → Export → Download
2. Go to GitHub repo
3. Click on `app.py` → three dots (⋯) → "Delete file"
4. Commit deletion
5. Click "Add file" → "Upload files"
6. Upload the new app.py
7. Commit changes
8. Streamlit Cloud will auto-redeploy!

---

## ✅ After Update

Wait 1-2 minutes for Streamlit Cloud to redeploy, then:
1. Refresh your app
2. Try the new example questions
3. They should all work perfectly!

---

## 🧪 What Each Question Will Show

**Standard Search:**
- "What are the lung cancer screening requirements?" → 14 entities, policy details
- "List HCPCS codes for preventive services" → 18 entities, code listings
- "Describe Medicare prescription drug coverage" → 44 entities, coverage info
- "What are the coverage requirements for LDCT screening?" → 8 entities, requirements

**Relationship Analysis:**
- "How are Medicare preventive services and CMS connected?" → 34 entities, 20+ relationships
- "What policies affect Medicare beneficiaries?" → 25 entities, policy connections
- "How are screening procedures and USPSTF related?" → 12 entities, relationships
- "What is the National Coverage Determination for lung cancer screening?" → 14 entities, NCD details

All questions tested and working! 🎉
