# User Manual: Final Merged & Summary Excel Generator

## 1. Introduction
The **Final Merged & Summary Excel Generator** is a specialized tool designed to automate the process of merging multiple inventory, sales, and financial Excel records. It reconciles data from various sources (Branded, RM Job, Sales, and Trade Receivables) against a Master Data sheet to provide comprehensive summaries by Region, Zone, Company, and EMR ID.

---

## 2. Setting Up
To run this application, ensure you have Python and the required libraries installed.

### 2.1 Prerequisites
- Python 3.8 or higher
- Streamlit
- Pandas
- Openpyxl
- Rapidfuzz

### 2.2 How to Start
1. Open your terminal or command prompt.
2. Navigate to the `work` directory.
3. Run the following command:
   ```bash
   streamlit run new3.py
   ```
4. The application will automatically open in your default web browser (usually at `http://localhost:8501`).

---

## 3. Uploading Data Files
All required source files are conveniently located in the `assets22` folder. You must upload five specific files into their respective fields in the sidebar.

| Sidebar Upload Field | Corresponding File in `assets22` Folder |
| :--- | :--- |
| **Upload Branded Apr File** | `Branded Apr- 25-Jun -25.xlsx` |
| **Upload RM Job File** | `RM JOb.xlsx` |
| **Upload Master Data File** | `Master data.xlsx` |
| **Upload Sale Invoice File** | `Sale Invoice vs Order Number.xlsx` |
| **Upload Trade Receivable File** | `Trade Receivable.xlsx` |

> IMPORTANT
> The application will only begin processing once **all five** files are uploaded.

---

## 4. Understanding the Workflow
1. **File Normalization**: The tool skips the first 8 rows (header at row 9) for Branded and RM Job files to find the correct data column headers.
2. **EMR Mapping**: It automatically fills missing EMR IDs by matching company names against the Master Data.
3. **Sales Reconciliation**: RM data is cross-referenced with the Sales Invoice file to fetch missing 'JSO Order Numbers'.
4. **Outstanding Calculation**: It calculates the outstanding balance for each client by subtracting 'Trade Receivables' from the ledger totals.
5. **Priority Assignment**: Certain EMR IDs are automatically tagged as "Priority II", while others are "Priority I".

---

## 5. Exports and Results
Once processing is complete, you will see a preview of the data in the app:
- **Final Merged Preview**: The consolidated list of all transactions.
- **Summaries**: Individual tables for Zone, Region, Company, and EMR ID.

### 5.1 Downloading the Report
Click the **"📅 Download Final Excel with Monthly & Company/EMR Summaries"** button to save the result.

The exported file (`Final_Merged_Monthly_Summary.xlsx`) contains:
- **Final Merged**: The full database of merged records.
- **Summaries**: Separate sheets for Zone, Region, Company, and EMR ID totals.
- **Monthly Sheets**: Individual sheets for each month (e.g., 2025_04, 2025_05) for filtered analysis.

---


