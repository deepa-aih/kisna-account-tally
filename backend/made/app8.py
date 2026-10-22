import streamlit as st
import pandas as pd
import io
 
st.set_page_config(page_title="📊 Final Merged & Summary Excel Generator", layout="wide")
st.title("📊 Final Merged Excel with Region/Zone Summary")
 
# === File Uploads ===
st.sidebar.header("📂 Upload Excel Files")
branded_file = st.sidebar.file_uploader("Upload Branded Apr File", type=["xlsx"])
rm_file = st.sidebar.file_uploader("Upload RM Job File", type=["xlsx"])
master_file = st.sidebar.file_uploader("Upload Master Data File", type=["xlsx"])
sale_file = st.sidebar.file_uploader("Upload Sale Invoice File", type=["xlsx"])
receivable_file = st.sidebar.file_uploader("Upload Trade Receivable File", type=["xlsx"])
 
if all([branded_file, rm_file, master_file, sale_file, receivable_file]):
 
    # ---------- Step 1: Read Branded & RM ----------
    branded_all = pd.concat(pd.read_excel(branded_file, sheet_name=None), ignore_index=True)
    rm_all = pd.concat(pd.read_excel(rm_file, sheet_name=None), ignore_index=True)
    branded_all.columns = [col.strip().lower() for col in branded_all.columns]
    rm_all.columns = [col.strip().lower() for col in rm_all.columns]
 
    branded_data = branded_all[['particulars', 'vch type', 'vch no.', 'date', 'debit', 'credit']].copy()
    branded_data = branded_data[~branded_data['particulars'].astype(str).str.lower().str.contains("total")]
    rm_data = rm_all[['particulars', 'vch type', 'vch no.', 'date', 'debit', 'credit']].copy()
    rm_data = rm_data[~rm_data['particulars'].astype(str).str.lower().str.contains("total")]
 
    # ---------- Step 2: Read Master & Tally ----------
    master_df = pd.read_excel(master_file, sheet_name="Kisna Force Master Details ")
    tally_df  = pd.read_excel(master_file, sheet_name="Tally Ledger Name")
    master_df.columns = master_df.columns.str.lower().str.strip()
    tally_df.columns  = tally_df.columns.str.lower().str.strip()
 
    tally_df['company'] = tally_df['company'].astype(str).str.strip().str.lower()
    tally_df['code']    = tally_df['code'].astype(str).str.strip().str.upper()
 
    if 'emr id' in master_df.columns:
        master_df['emr id'] = master_df['emr id'].astype(str).str.strip().str.upper()
 
    # Map particulars -> EMR ID
    particular_to_code = dict(zip(tally_df['company'], tally_df['code']))
    for df in [branded_data, rm_data]:
        df['emr id'] = df['particulars'].astype(str).str.strip().str.lower().map(particular_to_code)
        df['emr id'] = df['emr id'].astype(str).str.strip().str.upper()
 
    branded_data['source'] = 'branded'
    rm_data['source'] = 'rm'
    combined = pd.concat([branded_data, rm_data], ignore_index=True)
 
    # ---------- Step 3: Merge with Master ----------
    final = combined.merge(master_df, on='emr id', how='left')
    final['sr no'] = range(1, len(final) + 1)
 
    final = final[['vch type', 'vch no.', 'date', 'debit', 'credit', 'sr no', 'emr id',
                   'region', 'zone', 'part', 'state', 'ba code', 'territory', 'city',
                   'type', 'status', 'kisna/siva', 'party name', 'nsm', 'zone head']]
 
    # ---------- Step 4: Read Sale & Build JSO Map ----------
    sale_df = pd.read_excel(sale_file)
    sale_df.columns = sale_df.columns.str.lower()
    sale_df.rename(columns={'account code': 'emr id'}, inplace=True)
    sale_df['emr id'] = sale_df['emr id'].astype(str).str.strip().str.upper()
 
    if 'jso order no' in sale_df.columns:
        jso_map = (
            sale_df.groupby('emr id')['jso order no']
            .apply(lambda x: ', '.join(sorted(set(
                s for s in (str(i).strip() for i in x) if s and s.lower() != 'nan'
            ))))
            .to_dict()
        )
    else:
        jso_map = {}
 
    final['jso order no'] = final['emr id'].map(jso_map).fillna('')
 
    # ---------- Step 5: Add Remark ----------
    def get_remark(order_no):
        if pd.isna(order_no) or not order_no.strip():
            return ''
        order_no = order_no.upper()
        if any(x in order_no for x in ['KCO', 'KCD']): return "KCO | Extra Gold IGI"
        elif any(x in order_no for x in ['RLS', 'SNL']): return "SNMCC | Line Sale"
        elif any(x in order_no for x in ['KSN', 'RAD']): return "Invoice ready"
        elif 'HKJ' in order_no: return "Retailer ledger Dr. | KIOS"
        return ''
 
    def aggregate_remarks(jso_str):
        if not jso_str:
            return ''
        remarks = {get_remark(j) for j in jso_str.split(',') if j.strip()}
        remarks.discard('')
        return ', '.join(sorted(remarks))
 
    final['remark'] = final['jso order no'].apply(aggregate_remarks)
 
    # ---------- Step 6: Trade Receivable ----------
    receivable_df = pd.read_excel(receivable_file)
    receivable_df.columns = receivable_df.columns.str.lower()
    receivable_df['particulars'] = receivable_df['particulars'].astype(str).str.strip().str.lower()
 
    final['emr id'] = final['emr id'].astype(str).str.strip().str.upper()
    final['debit']  = final['debit'].fillna(0)
    final['credit'] = final['credit'].fillna(0)
    final['receivable_credit'] = 0.0
    final['outstanding'] = final['debit'] - final['credit']
    final['advance_payment'] = 0.0
 
    updated_codes = set()
    for _, row in receivable_df.iterrows():
        party = row['particulars']
        credit_amt = row['credit'] if pd.notna(row.get('credit')) else 0
        matched = tally_df[tally_df['company'] == party]
        if not matched.empty:
            code = matched.iloc[0]['code'].strip().upper()
            if code not in updated_codes:
                match_idx = final[final['emr id'] == code].index
                if not match_idx.empty:
                    idx = match_idx[0]
                    final.at[idx, 'receivable_credit'] = credit_amt
                    final.at[idx, 'outstanding'] = (
                        final.at[idx, 'debit'] - final.at[idx, 'credit'] - credit_amt
                    )
                    updated_codes.add(code)
 
    all_found_codes = set(final['emr id'].unique())
    unmatched_rows = []
    for _, row in receivable_df.iterrows():
        party_name = row['particulars']
        credit_amt = row['credit'] if pd.notna(row.get('credit')) else 0
        matched = tally_df[tally_df['company'] == party_name]
        if not matched.empty:
            code = matched.iloc[0]['code'].strip().upper()
            if code not in all_found_codes:
                unmatched_rows.append({
                    "vch type": "",
                    "vch no.": "",
                    "date": pd.NaT,
                    "debit": 0,
                    "credit": 0,
                    "sr no": None,
                    "emr id": code,
                    "region": "",
                    "zone": "",
                    "part": "",
                    "state": "",
                    "ba code": "",
                    "territory": "",
                    "city": "",
                    "type": "",
                    "status": "",
                    "kisna/siva": "",
                    "party name": party_name.title(),
                    "nsm": "",
                    "zone head": "",
                    "jso order no": jso_map.get(code, ""),
                    "remark": aggregate_remarks(jso_map.get(code, "")),
                    "receivable_credit": 0,
                    "outstanding": 0,
                    "advance_payment": credit_amt,
                    "source": "Unmatched"
                })
 
    unmatched_df = pd.DataFrame(unmatched_rows)
 
    if 'credit' in final.columns:
        credit_index = final.columns.get_loc('credit')
        cols = list(final.columns)
        for col in ['receivable_credit', 'outstanding']:
            if col in cols:
                cols.remove(col)
                cols.insert(credit_index + 1, col)
        final = final[cols]
        final.drop(columns=['credit'], inplace=True)
 
    # ---------- Step 7: Priority & Sorting ----------
    priority_emr_ids = {
        "MPCCD", "MPGJ2", "TNPJ", "UPAH", "UPBPAKS", "UPHG", "UPHK", "UPJP",
        "UPMHJ", "UPPLP", "UPPLR", "UPUBJH1", "UPUDJB", "UPUHKJHP", "UPURJL",
        "UPUSDJBW", "UPUTRSJ"
    }
    final['priority'] = final['emr id'].apply(lambda x: "II" if x in priority_emr_ids else "I")
    cols = ['priority'] + [c for c in final.columns if c != 'priority']
    final = final[cols]
    final['priority_sort'] = final['priority'].map({'II': 0, 'I': 1})
    final = final.sort_values(by='priority_sort').drop(columns=['priority_sort']).reset_index(drop=True)
 
    # ---------- Step 8: Summaries ----------
    summary_zone = final.groupby('zone')[['debit', 'receivable_credit', 'outstanding']].sum(numeric_only=True).reset_index()
    summary_region = final.groupby('region')[['debit', 'receivable_credit', 'outstanding']].sum(numeric_only=True).reset_index()
 
    st.subheader("✅ Final Preview (Top 50 Rows)")
    st.dataframe(final.head(50))
 
    st.subheader("📍 Zone-wise Summary")
    st.dataframe(summary_zone)
 
    st.subheader("📍 Region-wise Summary")
    st.dataframe(summary_region)
 
    # ---------- Step 9: Export ----------
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        final.to_excel(writer, sheet_name="Final Merged", index=False)
        summary_zone.to_excel(writer, sheet_name="Zone Summary", index=False)
        summary_region.to_excel(writer, sheet_name="Region Summary", index=False)
        if not unmatched_df.empty:
            unmatched_df.to_excel(writer, sheet_name="Unmatched Parties", index=False)
    output.seek(0)
 
    st.download_button(
        label="📅 Download Final Excel with Summaries",
        data=output,
        file_name="Final_Merged_Summary.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
 
else:
    st.warning("📂 Please upload all 5 required Excel files to proceed.")