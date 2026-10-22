# # import streamlit as st
# # import pandas as pd
# # import io

# # st.set_page_config(page_title="📊 Final Merged & Summary Excel Generator", layout="wide")
# # st.title("📊 Final Merged Excel with Region/Zone Summary")

# # # === File Uploads ===
# # st.sidebar.header("📂 Upload Excel Files")
# # branded_file = st.sidebar.file_uploader("Upload Branded Apr File", type=["xlsx"])
# # rm_file = st.sidebar.file_uploader("Upload RM Job File", type=["xlsx"])
# # master_file = st.sidebar.file_uploader("Upload Master Data File", type=["xlsx"])
# # sale_file = st.sidebar.file_uploader("Upload Sale Invoice File", type=["xlsx"])
# # receivable_file = st.sidebar.file_uploader("Upload Trade Receivable File", type=["xlsx"])

# # if all([branded_file, rm_file, master_file, sale_file, receivable_file]):
# #     # Step 1: Read Files
# #     branded_all = pd.concat(pd.read_excel(branded_file, sheet_name=None), ignore_index=True)
# #     rm_all = pd.concat(pd.read_excel(rm_file, sheet_name=None), ignore_index=True)
# #     branded_all.columns = [col.strip().lower() for col in branded_all.columns]
# #     rm_all.columns = [col.strip().lower() for col in rm_all.columns]

# #     branded_data = branded_all[['particulars', 'vch type', 'vch no.', 'date', 'debit', 'credit']].copy()
# #     branded_data = branded_data[~branded_data['particulars'].astype(str).str.lower().str.contains("total")]
# #     rm_data = rm_all[['particulars', 'vch type', 'vch no.', 'date', 'debit', 'credit']].copy()
# #     rm_data = rm_data[~rm_data['particulars'].astype(str).str.lower().str.contains("total")]

# #     master_df = pd.read_excel(master_file, sheet_name="Kisna Force Master Details ")
# #     tally_df = pd.read_excel(master_file, sheet_name="Tally Ledger Name")
# #     master_df.columns = master_df.columns.str.lower().str.strip()
# #     tally_df.columns = tally_df.columns.str.lower().str.strip()
# #     tally_df['company'] = tally_df['company'].astype(str).str.strip().str.lower()
# #     tally_df['code'] = tally_df['code'].astype(str).str.strip()

# #     particular_to_code = dict(zip(tally_df['company'], tally_df['code']))
# #     for df in [branded_data, rm_data]:
# #         df['emr id'] = df['particulars'].astype(str).str.strip().str.lower().map(particular_to_code)
# #         df['emr id'] = df['emr id'].str.upper()

# #     branded_data['source'] = 'branded'
# #     rm_data['source'] = 'rm'
# #     combined = pd.concat([branded_data, rm_data], ignore_index=True)

# #     final = combined.merge(master_df, on='emr id', how='left')
# #     final['sr no'] = range(1, len(final) + 1)
# #     final = final[['vch type', 'vch no.', 'date', 'debit', 'credit', 'sr no', 'emr id',
# #                    'region', 'zone', 'part', 'state', 'ba code', 'territory', 'city',
# #                    'type', 'status', 'kisna/siva', 'party name', 'nsm', 'zone head']]

# #     sale_df = pd.read_excel(sale_file)
# #     sale_df.columns = sale_df.columns.str.lower()
# #     sale_df.rename(columns={
# #         'doc. date': 'date',
# #         'doc. no.': 'vch no.',
# #         'account code': 'emr id',
# #         'account name': 'party name',
# #         'sr code': 'ba code',
# #         'ref. code': 'state'
# #     }, inplace=True)

# #     final['date'] = pd.to_datetime(final['date'], errors='coerce')
# #     sale_df['date'] = pd.to_datetime(sale_df['date'], errors='coerce')

# #     merged = pd.merge(
# #         final,
# #         sale_df[['date', 'vch no.', 'emr id', 'party name', 'ba code', 'state', 'jso order no']],
# #         on=['date', 'vch no.', 'emr id', 'party name', 'ba code', 'state'],
# #         how='left'
# #     )
# #     # print(merged)

# #     def get_remark(order_no):
# #         if pd.isna(order_no): return ''
# #         order_no = str(order_no).upper()
# #         if any(x in order_no for x in ['KCO', 'KCD']): return "KCO | Extra Gold IGI"
# #         elif any(x in order_no for x in ['RLS', 'SNL']): return "SNMCC | Line Sale"
# #         elif any(x in order_no for x in ['KSN', 'RAD']): return "Invoice ready"
# #         elif 'HKJ' in order_no: return "Retailer ledger Dr. | KIOS"
# #         return ''

# #     exploded = merged.dropna(subset=['jso order no']).copy()
# #     exploded['jso order no'] = exploded['jso order no'].astype(str)
# #     exploded = exploded.assign(jso_order_no=exploded['jso order no'].str.split(',')).explode('jso_order_no')
# #     exploded['jso_order_no'] = exploded['jso_order_no'].str.strip()
# #     exploded['remark'] = exploded['jso_order_no'].apply(get_remark)

# #     exploded['row_number'] = exploded.groupby('vch no.').cumcount()
# #     for col in ['vch no.', 'debit', 'credit', 'receivable_credit', 'outstanding']:
# #         exploded.loc[exploded['row_number'] > 0, col] = None
# #     exploded.drop(columns=['row_number'], inplace=True)
# #     exploded.rename(columns={'jso_order_no': 'jso order no'}, inplace=True)

# #     base_cols = [col for col in merged.columns if col not in ['jso order no', 'remark']]
# #     merged_cleaned = merged[merged['jso order no'].isna()][base_cols]

# #     # Deduplicate columns and align schema
# #     exploded = exploded.loc[:, ~exploded.columns.duplicated()]
# #     merged_cleaned = merged_cleaned.loc[:, ~merged_cleaned.columns.duplicated()]
# #     common_cols = merged_cleaned.columns.intersection(exploded.columns).tolist()
# #     merged_cleaned = merged_cleaned[common_cols]
# #     exploded = exploded[common_cols]

# #     final_merged = pd.concat([merged_cleaned, exploded], ignore_index=True)

# #     receivable_df = pd.read_excel(receivable_file)
# #     receivable_df.columns = receivable_df.columns.str.lower()
# #     receivable_df['particulars'] = receivable_df['particulars'].astype(str).str.strip().str.lower()
# #     final_merged['emr id'] = final_merged['emr id'].astype(str).str.strip().str.upper()
# #     final_merged['debit'] = final_merged['debit'].fillna(0)
# #     final_merged['credit'] = final_merged.get('credit', 0).fillna(0)
# #     if 'receivable_credit' in final_merged.columns:
# #         final_merged['receivable_credit'] = final_merged['receivable_credit'].fillna(0)
# #     else:
# #         final_merged['receivable_credit'] = 0
# #     final_merged['outstanding'] = final_merged['debit'] - final_merged['credit']

# #     updated_codes = set()
# #     for _, row in receivable_df.iterrows():
# #         party = row['particulars']
# #         credit_amt = row['credit'] if pd.notna(row['credit']) else 0
# #         matched = tally_df[tally_df['company'] == party]
# #         if not matched.empty:
# #             code = matched.iloc[0]['code'].strip().upper()
# #             if code not in updated_codes:
# #                 match_idx = final_merged[final_merged['emr id'] == code].index
# #                 if not match_idx.empty:
# #                     idx = match_idx[0]
# #                     final_merged.at[idx, 'receivable_credit'] = credit_amt
# #                     final_merged.at[idx, 'outstanding'] = (
# #                         final_merged.at[idx, 'debit'] - final_merged.at[idx, 'credit'] - credit_amt
# #                     )
# #                     updated_codes.add(code)

# #     all_found_codes = set(final_merged['emr id'].unique())
# #     unmatched_rows = []
# #     for _, row in receivable_df.iterrows():
# #         party_name = row['particulars']
# #         credit_amt = row['credit'] if pd.notna(row['credit']) else 0
# #         matched = tally_df[tally_df['company'] == party_name]
# #         if not matched.empty:
# #             code = matched.iloc[0]['code'].strip().upper()
# #             if code not in all_found_codes:
# #                 master_match = master_df[master_df['emr id'].str.upper() == code]
# #                 unmatched_rows.append({
# #                     "vch type": "",
# #                     "vch no.": "",
# #                     "date": "",
# #                     "debit": None,
# #                     "receivable_credit": None,
# #                     "outstanding": None,
# #                     "advance_payment": credit_amt,
# #                     "emr id": code,
# #                     "party name": party_name.title(),
# #                     "source": "Unmatched",
# #                     "zone": master_match['zone'].iloc[0] if not master_match.empty else "",
# #                     "region": master_match['region'].iloc[0] if not master_match.empty else ""
# #                 })

# #     unmatched_df = pd.DataFrame(unmatched_rows)
# #     final_merged = pd.concat([merged_cleaned, exploded,unmatched_df], ignore_index=True)

# #     # Ensure 'jso number' and 'remark' are in final_merged
# #     if 'jso number' in exploded.columns and 'remark' in exploded.columns:
# #         final_merged = pd.concat([merged_cleaned, exploded], ignore_index=True)
# #         # Re-add the 'jso number' and 'remark' columns
# #         if 'jso number' not in final_merged.columns:
# #             final_merged['jso number'] = None
# #         if 'remark' not in final_merged.columns:
# #             final_merged['remark'] = None

# #     if 'credit' in final_merged.columns:
# #         credit_index = final_merged.columns.get_loc('credit')
# #         cols = list(final_merged.columns)
# #         for col in ['receivable_credit', 'outstanding']:
# #             if col in cols:
# #                 cols.remove(col)
# #                 cols.insert(credit_index + 1, col)
# #         final_merged = final_merged[cols]
# #         final_merged.drop(columns=['credit'], inplace=True)

# #     priority_emr_ids = {
# #         "MPCCD", "MPGJ2", "TNPJ", "UPAH", "UPBPAKS", "UPHG", "UPHK", "UPJP",
# #         "UPMHJ", "UPPLP", "UPPLR", "UPUBJH1", "UPUDJB", "UPUHKJHP", "UPURJL",
# #         "UPUSDJBW", "UPUTRSJ"
# #     }

# #     final_merged['priority'] = final_merged['emr id'].str.upper().apply(
# #         lambda x: "II" if x in priority_emr_ids else "I"
# #     )
# #     cols = ['priority'] + [col for col in final_merged.columns if col != 'priority']
# #     final_merged = final_merged[cols]
# #     final_merged['priority_sort'] = final_merged['priority'].map({'II': 0, 'I': 1})
# #     final_merged = final_merged.sort_values(by='priority_sort').drop(columns=['priority_sort']).reset_index(drop=True)

# #     summary_zone = final_merged.groupby('zone')[['debit', 'receivable_credit', 'outstanding']].sum(numeric_only=True).reset_index()
# #     summary_region = final_merged.groupby('region')[['debit', 'receivable_credit', 'outstanding']].sum(numeric_only=True).reset_index()

# #     st.subheader("✅ Final Preview (Top 50 Rows)")
# #     st.dataframe(final_merged.head(50))

# #     st.subheader("📍 Zone-wise Summary")
# #     st.dataframe(summary_zone)

# #     st.subheader("📍 Region-wise Summary")
# #     st.dataframe(summary_region)

# #     output = io.BytesIO()
# #     with pd.ExcelWriter(output, engine='openpyxl') as writer:
# #         final_merged.to_excel(writer, sheet_name="Final Merged", index=False)
# #         summary_zone.to_excel(writer, sheet_name="Zone Summary", index=False)
# #         summary_region.to_excel(writer, sheet_name="Region Summary", index=False)
# #         if not unmatched_df.empty:
# #             unmatched_df.to_excel(writer, sheet_name="Unmatched Parties", index=False)
# #     output.seek(0)

# #     st.download_button(
# #         label="📅 Download Final Excel with Summaries",
# #         data=output,
# #         file_name="Final_Merged_Summary.xlsx",
# #         mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
# #     )
# # else:
# #     st.warning("📂 Please upload all 5 required Excel files to proceed.")


# import streamlit as st
# import pandas as pd
# import io
# from main import process_kisna_files, process_with_outstanding_sorted, calculate_region_zone_summary  # Import your functions

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
#     # === Run both functions ===
#     remark_df = process_kisna_files(
#         branded_file, rm_file, master_file, sale_file
#     )
#     outstanding_df = process_with_outstanding_sorted(
#         branded_file, rm_file, master_file,sale_file, receivable_file
#     )
#     region_summary, zone_summary = calculate_region_zone_summary(outstanding_df)

#     # === Save all four sheets ===
#     output_buffer = io.BytesIO()
#     with pd.ExcelWriter(output_buffer, engine="openpyxl") as writer:
#         remark_df.to_excel(writer, index=False, sheet_name="Party Name with Remark")
#         outstanding_df.to_excel(writer, index=False, sheet_name="Party Name with Outstanding")
#         region_summary.to_excel(writer, index=False, sheet_name="Region Summary")
#         zone_summary.to_excel(writer, index=False, sheet_name="Zone Summary")

#     st.success("✅ All 4 sheets generated successfully!")
#     st.download_button(
#         label="📥 Download Final Excel",
#         data=output_buffer.getvalue(),
#         file_name="Final_Merged_Summary.xlsx",
#         mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
#     )


