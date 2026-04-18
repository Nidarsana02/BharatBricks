# EpiAlert - Quick Start Guide 🚀

## 📌 TL;DR - Deployment in 5 Minutes

### 1️⃣ **Setup Pincode Coordinates** (One-time)
```
Open: 8.EpiAlert_Map_Visualization notebook
Run: Cell 2A only
✅ Creates: workspace.epialert.epi_pincode_coordinates (50 pincodes)
```

### 2️⃣ **Run Data Pipeline** (Daily)
```bash
# Execute in this exact order:
1. Run all cells: 1.Synthetic_Data_Generation
2. Run all cells: 2.Data_processing
3. Run all cells: 3.Anamoly_detection
```

### 3️⃣ **Deploy Dashboard**
```bash
cd /Users/ce230004031@iiti.ac.in/EpiAlert_Dashboard

# Configure credentials
cp .env.template .env
# Edit .env with your Databricks credentials

# Install dependencies
pip install -r requirements.txt

# Run dashboard
streamlit run app.py
```

### 4️⃣ **Access Dashboard**
```
Open browser: http://localhost:8501
```

---

## 🔄 Daily Workflow

### Automated (Recommended)
Create Databricks Job with 3 tasks:
1. **Task 1:** `2.Data_processing` → Run daily at 2 AM
2. **Task 2:** `3.Anamoly_detection` → Depends on Task 1
3. **Task 3:** Dashboard auto-refreshes every 5 min

### Manual
```bash
# Every morning:
1. Open 2.Data_processing → Run All
2. Open 3.Anamoly_detection → Run All
3. Dashboard shows updated alerts automatically
```

---

## 📊 What Each Notebook Does

 Notebook | Purpose | Runtime | Run Frequency |
----------|---------|---------|---------------|
 **1.Synthetic_Data_Generation** | Generate sample health data | 2-3 min | Once (or refresh) |
 **2.Data_processing** | Clean & normalize symptoms | 2-5 min | Daily |
 **3.Anamoly_detection** | Detect outbreaks + classify diseases | 3-7 min | Daily |
 **4.forecasting_cluster** | Predict future cases (optional) | 5-10 min | Weekly |
 **8.EpiAlert_Map_Visualization** | View map (optional) | 1-2 min | On-demand |

---

## 🗺️ Dashboard Features

* **Live Map:** Interactive Folium map with heatmap overlay
* **Metrics:** Active alerts, high-risk count, avg spike ratio, affected locations
* **Alert Table:** Sortable table with all active disease alerts
* **Input Form:** Add new health report → Real-time analysis
* **Anomaly Detection:** Automatic spike detection (>2.0x baseline)
* **Disease Classification:** ML-based disease prediction from symptoms
* **Dynamic Updates:** New alerts marked with yellow border on map

---

## 🎯 Testing the System

### Test 1: Normal Data (No Alert)
```
Dashboard Sidebar → Add New Health Report:
- Pincode: 560001 (Bengaluru)
- Symptom Cluster: fever_with_cough
- Daily Count: 8
- Baseline: 7.5
- Anomaly Score: 0.4

Result: ✅ "No Anomaly Detected" - NOT marked on map
```

### Test 2: Anomaly (Alert Triggered)
```
Dashboard Sidebar → Add New Health Report:
- Pincode: 600001 (Chennai)
- Symptom Cluster: fever_rash_jointpain
- Daily Count: 45
- Baseline: 12.0
- Anomaly Score: 0.89

Result: ⚠️ "ANOMALY DETECTED"
- Disease: DENGUE (90% confidence)
- Risk: HIGH
- Marked on map with yellow border
```

---

## 📂 File Structure

```
/Users/ce230004031@iiti.ac.in/
├── 1.Synthetic_Data_Generation.ipynb
├── 2.Data_processing.ipynb
├── 3.Anamoly_detection.ipynb
├── 4.forecasting_cluster.ipynb
├── 8.EpiAlert_Map_Visualization.ipynb
└── EpiAlert_Dashboard/
    ├── app.py              # Streamlit dashboard
    ├── requirements.txt    # Python dependencies
    ├── .env.template       # Config template
    ├── .env                # Your credentials (create this)
    ├── DEPLOYMENT.md       # Full deployment guide
    └── QUICKSTART.md       # This file
```

---

## 🔑 Get Databricks Credentials

### Server Hostname
```
Your workspace URL without https://
Example: adb-1234567890123456.7.azuredatabricks.net
```

### HTTP Path
```
1. Databricks UI → Compute → SQL Warehouses
2. Select your warehouse → Connection Details
3. Copy "Server hostname" and "HTTP path"
```

### Access Token
```
1. Databricks UI → User Settings (top right)
2. Developer → Access Tokens
3. Generate New Token → Copy token
```

---

## 🐛 Common Issues

**Error: "Table not found"**
→ Run Cell 2A in 8.EpiAlert_Map_Visualization notebook

**Dashboard shows empty map**
→ Run notebooks 1, 2, 3 in order first

**Connection timeout**
→ Check .env file has correct credentials

**No alerts detected**
→ Thresholds: spike_ratio > 2.0 AND anomaly_score > 0.8

---

## 📞 Need Help?

Read full deployment guide: `DEPLOYMENT.md`

---

**Ready to deploy? Start with Step 1 above! 🚀**
