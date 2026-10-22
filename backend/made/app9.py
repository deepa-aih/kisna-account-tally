import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="📊 Final Merged & Summary Excel Generator", layout="wide")
st.title("📊 Final Merged Excel with Region/Zone Summary (vch-no based, no double-count)")

# ---------- Helpers ----------
def find_col(df, candidates):
    cols = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in cols:
            return cols[cand.lower()]
    return None

def safe_first(series):
    s = series.dropna()
    return s.iloc[0] if len(s) else None

# ---------- Uploads ----------
st.sidebar.header("📂 Upload Excel Files")
branded_file = st.sidebar.file_uploader("Upload Branded Apr File", type=["xlsx"])
rm_file = st.sidebar.file_uploader("Upload RM Job File", type=["xlsx"])
master_file = st.sidebar.file_uploader("Upload Master Data File", type=["xlsx"])
sale_file = st.sidebar.file_uploader("Upload Sale Invoice File", type=["xlsx"])
receivable_file = st.sidebar.file_uploader("Upload Trade Receivable File", type=["xlsx"])

if not all([branded_file, rm_file, master_file, sale_file, receivable_file]):
    st.warning("📂 Please upload all 5 required Excel files to proceed.")
    st.stop()

# ---------- Read and combine branded + rm (all sheets) ----------
branded_all = pd.concat(pd.read_excel(branded_file, sheet_name=None), ignore_index=True)
rm_all = pd.concat(pd.read_excel(rm_file, sheet_name=None), ignore_index=True)

# strip whitespace in headers
branded_all.columns = [c.strip() for c in branded_all.columns]
rm_all.columns = [c.strip() for c in rm_all.columns]

# detect columns (fallbacks)
part_col = find_col(branded_all, ['particulars', 'particular', 'party name', 'ledger name', 'account name'])
vch_col = find_col(branded_all, ['vch no.', 'vch no', 'voucher no', 'voucherno', 'voucher no.'])
date_col = find_col(branded_all, ['date', 'doc. date', 'doc date', 'voucher date'])
debit_col = find_col(branded_all, ['debit', 'dr', 'debit amount'])
credit_col = find_col(branded_all, ['credit', 'cr', 'credit amount'])
vchtype_col = find_col(branded_all, ['vch type', 'voucher type', 'type'])

if not all([part_col, vch_col, date_col, debit_col, credit_col]):
    st.error("Couldn't detect required columns in Branded/RM files (particulars, vch no., date, debit, credit). Check headers.")
    st.stop()

branded = branded_all[[part_col, vchtype_col, vch_col, date_col, debit_col, credit_col]].copy()
rm = rm_all[[part_col, vchtype_col, vch_col, date_col, debit_col, credit_col]].copy()

branded.columns = ['particulars', 'vch type', 'vch no.', 'date', 'debit', 'credit']
rm.columns = ['particulars', 'vch type', 'vch no.', 'date', 'debit', 'credit']

# drop "Total" rows if present
branded = branded[~branded['particulars'].astype(str).str.lower().str.contains('total', na=False)]
rm = rm[~rm['particulars'].astype(str).str.lower().str.contains('total', na=False)]

# ---------- Master & Tally ----------
xls_master = pd.ExcelFile(master_file)
# find probable sheet names
master_sheet = next((s for s in xls_master.sheet_names if 'kisna' in s.lower() or 'force' in s.lower()), None)
tally_sheet = next((s for s in xls_master.sheet_names if 'tally' in s.lower()), None)
if not master_sheet or not tally_sheet:
    st.error("Couldn't find 'Kisna Force Master Details' or 'Tally Ledger Name' sheet in Master file. Check sheet names.")
    st.stop()

master_df = pd.read_excel(master_file, sheet_name=master_sheet)
tally_df = pd.read_excel(master_file, sheet_name=tally_sheet)
master_df.columns = [c.strip().lower() for c in master_df.columns]
tally_df.columns = [c.strip().lower() for c in tally_df.columns]

if 'company' not in tally_df.columns or 'code' not in tally_df.columns:
    st.error("Tally sheet must have 'Company' and 'Code' columns.")
    st.stop()

# prepare mapping: company(lower) -> code(UPPER)
tally_df['company'] = tally_df['company'].astype(str).str.strip().str.lower()
tally_df['code'] = tally_df['code'].astype(str).str.strip().str.upper()
particular_to_code = dict(zip(tally_df['company'], tally_df['code']))

# ---------- Map particulars -> emr id, combine sources ----------
for df in (branded, rm):
    df['particulars_clean'] = df['particulars'].astype(str).str.strip().str.lower()
    df['emr id'] = df['particulars_clean'].map(particular_to_code).astype(str).str.strip().str.upper()
    df['source'] = 'branded' if df is branded else 'rm'

combined = pd.concat([branded, rm], ignore_index=True)

# normalize vch no. and date & numeric columns
combined['vch no.'] = combined['vch no.'].astype(str).str.strip()
combined['date'] = pd.to_datetime(combined['date'], errors='coerce')
combined['debit'] = pd.to_numeric(combined['debit'], errors='coerce').fillna(0)
combined['credit'] = pd.to_numeric(combined['credit'], errors='coerce').fillna(0)

# Debug totals from combined sheets (this is the "truth" you said)
totals_before = {
    'combined_debit_sum': combined['debit'].sum(),
    'combined_credit_sum': combined['credit'].sum(),
    'combined_row_count': len(combined)
}
st.write("🔎 Totals computed from combined 6 sheets (Branded + RM) — these should be your source-of-truth amounts")
st.write(totals_before)

# ---------- AGGREGATE by (vch no., emr id) — this prevents duplication ----------
agg = combined.groupby(['vch no.', 'emr id'], dropna=False, as_index=False).agg({
    'vch type': lambda x: safe_first(x.dropna().astype(str)),
    'date': lambda x: safe_first(x.dropna()),
    'particulars': lambda x: safe_first(x.dropna().astype(str)),
    'debit': 'sum',
    'credit': 'sum',
    'source': lambda x: ','.join(sorted(set(x.dropna().astype(str))))
})

# sanity check: sums should match totals_before
totals_after_agg = {'agg_debit_sum': agg['debit'].sum(), 'agg_credit_sum': agg['credit'].sum(), 'agg_row_count': len(agg)}
st.write("🔎 Totals after grouping by (vch no., emr id)")
st.write(totals_after_agg)

# ---------- Enrich with master (emr id uppercase) ----------
# normalize master emr id column name
if 'emr id' not in master_df.columns:
    possible = [c for c in master_df.columns if 'emr' in c and 'id' in c]
    if possible:
        master_df.rename(columns={possible[0]: 'emr id'}, inplace=True)
    else:
        st.error("Master sheet doesn't contain 'EMR ID' column.")
        st.stop()
master_df['emr id'] = master_df['emr id'].astype(str).str.strip().str.upper()

final = pd.merge(agg, master_df, on='emr id', how='left', suffixes=('', '_master'))

# ---------- Sale invoice: aggregate JSO order no per vch no. (display only) ----------
sale_df = pd.read_excel(sale_file)
sale_df.columns = [c.strip().lower() for c in sale_df.columns]
# normalize known names if present
rename_map = {}
if 'doc. date' in sale_df.columns: rename_map['doc. date'] = 'date'
if 'doc. no.' in sale_df.columns: rename_map['doc. no.'] = 'vch no.'
if 'account code' in sale_df.columns: rename_map['account code'] = 'emr id'
if 'account name' in sale_df.columns: rename_map['account name'] = 'party name'
if 'sr code' in sale_df.columns: rename_map['sr code'] = 'ba code'
if 'ref. code' in sale_df.columns: rename_map['ref. code'] = 'state'
if rename_map: sale_df.rename(columns=rename_map, inplace=True)

# find jso column
jso_col = find_col(sale_df, ['jso order no', 'jso order no.', 'jso order', 'order no', 'order no.'])
sale_df['jso_temp'] = sale_df[jso_col] if jso_col in sale_df.columns else None
if 'vch no.' in sale_df.columns:
    sale_df['vch no.'] = sale_df['vch no.'].astype(str).str.strip()
    jso_by_vch = sale_df.groupby('vch no.', dropna=False)['jso_temp'].apply(
        lambda x: ', '.join(sorted(set(str(i).strip() for i in x if pd.notna(i) and str(i).strip())))
    ).reset_index().rename(columns={'jso_temp': 'jso order no'})
else:
    jso_by_vch = pd.DataFrame(columns=['vch no.', 'jso order no'])

# attach JSO display data by vch no.
final = pd.merge(final, jso_by_vch, on='vch no.', how='left')

# ---------- Trade Receivable file: map particulars -> tally -> code -> assign receivable_credit ----------
receivable_df = pd.read_excel(receivable_file)
receivable_df.columns = [c.strip().lower() for c in receivable_df.columns]
# ensure particulars col present
if 'particulars' not in receivable_df.columns:
    alt = find_col(receivable_df, ['particulars', 'party name', 'ledger name', 'account name'])
    if alt:
        receivable_df.rename(columns={alt: 'particulars'}, inplace=True)
    else:
        st.error("Receivable file must have a 'particulars' column.")
        st.stop()

receivable_df['particulars'] = receivable_df['particulars'].astype(str).str.strip().str.lower()
receivable_df['credit'] = pd.to_numeric(receivable_df.get('credit', 0), errors='coerce').fillna(0)

# aggregate receivable per particulars (some files have multiple rows)
rec_agg = receivable_df.groupby('particulars', as_index=False)['credit'].sum().rename(columns={'credit': 'receivable_credit_amt'})

# ensure tally mapping exists: company lower -> code upper (already prepared earlier)
# assign receivable_credit to first final row matching the code
final['emr id'] = final['emr id'].astype(str).str.strip().str.upper()
final['receivable_credit'] = 0.0
final['advance_payment'] = 0.0
final['outstanding'] = final['debit'].fillna(0) - final['credit'].fillna(0)

updated_codes = set()
for _, r in rec_agg.iterrows():
    party = r['particulars']  # lower
    amt = r['receivable_credit_amt']
    matched = tally_df[tally_df['company'] == party]
    if not matched.empty:
        code = matched.iloc[0]['code'].strip().upper()
        # find first index in final with this emr id
        idxs = final[final['emr id'] == code].index
        if len(idxs):
            idx = idxs[0]
            if code not in updated_codes:
                final.at[idx, 'receivable_credit'] = amt
                final.at[idx, 'outstanding'] = final.at[idx, 'debit'] - final.at[idx, 'credit'] - amt
                updated_codes.add(code)

# create unmatched advance rows (if receivable party maps to a code not present in final)
all_codes = set(final['emr id'].dropna().unique())
unmatched_rows = []
for _, r in rec_agg.iterrows():
    party = r['particulars']
    amt = r['receivable_credit_amt']
    matched = tally_df[tally_df['company'] == party]
    if not matched.empty:
        code = matched.iloc[0]['code'].strip().upper()
        if code not in all_codes and code not in [d.get('emr id') for d in unmatched_rows]:
            # try to get master data for this code
            master_row = master_df[master_df['emr id'] == code]
            row = {
                'vch type': '',
                'vch no.': '',
                'date': pd.NaT,
                'debit': 0.0,
                'credit': 0.0,
                'emr id': code,
                'receivable_credit': amt,
                'advance_payment': amt,
                'outstanding': 0.0,
                'source': 'Unmatched'
            }
            if not master_row.empty:
                for c in master_row.columns:
                    row[c] = master_row.iloc[0].get(c, '')
            unmatched_rows.append(row)

if unmatched_rows:
    unmatched_df = pd.DataFrame(unmatched_rows)
    # ensure columns align
    for c in unmatched_df.columns:
        if c not in final.columns:
            final[c] = None
    final = pd.concat([final, unmatched_df], ignore_index=True)
else:
    unmatched_df = pd.DataFrame([])

# ---------- Keep amounts only in first row per vch no. ----------
def keep_first_amounts(g):
    g = g.copy()
    if len(g) <= 1:
        return g
    debit0 = float(g.iloc[0].get('debit', 0) or 0)
    credit0 = float(g.iloc[0].get('credit', 0) or 0)
    recv0 = float(g.iloc[0].get('receivable_credit', 0) or 0)
    out0 = float(g.iloc[0].get('outstanding', debit0 - credit0 - recv0))
    g['debit'] = [debit0] + [0.0] * (len(g) - 1)
    if 'credit' in g.columns:
        g['credit'] = [credit0] + [0.0] * (len(g) - 1)
    g['receivable_credit'] = [recv0] + [0.0] * (len(g) - 1)
    g['outstanding'] = [out0] + [0.0] * (len(g) - 1)
    return g

if 'vch no.' in final.columns:
    final = final.groupby('vch no.', sort=False).apply(keep_first_amounts).reset_index(drop=True)

# ---------- Reposition receivable_credit and advance_payment next to credit ----------
cols = list(final.columns)
if 'credit' in cols and 'receivable_credit' in cols:
    cols.remove('receivable_credit')
    insert_pos = cols.index('credit') + 1
    cols.insert(insert_pos, 'receivable_credit')
    if 'advance_payment' in cols:
        cols.remove('advance_payment')
        cols.insert(insert_pos + 1, 'advance_payment')
    final = final[cols]

# optional: drop credit column if you don't want it shown (your earlier script dropped it)
# final.drop(columns=['credit'], inplace=True, errors='ignore')

# ---------- Ensure EMR ID uppercase ----------
final['emr id'] = final['emr id'].astype(str).str.strip().str.upper()

# ---------- Priority & ordering ----------
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

# ---------- Summaries ----------
for c in ['debit', 'receivable_credit', 'outstanding', 'advance_payment']:
    if c not in final.columns:
        final[c] = 0

summary_zone = final.groupby('zone', dropna=False)[['debit', 'receivable_credit', 'outstanding', 'advance_payment']].sum(numeric_only=True).reset_index()
summary_region = final.groupby('region', dropna=False)[['debit', 'receivable_credit', 'outstanding', 'advance_payment']].sum(numeric_only=True).reset_index()

# add totals
if not summary_zone.empty:
    t = summary_zone[['debit', 'receivable_credit', 'outstanding', 'advance_payment']].sum().to_dict()
    t['zone'] = 'Total'
    summary_zone = pd.concat([summary_zone, pd.DataFrame([t])], ignore_index=True)
if not summary_region.empty:
    t = summary_region[['debit', 'receivable_credit', 'outstanding', 'advance_payment']].sum().to_dict()
    t['region'] = 'Total'
    summary_region = pd.concat([summary_region, pd.DataFrame([t])], ignore_index=True)

# ---------- Final debug totals (verify no double count) ----------
final_totals = {'final_debit_sum': final['debit'].sum(), 'final_receivable_credit_sum': final['receivable_credit'].sum()}
st.write("✅ Final totals (after grouping/merge):", final_totals)
st.write("➡ Compare with combined (source) totals shown earlier — they should match the expected amounts from Branded+RM.")

# ---------- Preview & download ----------
st.subheader("✅ Final Preview (Top 100 rows)")
st.dataframe(final.head(100))

st.subheader("📍 Zone-wise Summary")
st.dataframe(summary_zone)

st.subheader("📍 Region-wise Summary")
st.dataframe(summary_region)

output = io.BytesIO()
with pd.ExcelWriter(output, engine='openpyxl') as writer:
    final.to_excel(writer, sheet_name="Final Merged", index=False)
    summary_zone.to_excel(writer, sheet_name="Zone Summary", index=False)
    summary_region.to_excel(writer, sheet_name="Region Summary", index=False)
    if not unmatched_df.empty:
        unmatched_df.to_excel(writer, sheet_name="Unmatched Parties", index=False)
output.seek(0)

st.download_button(
    label="📥 Download Final Excel with Summaries",
    data=output,
    file_name="Final_Merged_Summary.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
