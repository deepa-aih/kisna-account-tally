import pandas as pd
 
# === File Paths ===
branded_file = r"D:\kisna\work\assets\Branded Apr- 25-Jun -25.xlsx"
rm_file = r"D:\kisna\work\assets\RM JOb.xlsx"
master_file = r"D:\kisna\work\assets\Master data.xlsx"
sale_file = r"D:\kisna\work\assets\Sale Invoice vs Order Number.xlsx"
receivable_file = r"D:\kisna\work\assets\Trade Receivable.xlsx"
 
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
 
# ==== Step 5: Add Remark ====
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
 
# ==== Step 6: Trade Receivable Matching and First Occurrence Update ====
receivable_df = pd.read_excel(receivable_file)
receivable_df.columns = receivable_df.columns.str.lower()
receivable_df['particulars'] = receivable_df['particulars'].astype(str).str.strip().str.lower()
tally_df['company'] = tally_df['company'].astype(str).str.strip().str.lower()
 
final_merged['emr id'] = final_merged['emr id'].astype(str).str.strip().str.lower()
final_merged['debit'] = final_merged['debit'].fillna(0)
final_merged['credit'] = final_merged['credit'].fillna(0)
final_merged['receivable_credit'] = 0.0
final_merged['outstanding'] = final_merged['debit'] - final_merged['credit']
 
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
 
# Reorder columns: Insert after 'credit'
if 'credit' in final_merged.columns:
    credit_index = final_merged.columns.get_loc('credit')
    cols = list(final_merged.columns)
    for col in ['receivable_credit', 'outstanding']:
        cols.remove(col)
        cols.insert(credit_index + 1, col)
    final_merged = final_merged[cols]
    final_merged.drop(columns=['credit'], inplace=True)
 
# ==== Step 7: Add Priority Column ====
priority_emr_ids = {
    "MPCCD", "MPGJ2", "TNPJ", "UPAH", "UPBPAKS", "UPHG", "UPHK", "UPJP",
    "UPMHJ", "UPPLP", "UPPLR", "UPUBJH1", "UPUDJB", "UPUHKJHP", "UPURJL",
    "UPUSDJBW", "UPUTRSJ"
}
 
final_merged['priority'] = final_merged['emr id'].str.upper().apply(
    lambda x: "II" if x in priority_emr_ids else "I"
)
 
# Move 'priority' to the first column
cols = ['priority'] + [col for col in final_merged.columns if col != 'priority']
final_merged = final_merged[cols]
 
# Sort so Priority II rows come first
final_merged['priority_sort'] = final_merged['priority'].map({'II': 0, 'I': 1})
final_merged = final_merged.sort_values(by='priority_sort').drop(columns=['priority_sort']).reset_index(drop=True)
 
# ==== Save to ``
# ==== Save to Excel ====
output_file = "Final_Merged_Updated.xlsx"
final_merged.to_excel(output_file, index=False, engine='openpyxl')
 
# === Step 8: Generate Zone-wise and Region-wise summaries ===
 
# === Step 8: Generate Zone-wise and Region-wise summaries with Remaining ===
 
# Group by Zone
# zone_summary = final_merged.groupby('zone').agg(
#     total_debit=pd.NamedAgg(column='debit', aggfunc='sum'),
#     total_credit=pd.NamedAgg(column='receivable_credit', aggfunc='sum'),
#     count=pd.NamedAgg(column='emr id', aggfunc='count')
# ).reset_index()
 
 
# zone_summary['remaining_amount_needed'] = zone_summary['total_debit'] - zone_summary['total_credit']
 
# # Group by Region
# region_summary = final_merged.groupby('region').agg(
#     total_debit=pd.NamedAgg(column='debit', aggfunc='sum'),
#     total_credit=pd.NamedAgg(column='receivable_credit', aggfunc='sum'),
#     count=pd.NamedAgg(column='emr id', aggfunc='count')
# ).reset_index()
 
# region_summary['remaining_amount_needed'] = region_summary['total_debit'] - region_summary['total_credit']
 
# # === Step 9: Save to separate Excel file: Group_Summary.xlsx ===
# group_summary_file = "Group_Summary.xlsx"
# with pd.ExcelWriter(group_summary_file, engine='openpyxl') as writer:
#     zone_summary.to_excel(writer, sheet_name='Zone_Summary', index=False)
#     region_summary.to_excel(writer, sheet_name='Region_Summary', index=False)
 
# print("📁 Group Summary Excel saved as:", group_summary_file)
# print("📈 Zone Summary Preview:\n", zone_summary.head())
# print("📍 Region Summary Preview:\n", region_summary.head())
