import pandas as pd

# ==== Load all source files ====
master_file = r"D:\kisna\work\assets\Master data.xlsx"
branded_file = r"D:\kisna\work\assets\Branded Apr- 25-Jun -25.xlsx"
rm_file = r"D:\kisna\work\assets\RM JOb.xlsx"
sale_file = r"D:\kisna\work\assets\Sale Invoice vs Order Number.xlsx"
trade_receivable_file = r"D:\kisna\work\assets\Trade Receivable.xlsx"  # NEW

# ==== Load and clean Branded and RM sheets ====
branded_all = pd.concat(pd.read_excel(branded_file, sheet_name=None), ignore_index=True)
rm_all = pd.concat(pd.read_excel(rm_file, sheet_name=None), ignore_index=True)
branded_all.columns = [col.strip().lower() for col in branded_all.columns]
rm_all.columns = [col.strip().lower() for col in rm_all.columns]

branded_data = branded_all[['particulars', 'vch type', 'vch no.', 'date', 'debit', 'credit']].copy()
branded_data = branded_data[~branded_data['particulars'].astype(str).str.lower().str.contains("total")]

rm_data = rm_all[['particulars', 'vch type', 'vch no.', 'date', 'debit', 'credit']].copy()
rm_data = rm_data[~rm_data['particulars'].astype(str).str.lower().str.contains("total")]

# ==== Load Master & Code Mapping ====
master_df = pd.read_excel(master_file, sheet_name="Kisna Force Master Details ")
tally_df = pd.read_excel(master_file, sheet_name="Tally Ledger Name")
master_df.columns = [col.strip().lower() for col in master_df.columns]
tally_df.columns = [col.strip().lower() for col in tally_df.columns]

# Create mapping: particular → emr id
tally_df['company'] = tally_df['company'].astype(str).str.strip().str.lower()
tally_df['code'] = tally_df['code'].astype(str).str.strip()
particular_to_code = dict(zip(tally_df['company'], tally_df['code']))

# ==== Map EMR ID ====
for df in [branded_data, rm_data]:
    df['emr id'] = df['particulars'].astype(str).str.strip().str.lower().map(particular_to_code)

branded_data['source'] = 'branded'
rm_data['source'] = 'rm'
combined = pd.concat([branded_data, rm_data], ignore_index=True)

# ==== Merge with Master ====
final = combined.merge(master_df, on='emr id', how='left')
final['sr no'] = range(1, len(final) + 1)

# ==== Select columns for final output ====
final_columns = [
    'vch type', 'vch no.', 'date', 'debit', 'credit', 'sr no', 'emr id',
    'region', 'zone', 'part', 'state', 'ba code', 'territory', 'city',
    'type', 'status', 'kisna/siva', 'party name', 'nsm', 'zone head'
]
final_df = final[[col for col in final_columns if col in final.columns]].copy()

# ==== Load Sale Invoice File & merge to get 'jso order no' ====
sale_df = pd.read_excel(sale_file)
final_df.columns = final_df.columns.str.lower()
sale_df.columns = sale_df.columns.str.lower()

sale_df.rename(columns={
    'doc. date': 'date',
    'doc. no.': 'vch no.',
    'account code': 'emr id',
    'account name': 'party name',
    'sr code': 'ba code',
    'ref. code': 'state'
}, inplace=True)

# Convert 'date' to datetime
final_df['date'] = pd.to_datetime(final_df['date'], errors='coerce')
sale_df['date'] = pd.to_datetime(sale_df['date'], errors='coerce')

# Merge to get jso order no
merged = pd.merge(
    final_df,
    sale_df[['date', 'vch no.', 'emr id', 'party name', 'ba code', 'state', 'jso order no']],
    on=['date', 'vch no.', 'emr id', 'party name', 'ba code', 'state'],
    how='left'
)

# ==== Add Remarks Column based on JSO Order No ====
def get_remarks(jso):
    if pd.isna(jso):
        return None
    jso = str(jso).upper()
    if 'KCO' in jso or 'KCD' in jso:
        return "KCO | Extra Gold IGI"
    elif 'RLS' in jso or 'SNL' in jso:
        return "SNMCC | Line Sale"
    elif 'KSN' in jso or 'RAD' in jso:
        return "Invoice ready"
    elif 'HKJ' in jso:
        return "Retailer ledger Dr. | KIOS"
    return None

merged['remarks'] = merged['jso order no'].apply(get_remarks)

# ==== Load Trade Receivable and compute Outstanding ====
tr_df = pd.read_excel(trade_receivable_file)
tr_df.columns = [col.strip().lower() for col in tr_df.columns]

# Group by particulars (same as party name)
outstanding_df = tr_df.groupby('particulars')[['debit', 'credit']].sum().reset_index()
outstanding_df['particulars'] = outstanding_df['particulars'].astype(str).str.strip().str.lower()
outstanding_df['outstanding'] = outstanding_df['debit'] - outstanding_df['credit']

# Normalize and merge with merged df
merged['party name (match)'] = merged['party name'].astype(str).str.strip().str.lower()
final_merged = pd.merge(
    merged,
    outstanding_df,
    left_on='party name (match)',
    right_on='particulars',
    how='left'
)

# Drop helper columns
final_merged.drop(['party name (match)', 'particulars'], axis=1, inplace=True)

# ==== Save Final Output ====
output_path = r"D:\kisna\work\Final_Merged_With_Outstanding.xlsx"
final_merged.to_excel(output_path, index=False)
print(f"✅ Final output saved to: {output_path}")
