# import streamlit as st
# import pandas as pd
# import io
 
# st.set_page_config(page_title="📊 Final Merged & Summary Excel Generator", layout="wide")
# st.title("📊 Final Merged Excel with Region/Zone Summary")
 
# # === File Uploads ===
# st.sidebar.header("📂 Upload Excel Files")
# branded_file = st.sidebar.file_uploader("Upload Branded Apr File", type=["xlsx"])
# rm_file = st.sidebar.file_uploader("Upload RM Job File", type=["xlsx"])
# master_file = st.sidebar.file_uploader("Upload Master Data File", type=["xlsx"])
# sale_file = st.sidebar.file_uploader("Upload Sale Invoice File", type=["xlsx"])
# receivable_file = st.sidebar.file_uploader("Upload Trade Receivable File", type=["xlsx"])
 
# if all([branded_file, rm_file, master_file, sale_file, receivable_file]):
#     # Step 1: Read Files
#     branded_all = pd.concat(pd.read_excel(branded_file, sheet_name=None), ignore_index=True)
#     rm_all = pd.concat(pd.read_excel(rm_file, sheet_name=None), ignore_index=True)
#     branded_all.columns = [col.strip().lower() for col in branded_all.columns]
#     rm_all.columns = [col.strip().lower() for col in rm_all.columns]
 
#     branded_data = branded_all[['particulars', 'vch type', 'vch no.', 'date', 'debit', 'credit']].copy()
#     branded_data = branded_data[~branded_data['particulars'].astype(str).str.lower().str.contains("total")]
#     rm_data = rm_all[['particulars', 'vch type', 'vch no.', 'date', 'debit', 'credit']].copy()
#     rm_data = rm_data[~rm_data['particulars'].astype(str).str.lower().str.contains("total")]
 
#     master_df = pd.read_excel(master_file, sheet_name="Kisna Force Master Details ")
#     tally_df = pd.read_excel(master_file, sheet_name="Tally Ledger Name")
#     master_df.columns = master_df.columns.str.lower().str.strip()
#     tally_df.columns = tally_df.columns.str.lower().str.strip()
#     tally_df['company'] = tally_df['company'].astype(str).str.strip().str.lower()
#     tally_df['code'] = tally_df['code'].astype(str).str.strip()
 
#     particular_to_code = dict(zip(tally_df['company'], tally_df['code']))
#     for df in [branded_data, rm_data]:
#         df['emr id'] = df['particulars'].astype(str).str.strip().str.lower().map(particular_to_code)
 
#     branded_data['source'] = 'branded'
#     rm_data['source'] = 'rm'
#     combined = pd.concat([branded_data, rm_data], ignore_index=True)
 
#     final = combined.merge(master_df, on='emr id', how='left')
#     final['sr no'] = range(1, len(final) + 1)
#     final = final[[ 'vch type', 'vch no.', 'date', 'debit', 'credit', 'sr no', 'emr id',
#                     'region', 'zone', 'part', 'state', 'ba code', 'territory', 'city',
#                     'type', 'status', 'kisna/siva', 'party name', 'nsm', 'zone head']]
 
#     sale_df = pd.read_excel(sale_file)
#     sale_df.columns = sale_df.columns.str.lower()
#     sale_df.rename(columns={
#         'doc. date': 'date',
#         'doc. no.': 'vch no.',
#         'account code': 'emr id',
#         'account name': 'party name',
#         'sr code': 'ba code',
#         'ref. code': 'state'
#     }, inplace=True)
 
#     final['date'] = pd.to_datetime(final['date'], errors='coerce')
#     sale_df['date'] = pd.to_datetime(sale_df['date'], errors='coerce')
 
#     final_merged = pd.merge(
#         final,
#         sale_df[['date', 'vch no.', 'emr id', 'party name', 'ba code', 'state', 'jso order no']],
#         on=['date', 'vch no.', 'emr id', 'party name', 'ba code', 'state'],
#         how='left'
#     )
 
#     def get_remark(order_no):
#         if pd.isna(order_no): return ''
#         order_no = str(order_no).upper()
#         if any(x in order_no for x in ['KCO', 'KCD']): return "KCO | Extra Gold IGI"
#         elif any(x in order_no for x in ['RLS', 'SNL']): return "SNMCC | Line Sale"
#         elif any(x in order_no for x in ['KSN', 'RAD']): return "Invoice ready"
#         elif 'HKJ' in order_no: return "Retailer ledger Dr. | KIOS"
#         return ''
 
#     final_merged['remark'] = final_merged['jso order no'].apply(get_remark)
 
#     receivable_df = pd.read_excel(receivable_file)
#     receivable_df.columns = receivable_df.columns.str.lower()
#     receivable_df['particulars'] = receivable_df['particulars'].astype(str).str.strip().str.lower()
#     tally_df['company'] = tally_df['company'].astype(str).str.strip().str.lower()
 
#     final_merged['emr id'] = final_merged['emr id'].astype(str).str.strip().str.lower()
#     final_merged['debit'] = final_merged['debit'].fillna(0)
#     final_merged['credit'] = final_merged['credit'].fillna(0)
#     final_merged['receivable_credit'] = 0.0
#     final_merged['outstanding'] = final_merged['debit'] - final_merged['credit']
 
#     updated_codes = set()
#     for _, row in receivable_df.iterrows():
#         party = row['particulars']
#         credit_amt = row['credit'] if pd.notna(row['credit']) else 0
#         matched = tally_df[tally_df['company'] == party]
#         if not matched.empty:
#             code = matched.iloc[0]['code'].strip().lower()
#             if code not in updated_codes:
#                 match_idx = final_merged[final_merged['emr id'] == code].index
#                 if not match_idx.empty:
#                     idx = match_idx[0]
#                     final_merged.at[idx, 'receivable_credit'] = credit_amt
#                     final_merged.at[idx, 'outstanding'] = (
#                         final_merged.at[idx, 'debit'] - final_merged.at[idx, 'credit'] - credit_amt
#                     )
#                     updated_codes.add(code)
 
#     if 'credit' in final_merged.columns:
#         credit_index = final_merged.columns.get_loc('credit')
#         cols = list(final_merged.columns)
#         for col in ['receivable_credit', 'outstanding']:
#             cols.remove(col)
#             cols.insert(credit_index + 1, col)
#         final_merged = final_merged[cols]
#         final_merged.drop(columns=['credit'], inplace=True)
 
#     priority_emr_ids = {
#         "MPCCD", "MPGJ2", "TNPJ", "UPAH", "UPBPAKS", "UPHG", "UPHK", "UPJP",
#         "UPMHJ", "UPPLP", "UPPLR", "UPUBJH1", "UPUDJB", "UPUHKJHP", "UPURJL",
#         "UPUSDJBW", "UPUTRSJ"
#     }
 
#     final_merged['priority'] = final_merged['emr id'].str.upper().apply(
#         lambda x: "II" if x in priority_emr_ids else "I"
#     )
#     cols = ['priority'] + [col for col in final_merged.columns if col != 'priority']
#     final_merged = final_merged[cols]
#     final_merged['priority_sort'] = final_merged['priority'].map({'II': 0, 'I': 1})
#     final_merged = final_merged.sort_values(by='priority_sort').drop(columns=['priority_sort']).reset_index(drop=True)
 
#     # === Zone-wise and Region-wise summaries ===
#     summary_zone = final_merged.groupby('zone')[['debit', 'receivable_credit', 'outstanding']].sum().reset_index()
#     summary_region = final_merged.groupby('region')[['debit', 'receivable_credit', 'outstanding']].sum().reset_index()
 
#     st.subheader("✅ Final Preview (Top 50 Rows)")
#     st.dataframe(final_merged.head(50))
 
#     st.subheader("📍 Zone-wise Summary")
#     st.dataframe(summary_zone)
 
#     st.subheader("📍 Region-wise Summary")
#     st.dataframe(summary_region)
 
#     output = io.BytesIO()
#     with pd.ExcelWriter(output, engine='openpyxl') as writer:
#         final_merged.to_excel(writer, sheet_name="Final Merged", index=False)
#         summary_zone.to_excel(writer, sheet_name="Zone Summary", index=False)
#         summary_region.to_excel(writer, sheet_name="Region Summary", index=False)
#     output.seek(0)
 
#     st.download_button(
#         label="📥 Download Final Excel with Summaries",
#         data=output,
#         file_name="Final_Merged_Summary.xlsx",
#         mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
#     )
# else:
#     st.warning("📂 Please upload all 5 required Excel files to proceed.")
 
 
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
 
    master_df = pd.read_excel(master_file, sheet_name="Kisna Force Master Details ")
    tally_df = pd.read_excel(master_file, sheet_name="Tally Ledger Name")
    master_df.columns = master_df.columns.str.lower().str.strip()
    tally_df.columns = tally_df.columns.str.lower().str.strip()
    tally_df['company'] = tally_df['company'].astype(str).str.strip().str.lower()
    tally_df['code'] = tally_df['code'].astype(str).str.strip()
 
    particular_to_code = dict(zip(tally_df['company'], tally_df['code']))
    for df in [branded_data, rm_data]:
        df['emr id'] = df['particulars'].astype(str).str.strip().str.lower().map(particular_to_code)
 
    branded_data['source'] = 'branded'
    rm_data['source'] = 'rm'
    combined = pd.concat([branded_data, rm_data], ignore_index=True)
 
    final = combined.merge(master_df, on='emr id', how='left')
    final['sr no'] = range(1, len(final) + 1)
    final = final[['vch type', 'vch no.', 'date', 'debit', 'credit', 'sr no', 'emr id',
                   'region', 'zone', 'part', 'state', 'ba code', 'territory', 'city',
                   'type', 'status', 'kisna/siva', 'party name', 'nsm', 'zone head', 'source']]
 
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
 
    def get_remark(order_no):
        if pd.isna(order_no): return ''
        order_no = str(order_no).upper()
        if any(x in order_no for x in ['KCO', 'KCD']): return "KCO | Extra Gold IGI"
        elif any(x in order_no for x in ['RLS', 'SNL']): return "SNMCC | Line Sale"
        elif any(x in order_no for x in ['KSN', 'RAD']): return "Invoice ready"
        elif 'HKJ' in order_no: return "Retailer ledger Dr. | KIOS"
        return ''
 
    final_merged['remark'] = final_merged['jso order no'].apply(get_remark)
 
    receivable_df = pd.read_excel(receivable_file)
    receivable_df.columns = receivable_df.columns.str.lower()
    receivable_df['particulars'] = receivable_df['particulars'].astype(str).str.strip().str.lower()
    tally_df['company'] = tally_df['company'].astype(str).str.strip().str.lower()
 
    final_merged['emr id'] = final_merged['emr id'].astype(str).str.strip().str.lower()
    final_merged['debit'] = final_merged['debit'].fillna(0)
    final_merged['credit'] = final_merged['credit'].fillna(0)
    final_merged['receivable_credit'] = 0.0
    final_merged['outstanding'] = final_merged['debit'] - final_merged['credit']
    final_merged['advance_payment'] = 0.0
 
    updated_codes = set()
    for _, row in receivable_df.iterrows():
        party = row['particulars']
        credit_amt = row['credit'] if pd.notna(row['credit']) else 0
        matched = tally_df[tally_df['company'] == party]
        if not matched.empty:
            code = matched.iloc[0]['code'].strip().lower()
            if code not in updated_codes:
                match_idx = final_merged[final_merged['emr id'] == code].index
                if not match_idx.empty:
                    idx = match_idx[0]
                    final_merged.at[idx, 'receivable_credit'] = credit_amt
                    final_merged.at[idx, 'outstanding'] = (
                        final_merged.at[idx, 'debit'] - final_merged.at[idx, 'credit'] - credit_amt
                    )
                    updated_codes.add(code)
 
    # Handle unmatched parties — create new advance rows
    known_emr_ids = set(final_merged['emr id'].unique())
    advance_rows = []
    for _, row in receivable_df.iterrows():
        party = row['particulars']
        credit_amt = row['credit'] if pd.notna(row['credit']) else 0
        matched_tally = tally_df[tally_df['company'] == party]
        if not matched_tally.empty:
            emr_code = matched_tally.iloc[0]['code'].strip().lower()
            if emr_code not in known_emr_ids:
                matched_master = master_df[master_df['emr id'] == emr_code]
                master_row = matched_master.iloc[0].to_dict() if not matched_master.empty else {
                    'region': '', 'zone': '', 'part': '', 'state': '', 'ba code': '',
                    'territory': '', 'city': '', 'type': '', 'status': '', 'kisna/siva': '',
                    'party name': '', 'nsm': '', 'zone head': ''
                }
                new_row = {
                    'vch type': '', 'vch no.': '', 'date': pd.NaT,
                    'debit': 0.0, 'receivable_credit': 0.0, 'outstanding': 0.0, 'credit': 0.0,
                    'sr no': len(final_merged) + len(advance_rows) + 1,
                    'emr id': emr_code,
                    **master_row,
                    'source': 'advance',
                    'remark': 'Advance Payment',
                    'advance_payment': credit_amt,
                    'jso order no': ''
                }
                advance_rows.append(new_row)
 
    if advance_rows:
        final_merged = pd.concat([final_merged, pd.DataFrame(advance_rows)], ignore_index=True)
 
    # Amount only in first row of each vch no.
    final_merged = final_merged.sort_values(by=['vch no.', 'date']).reset_index(drop=True)
    final_merged[['debit', 'credit', 'receivable_credit', 'outstanding']] = final_merged.groupby('vch no.').apply(
        lambda g: g.assign(
            debit=[g.iloc[0]['debit']] + [0] * (len(g) - 1),
            credit=[g.iloc[0]['credit']] + [0] * (len(g) - 1),
            receivable_credit=[g.iloc[0]['receivable_credit']] + [0] * (len(g) - 1),
            outstanding=[g.iloc[0]['outstanding']] + [0] * (len(g) - 1)
        )
    ).reset_index(drop=True)[['debit', 'credit', 'receivable_credit', 'outstanding']]
 
    if 'credit' in final_merged.columns:
        credit_index = final_merged.columns.get_loc('credit')
        cols = list(final_merged.columns)
        for col in ['receivable_credit', 'outstanding']:
            cols.remove(col)
            cols.insert(credit_index + 1, col)
        final_merged = final_merged[cols]
        final_merged.drop(columns=['credit'], inplace=True)
 
    # Add Priority
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
 
    # Summary with total rows
    summary_zone = final_merged.groupby('zone')[['debit', 'receivable_credit', 'outstanding', 'advance_payment']].sum().reset_index()
    summary_region = final_merged.groupby('region')[['debit', 'receivable_credit', 'outstanding', 'advance_payment']].sum().reset_index()
 
    summary_zone_total = summary_zone[['debit', 'receivable_credit', 'outstanding', 'advance_payment']].sum().to_dict()
    summary_zone_total['zone'] = 'Total'
    summary_zone = pd.concat([summary_zone, pd.DataFrame([summary_zone_total])], ignore_index=True)
 
    summary_region_total = summary_region[['debit', 'receivable_credit', 'outstanding', 'advance_payment']].sum().to_dict()
    summary_region_total['region'] = 'Total'
    summary_region = pd.concat([summary_region, pd.DataFrame([summary_region_total])], ignore_index=True)
 
    # Streamlit Preview
    st.subheader("✅ Final Preview (Top 1000 Rows)")
    st.dataframe(final_merged.head(1000).style.apply(
        lambda row: ['background-color: #FFF3CD' if row['source'] == 'advance' else '' for _ in row], axis=1
    ))
 
    st.subheader("📍 Zone-wise Summary")
    st.dataframe(summary_zone)
 
    st.subheader("📍 Region-wise Summary")
    st.dataframe(summary_region)
    # === Optional: Download Advance Payments Only ===
    advance_only = final_merged[final_merged['source'] == 'advance'].copy()
 
    if not advance_only.empty:
        output_advance = io.BytesIO()
        with pd.ExcelWriter(output_advance, engine='openpyxl') as writer:
            advance_only.to_excel(writer, sheet_name="Advance Payments", index=False)
        output_advance.seek(0)
 
        st.download_button(
            label="📥 Download Advance Payments Excel",
            data=output_advance,
            file_name="Advance_Payments_Only.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
 
    # Excel Export
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        final_merged.to_excel(writer, sheet_name="Final Merged", index=False)
        summary_zone.to_excel(writer, sheet_name="Zone Summary", index=False)
        summary_region.to_excel(writer, sheet_name="Region Summary", index=False)
    output.seek(0)
 
    st.download_button(
        label="📥 Download Final Excel with Summaries",
        data=output,
        file_name="Final_Merged_Summary.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.warning("📂 Please upload all 5 required Excel files to proceed.")