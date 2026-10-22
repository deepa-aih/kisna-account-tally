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

    # Step 1: Read Files
    branded_all = pd.concat(pd.read_excel(branded_file, sheet_name=None), ignore_index=True)
    rm_all = pd.concat(pd.read_excel(rm_file, sheet_name=None), ignore_index=True)
    branded_all.columns = [col.strip().lower() for col in branded_all.columns]
    rm_all.columns = [col.strip().lower() for col in rm_all.columns]

    branded_data = branded_all[['particulars', 'vch type', 'vch no.', 'date', 'debit', 'credit']].copy()
    branded_data = branded_data[~branded_data['particulars'].astype(str).str.lower().str.contains("total")]
    rm_data = rm_all[['particulars', 'vch type', 'vch no.', 'date', 'debit', 'credit']].copy()
    rm_data = rm_data[~rm_data['particulars'].astype(str).str.lower().str.contains("total")]

    # Read master and tally
    master_df = pd.read_excel(master_file, sheet_name="Kisna Force Master Details ")
    tally_df = pd.read_excel(master_file, sheet_name="Tally Ledger Name")
    master_df.columns = master_df.columns.str.lower().str.strip()
    tally_df.columns = tally_df.columns.str.lower().str.strip()

    # --- NORMALIZE CODES & COMPANIES ---
    tally_df['company'] = tally_df['company'].astype(str).str.strip().str.lower()   # keys for mapping are lower (particulars lowered)
    tally_df['code'] = tally_df['code'].astype(str).str.strip().str.upper()       # codes normalized UPPER for consistent matching later
    # Ensure master DF's emr id values are uppercase so merge will match (important!)
    if 'emr id' in master_df.columns:
        master_df['emr id'] = master_df['emr id'].astype(str).str.strip().str.upper()
    else:
        # defensive: if column exists with different name, try common variants (optional)
        pass

    # Map particulars -> code using tally (company -> code)
    particular_to_code = dict(zip(tally_df['company'], tally_df['code']))
    for df in [branded_data, rm_data]:
        # map from lower(particulars) -> code (which we've uppercased)
        df['emr id'] = df['particulars'].astype(str).str.strip().str.lower().map(particular_to_code)
        # ensure final emr id is uppercase (map already produced uppercase codes)
        df['emr id'] = df['emr id'].astype(str).str.strip().str.upper()

    branded_data['source'] = 'branded'
    rm_data['source'] = 'rm'
    combined = pd.concat([branded_data, rm_data], ignore_index=True)

    # Merge with master (master_df['emr id'] already uppercased above)
    final = combined.merge(master_df, on='emr id', how='left')
    final['sr no'] = range(1, len(final) + 1)

    # Keep all required columns (this preserves master columns - change if needed)
    final = final[['vch type', 'vch no.', 'date', 'debit', 'credit', 'sr no', 'emr id',
                   'region', 'zone', 'part', 'state', 'ba code', 'territory', 'city',
                   'type', 'status', 'kisna/siva', 'party name', 'nsm', 'zone head']]

    # --- Sale file ---
    sale_df = pd.read_excel(sale_file)
    sale_df.columns = sale_df.columns.str.lower()
    sale_df.rename(columns={
        'doc. date': 'date',
        'doc. no.': 'vch no.',
        'account code': 'emr id',
        'account name': 'party name',
        'sr code': 'ba code',
        'ref. code': 'state'
    }, inplace=True)

    # Normalize sale_df emr id to uppercase so merge is consistent
    if 'emr id' in sale_df.columns:
        sale_df['emr id'] = sale_df['emr id'].astype(str).str.strip().str.upper()

    final['date'] = pd.to_datetime(final['date'], errors='coerce')
    sale_df['date'] = pd.to_datetime(sale_df['date'], errors='coerce')

    # Merge sale - we will aggregate JSO / remark after this to avoid duplicates
    merged = pd.merge(
        final,
        sale_df[['date', 'vch no.', 'emr id', 'party name', 'ba code', 'state', 'jso order no']],
        on=['date', 'vch no.', 'emr id', 'party name', 'ba code', 'state'],
        how='left'
    )

    def get_remark(order_no):
        if pd.isna(order_no): return ''
        order_no = str(order_no).upper()
        if any(x in order_no for x in ['KCO', 'KCD']): return "KCO | Extra Gold IGI"
        elif any(x in order_no for x in ['RLS', 'SNL']): return "SNMCC | Line Sale"
        elif any(x in order_no for x in ['KSN', 'RAD']): return "Invoice ready"
        elif 'HKJ' in order_no: return "Retailer ledger Dr. | KIOS"
        return ''

    merged['remark'] = merged['jso order no'].apply(get_remark)

    # Aggregate unique JSO numbers and remarks, comma-separated (per vch no.)
    agg_orders = merged.groupby('vch no.').agg({
        'jso order no': lambda x: ', '.join(sorted(set(str(i).strip() for i in x if pd.notna(i) and str(i).strip()))),
        'remark': lambda x: ', '.join(sorted(set(r for r in x if r)))
    }).reset_index()

    merged_first_rows = merged.drop_duplicates(subset='vch no.', keep='first')
    final_merged = pd.merge(merged_first_rows, agg_orders, on='vch no.', how='left', suffixes=('', '_agg'))

    # Use aggregated values only
    final_merged['jso order no'] = final_merged['jso order no_agg']
    final_merged['remark'] = final_merged['remark_agg']
    final_merged.drop(columns=['jso order no_agg', 'remark_agg'], inplace=True)

    # --- Trade receivable ---
    receivable_df = pd.read_excel(receivable_file)
    receivable_df.columns = receivable_df.columns.str.lower()
    receivable_df['particulars'] = receivable_df['particulars'].astype(str).str.strip().str.lower()
    # NOTE: final_merged emr id must be uppercase for matching; ensure that now:
    final_merged['emr id'] = final_merged['emr id'].astype(str).str.strip().str.upper()

    final_merged['debit'] = final_merged['debit'].fillna(0)
    final_merged['credit'] = final_merged['credit'].fillna(0)
    final_merged['receivable_credit'] = 0.0
    final_merged['outstanding'] = final_merged['debit'] - final_merged['credit']
    final_merged['advance_payment'] = 0.0

    # Update receivable_credit by matching receivable_file particulars -> tally_df.company -> tally_df.code
    updated_codes = set()
    for _, row in receivable_df.iterrows():
        party = row['particulars']  # receivable_df particulars are lowercased
        credit_amt = row['credit'] if pd.notna(row['credit']) else 0
        matched = tally_df[tally_df['company'] == party]  # tally_df['company'] is lowercased earlier
        if not matched.empty:
            # use UPPER code to match final_merged (which is uppercase)
            code = matched.iloc[0]['code'].strip().upper()
            if code not in updated_codes:
                match_idx = final_merged[final_merged['emr id'] == code].index
                if not match_idx.empty:
                    idx = match_idx[0]
                    final_merged.at[idx, 'receivable_credit'] = credit_amt
                    final_merged.at[idx, 'outstanding'] = (
                        final_merged.at[idx, 'debit'] - final_merged.at[idx, 'credit'] - credit_amt
                    )
                    updated_codes.add(code)

    # Handle unmatched parties — create new advance rows (EMR ID uppercase)
    all_found_codes = set(final_merged['emr id'].unique())
    unmatched_rows = []
    for _, row in receivable_df.iterrows():
        party_name = row['particulars']
        credit_amt = row['credit'] if pd.notna(row['credit']) else 0
        matched = tally_df[tally_df['company'] == party_name]
        if not matched.empty:
            code = matched.iloc[0]['code'].strip().upper()
            if code not in all_found_codes:
                unmatched_rows.append({
                    "emr id": code,
                    "party name": party_name.title(),
                    "debit": 0,
                    "receivable_credit": 0,
                    "outstanding": 0,
                    "advance_payment": credit_amt,
                    "source": "Unmatched"
                })

    unmatched_df = pd.DataFrame(unmatched_rows)

    # Reposition receivable_credit & outstanding columns next to credit (then remove credit column)
    if 'credit' in final_merged.columns:
        credit_index = final_merged.columns.get_loc('credit')
        cols = list(final_merged.columns)
        for col in ['receivable_credit', 'outstanding']:
            if col in cols:
                cols.remove(col)
                cols.insert(credit_index + 1, col)
        final_merged = final_merged[cols]
        # drop credit column if you don't want it in final output
        final_merged.drop(columns=['credit'], inplace=True)

    # Priority and ordering (EMR IDs are uppercase already)
    priority_emr_ids = {
        "MPCCD", "MPGJ2", "TNPJ", "UPAH", "UPBPAKS", "UPHG", "UPHK", "UPJP",
        "UPMHJ", "UPPLP", "UPPLR", "UPUBJH1", "UPUDJB", "UPUHKJHP", "UPURJL",
        "UPUSDJBW", "UPUTRSJ"
    }

    final_merged['priority'] = final_merged['emr id'].str.upper().apply(
        lambda x: "II" if x in priority_emr_ids else "I"
    )
    cols = ['priority'] + [col for col in final_merged.columns if col != 'priority']
    final_merged = final_merged[cols]
    final_merged['priority_sort'] = final_merged['priority'].map({'II': 0, 'I': 1})
    final_merged = final_merged.sort_values(by='priority_sort').drop(columns=['priority_sort']).reset_index(drop=True)

    # Summaries
    summary_zone = final_merged.groupby('zone')[['debit', 'receivable_credit', 'outstanding']].sum().reset_index()
    summary_region = final_merged.groupby('region')[['debit', 'receivable_credit', 'outstanding']].sum().reset_index()

    st.subheader("✅ Final Preview (Top 50 Rows)")
    st.dataframe(final_merged.head(50))

    st.subheader("📍 Zone-wise Summary")
    st.dataframe(summary_zone)

    st.subheader("📍 Region-wise Summary")
    st.dataframe(summary_region)

    # Write Excel with unmatched (if any)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        final_merged.to_excel(writer, sheet_name="Final Merged", index=False)
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
