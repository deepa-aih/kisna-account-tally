import pandas as pd
import streamlit as st
import io

st.set_page_config(page_title="Final Merged Report", layout="wide")
st.title("📊 Final Merged Excel Generator")

# === File Uploads ===
st.sidebar.header("📂 Upload Required Excel Files")

branded_file = st.sidebar.file_uploader("Upload Branded Apr File", type=["xlsx"])
rm_file = st.sidebar.file_uploader("Upload RM Job File", type=["xlsx"])
master_file = st.sidebar.file_uploader("Upload Master Data File", type=["xlsx"])
sale_file = st.sidebar.file_uploader("Upload Sale Invoice File", type=["xlsx"])
receivable_file = st.sidebar.file_uploader("Upload Trade Receivable File", type=["xlsx"])

if all([branded_file, rm_file, master_file, sale_file, receivable_file]):
    # ==== Step 1: Read Branded & RM Files ====
    branded_all = pd.concat(pd.read_excel(branded_file, sheet_name=None), ignore_index=True)
    rm_all = pd.concat(pd.read_excel(rm_file, sheet_name=None), ignore_index=True)

    branded_all.columns = [col.strip().lower() for col in branded_all.columns]
    rm_all.columns = [col.strip().lower() for col in rm_all.columns]

    branded_data = branded_all[['particulars', 'vch type', 'vch no.', 'date', 'debit', 'credit']].copy()
    branded_data = branded_data[~branded_data['particulars'].astype(str).str.lower().str.contains("total")]

    rm_data = rm_all[['particulars', 'vch type', 'vch no.', 'date', 'debit', 'credit']].copy()
    rm_data = rm_data[~rm_data['particulars'].astype(str).str.lower().str.contains("total")]

    # ==== Step 2: Load Master ====
    master_df = pd.read_excel(master_file, sheet_name="Kisna Force Master Details ")
    tally_df = pd.read_excel(master_file, sheet_name="Tally Ledger Name")

    master_df.columns = [col.strip().lower() for col in master_df.columns]
    tally_df.columns = [col.strip().lower() for col in tally_df.columns]

    tally_df['company'] = tally_df['company'].astype(str).str.strip().str.lower()
    tally_df['code'] = tally_df['code'].astype(str).str.strip()

    particular_to_code = dict(zip(tally_df['company'], tally_df['code']))

    for df in [branded_data, rm_data]:
        df['emr id'] = df['particulars'].astype(str).str.strip().str.lower().map(particular_to_code)

    branded_data['source'] = 'branded'
    rm_data['source'] = 'rm'
    combined = pd.concat([branded_data, rm_data], ignore_index=True)

    # ==== Step 3: Merge with Master ====
    final = combined.merge(master_df, on='emr id', how='left')
    final['sr no'] = range(1, len(final) + 1)

    final = final[[
        'vch type', 'vch no.', 'date', 'debit', 'credit', 'sr no', 'emr id',
        'region', 'zone', 'part', 'state', 'ba code', 'territory', 'city',
        'type', 'status', 'kisna/siva', 'party name', 'nsm', 'zone head'
    ]]

    # ==== Step 4: Merge JSO Order No ====
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

    final['date'] = pd.to_datetime(final['date'], errors='coerce')
    sale_df['date'] = pd.to_datetime(sale_df['date'], errors='coerce')

    final_merged = pd.merge(
        final,
        sale_df[['date', 'vch no.', 'emr id', 'party name', 'ba code', 'state', 'jso order no']],
        on=['date', 'vch no.', 'emr id', 'party name', 'ba code', 'state'],
        how='left'
    )

    # ==== Step 5: Add Remark Based on JSO Order No ====
    def get_remark(order_no):
        if pd.isna(order_no):
            return ''
        order_no = str(order_no).upper()
        if any(x in order_no for x in ['KCO', 'KCD']):
            return "KCO | Extra Gold IGI"
        elif any(x in order_no for x in ['RLS', 'SNL']):
            return "SNMCC | Line Sale"
        elif any(x in order_no for x in ['KSN', 'RAD']):
            return "Invoice ready"
        elif 'HKJ' in order_no:
            return "Retailer ledger Dr. | KIOS"
        else:
            return ''

    final_merged['remark'] = final_merged['jso order no'].apply(get_remark)

    # ==== Step 6: Add Only Outstanding ====
    receivable_df = pd.read_excel(receivable_file)
    receivable_df.columns = receivable_df.columns.str.lower()

    receivable_df['particulars'] = receivable_df['particulars'].astype(str).str.strip().str.lower()
    final_merged['party name lower'] = final_merged['party name'].astype(str).str.strip().str.lower()

    # Step 6.1: Total debit/credit from final_merged per party
    existing_sum = final_merged.groupby('party name lower')[['debit', 'credit']].sum().reset_index()
    existing_sum.rename(columns={'debit': 'existing debit', 'credit': 'existing credit'}, inplace=True)

    # Step 6.2: Total summary from trade receivable
    summary_df = receivable_df.groupby('particulars')[['debit', 'credit']].sum().reset_index()
    summary_df.rename(columns={'debit': 'total debit', 'credit': 'total credit'}, inplace=True)

    # Step 6.3: Merge and calculate outstanding
    merged_summary = pd.merge(summary_df, existing_sum, left_on='particulars', right_on='party name lower', how='left')
    merged_summary['existing debit'] = merged_summary['existing debit'].fillna(0)
    merged_summary['existing credit'] = merged_summary['existing credit'].fillna(0)

    merged_summary['outstanding'] = (merged_summary['total debit'] - merged_summary['existing debit']) - \
                                     (merged_summary['total credit'] - merged_summary['existing credit'])

    # Step 6.4: Merge only outstanding into final_merged
    final_merged = pd.merge(
        final_merged,
        merged_summary[['particulars', 'outstanding']],
        left_on='party name lower',
        right_on='particulars',
        how='left'
    )

    final_merged.drop(columns=['party name lower', 'particulars'], inplace=True)

    # ==== Preview Table ====
    st.write("✅ Preview Final Data (Top 50 Rows)")
    st.dataframe(final_merged.head(50))

    # ==== Excel Export ====
    output = io.BytesIO()
    final_merged.to_excel(output, index=False, engine='openpyxl')
    output.seek(0)

    st.download_button(
        label="📥 Download Final Merged Excel",
        data=output,
        file_name="Final_Merged_Output.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.warning("📂 Please upload all required files from the sidebar to proceed.")
