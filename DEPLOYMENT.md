# EpiAlert Pipeline Deployment Guide

## 📋 Overview

This guide covers the complete deployment of the EpiAlert disease outbreak detection system, including:
1. Data generation and processing notebooks
2. Anomaly detection and disease classification
3. Interactive Streamlit dashboard
4. Automated scheduling

---

## 🗂️ Project Structure

```
EpiAlert/
├── Notebooks/
│   ├── 1.Synthetic_Data_Generation.ipynb
│   ├── 2.Data_processing.ipynb
│   ├── 3.Anamoly_detection.ipynb
│   ├── 4.forecasting_cluster.ipynb (optional)
│   ├── 8.EpiAlert_Map_Visualization.ipynb
│   └── 0.Translation.ipynb (optional - Sarvam AI)
├── Delta Tables/
│   ├── workspace.epialert.epi_alert_silver_events
│   ├── workspace.epialert.epi_alert_silver_agg
│   ├── workspace.default.epi_alert_gold_anomaly
│   └── workspace.epialert.epi_pincode_coordinates
└── Dashboard/
    ├── app.py (Streamlit dashboard)
    ├── requirements.txt
    └── .env (environment variables)
```

---

## 🚀 Deployment Steps

### **Phase 1: Initial Data Setup (Run Once)**

#### Step 1: Create Pincode Coordinates Table
**Notebook:** `8.EpiAlert_Map_Visualization`  
**Cell:** Cell 2A - "Create Pincode Delta Table"

**Action:**
```python
# Run Cell 2A to create workspace.epialert.epi_pincode_coordinates
# This table contains 50 pincode coordinates (25 state capitals × 2)
```

**Output Table:** `workspace.epialert.epi_pincode_coordinates`
- 50 rows with pincode, latitude, longitude, city, district, state
- Used by map visualization and dashboard

---

#### Step 2: Generate Synthetic Data
**Notebook:** `1.Synthetic_Data_Generation`  
**Run:** All cells sequentially

**What it does:**
- Generates synthetic health reports for 50 pincodes
- Creates data for 30+ days with seasonal patterns
- Simulates disease outbreaks (dengue, cholera, influenza, etc.)

**Output:**
- Raw synthetic data in memory (can be saved to Delta table if needed)

---

### **Phase 2: Data Processing Pipeline (Run Daily)**

#### Step 3: Data Processing & Normalization
**Notebook:** `2.Data_processing`  
**Run:** All cells sequentially

**What it does:**
- Cleans and normalizes symptom data
- Maps symptoms to standardized clusters (12 clusters)
- Creates silver-layer aggregated tables

**Output Tables:**
- `workspace.epialert.epi_alert_silver_events` - Per-report data
- `workspace.epialert.epi_alert_silver_agg` - Daily aggregated counts

**Runtime:** ~2-5 minutes

---

#### Step 4: Anomaly Detection & Disease Classification
**Notebook:** `3.Anamoly_detection`  
**Run:** All cells sequentially

**What it does:**
- Detects anomalies using Isolation Forest algorithm
- Applies season-aware thresholds (monsoon, summer, winter, post-monsoon)
- Classifies primary disease from symptom clusters
- Assigns risk levels (high/medium/low)

**Output Table:**
- `workspace.default.epi_alert_gold_anomaly` - Final alerts with disease predictions

**Key Thresholds:**
- Spike ratio > 2.0x baseline
- Anomaly score > 0.8
- Season-adjusted thresholds

**Runtime:** ~3-7 minutes

---

#### Step 5 (Optional): Forecasting
**Notebook:** `4.forecasting_cluster`  
**Run:** All cells (optional)

**What it does:**
- Time series forecasting for case counts
- Predicts future outbreaks

**Runtime:** ~5-10 minutes

---

### **Phase 3: Visualization (On-Demand)**

#### Step 6: Map Visualization
**Notebook:** `8.EpiAlert_Map_Visualization`  
**Run:** Cells 2-8

**What it does:**
- Loads coordinates from Delta table
- Joins alerts with locations
- Creates interactive Folium map with:
  - Heatmap layer
  - Risk-based markers
  - Disease classifications
  - Popups with details

**Output:** Interactive HTML map

**Runtime:** ~1-2 minutes

---

### **Phase 4: Dashboard Deployment**

#### Step 7: Configure Environment Variables
**File:** `/Users/ce230004031@iiti.ac.in/EpiAlert_Dashboard/.env`

Create `.env` file:
```bash
DATABRICKS_SERVER_HOSTNAME=your-workspace.cloud.databricks.com
DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/your-warehouse-id
DATABRICKS_TOKEN=dapi...your-token-here
```

**How to get these values:**
1. **Server Hostname:** Your Databricks workspace URL (without https://)
2. **HTTP Path:** Compute > SQL Warehouses > Select your warehouse > Connection Details
3. **Token:** User Settings > Developer > Access Tokens > Generate New Token

---

#### Step 8: Install Dependencies
```bash
cd /Users/ce230004031@iiti.ac.in/EpiAlert_Dashboard
pip install -r requirements.txt
```

---

#### Step 9: Run Streamlit Dashboard
```bash
streamlit run app.py --server.port 8501
```

**Dashboard Features:**
- 🗺️ Interactive disease outbreak map
- 📊 Real-time metrics (active alerts, high-risk count, avg spike ratio)
- 📝 Input form to add new health reports
- 🔍 Real-time anomaly detection on new inputs
- 🦠 Disease classification for new cases
- 🎨 Dynamic map updates with yellow-bordered "NEW" markers

**Access:** Open browser at `http://localhost:8501`

---

## ⏰ Automated Scheduling (Production)

### Option 1: Databricks Jobs (Recommended)

Create a **multi-task Databricks Job** with the following tasks:

#### Task 1: Data Processing
- **Type:** Notebook
- **Path:** `/Users/ce230004031@iiti.ac.in/2.Data_processing`
- **Cluster:** Serverless compute
- **Schedule:** Daily at 2:00 AM

#### Task 2: Anomaly Detection
- **Type:** Notebook
- **Path:** `/Users/ce230004031@iiti.ac.in/3.Anamoly_detection`
- **Cluster:** Serverless compute
- **Depends on:** Task 1
- **Schedule:** After Task 1 completes

#### Task 3 (Optional): Forecasting
- **Type:** Notebook
- **Path:** `/Users/ce230004031@iiti.ac.in/4.forecasting_cluster`
- **Cluster:** Serverless compute
- **Depends on:** Task 2

**How to create:**
1. Go to **Workflows** > **Jobs** > **Create Job**
2. Add each task with dependencies
3. Set schedule: `0 0 2 * * ? *` (daily at 2 AM)
4. Enable email alerts on failure

---

### Option 2: Manual Execution Order

If running manually, execute notebooks in this exact order:

1. ✅ **1.Synthetic_Data_Generation** (first time only, or to refresh data)
2. ✅ **2.Data_processing** (daily)
3. ✅ **3.Anamoly_detection** (daily, after #2)
4. ⚠️ **4.forecasting_cluster** (optional)
5. 📊 **8.EpiAlert_Map_Visualization** (on-demand)
6. 🌐 **Streamlit Dashboard** (always running)

---

## 🔄 Data Flow Diagram

```
┌─────────────────────┐
│ Synthetic Data Gen  │
│ (50 pincodes)       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ Data Processing     │
│ • Symptom normalize │
│ • 12 clusters       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐     ┌──────────────────┐
│ Anomaly Detection   │────>│ Pincode Coords   │
│ • Isolation Forest  │     │ (Delta Table)    │
│ • Disease classify  │     └──────────────────┘
│ • Risk levels       │              │
└──────────┬──────────┘              │
           │                         │
           ▼                         ▼
┌─────────────────────┐     ┌──────────────────┐
│ Gold Anomaly Table  │────>│ Map Viz Notebook │
│ (Alerts)            │     └──────────────────┘
└──────────┬──────────┘              │
           │                         │
           └─────────────┬───────────┘
                         │
                         ▼
                ┌──────────────────┐
                │ Streamlit        │
                │ Dashboard        │
                │ (Real-time UI)   │
                └──────────────────┘
```

---

## 📊 Key Delta Tables

 Table Name | Schema | Purpose | Updated By |
------------|--------|---------|------------|
 `epi_pincode_coordinates` | workspace.epialert | Pincode lat/lon lookup | One-time setup |
 `epi_alert_silver_events` | workspace.epialert | Per-report symptom data | Data processing |
 `epi_alert_silver_agg` | workspace.epialert | Daily aggregated counts | Data processing |
 `epi_alert_gold_anomaly` | workspace.default | Final alerts + predictions | Anomaly detection |

---

## 🔧 Troubleshooting

### Issue: "Table not found" error
**Solution:** Ensure notebooks are run in the correct order. Run Cell 2A in Map Visualization notebook first.

### Issue: Dashboard shows no data
**Solution:** 
1. Check `.env` file has correct credentials
2. Verify tables exist: `SHOW TABLES IN workspace.epialert`
3. Check anomaly table has data: `SELECT COUNT(*) FROM workspace.default.epi_alert_gold_anomaly WHERE alert_flag = 1`

### Issue: Pincode coordinates missing
**Solution:** Run Cell 2A in `8.EpiAlert_Map_Visualization` notebook to create the table.

### Issue: Anomaly detection not marking alerts
**Solution:** Check thresholds in notebook 3. Ensure `spike_ratio > 2.0` and `anomaly_score > 0.8`.

---

## 📈 Performance Optimization

### For Large-Scale Production:
1. **Partitioning:** Partition Delta tables by `report_date` and `pincode`
2. **Z-ordering:** Apply Z-ordering on frequently queried columns
3. **Caching:** Enable Delta cache for hot data
4. **Compute:** Use Photon-enabled SQL warehouses
5. **Streaming:** Convert batch notebooks to Structured Streaming for real-time processing

---

## 🎯 Success Criteria

✅ All notebooks run without errors  
✅ Delta tables contain data  
✅ Map visualization shows markers  
✅ Dashboard connects to database  
✅ New reports trigger anomaly detection  
✅ Map updates dynamically with new alerts  

---

## 📞 Support

For issues or questions:
- Check notebook cell outputs for error messages
- Review Databricks cluster logs
- Verify Unity Catalog permissions
- Ensure serverless compute is enabled

---

**Last Updated:** 2024-12-16  
**Version:** 1.0
