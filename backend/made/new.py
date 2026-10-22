# import streamlit as st
# import pandas as pd
# import io
# from rapidfuzz import fuzz, process

# st.set_page_config(page_title="📊 Final Merged & Summary Excel Generator", layout="wide")
# st.title("📊 Final Merged Excel with Region/Zone/Company/EMR Summary")

# # === File Uploads ===
# st.sidebar.header("📂 Upload Excel Files")
# branded_file = st.sidebar.file_uploader("Upload Branded Apr File", type=["xlsx"])
# rm_file = st.sidebar.file_uploader("Upload RM Job File", type=["xlsx"])
# master_file = st.sidebar.file_uploader("Upload Master Data File", type=["xlsx"])
# sale_file = st.sidebar.file_uploader("Upload Sale Invoice File", type=["xlsx"])
# receivable_file = st.sidebar.file_uploader("Upload Trade Receivable File", type=["xlsx"])

# if all([branded_file, rm_file, master_file, sale_file, receivable_file]):

#     # Step 1: Read Branded & RM Job (header at row 9)
#     branded_all = pd.concat(pd.read_excel(branded_file, sheet_name=None, header=8), ignore_index=True)
#     rm_all = pd.concat(pd.read_excel(rm_file, sheet_name=None, header=8), ignore_index=True)

#     # Cleanup
#     branded_all.columns = [col.strip().lower() for col in branded_all.columns]
#     rm_all.columns = [col.strip().lower() for col in rm_all.columns]

#     # 🔹 Normalize EMR columns
#     if "emr" in branded_all.columns and "emr id" not in branded_all.columns:
#         branded_all.rename(columns={"emr": "emr id"}, inplace=True)
#     if "emr" in rm_all.columns and "emr id" not in rm_all.columns:
#         rm_all.rename(columns={"emr": "emr id"}, inplace=True)

#     # 🔹 Remove "Total" rows
#     branded_all = branded_all[~branded_all['particulars'].astype(str).str.lower().str.contains("total", na=False)]
#     rm_all = rm_all[~rm_all['particulars'].astype(str).str.lower().str.contains("total", na=False)]

#     # 🔹 Branded ke liye JSO Order Number direct use karna hai
#     jso_col = None
#     for col in branded_all.columns:
#         if "jso order number" in col or "jso no" in col:
#             jso_col = col
#             break

#     if not jso_col:
#         st.error("❌ Branded Excel must have a 'JSO Order Number' or 'JSO No' column")
#         st.stop()

#     branded_data = branded_all[['particulars', 'vch type', 'vch no.', 'date',
#                                 'debit', 'credit', 'emr id', jso_col]].copy()
#     branded_data.rename(columns={jso_col: "jso order no"}, inplace=True)

#     rm_data = rm_all[['particulars', 'vch type', 'vch no.', 'date',
#                       'debit', 'credit', 'emr id']].copy()

#     # Read master and tally
#     master_df = pd.read_excel(master_file, sheet_name="Kisna Force Master Details ", header=0)
#     tally_df = pd.read_excel(master_file, sheet_name="Tally Ledger Name", header=0)
#     master_df.columns = master_df.columns.str.lower().str.strip()
#     tally_df.columns = tally_df.columns.str.lower().str.strip()

#     tally_df['company'] = tally_df['company'].astype(str).str.strip().str.lower()
#     tally_df['code'] = tally_df['code'].astype(str).str.strip().str.upper()
#     if 'emr id' in master_df.columns:
#         master_df['emr id'] = master_df['emr id'].astype(str).str.strip().str.upper()

#     # Map EMR if missing (branded & rm)
#     particular_to_code = dict(zip(tally_df['company'], tally_df['code']))
#     for df in [branded_data, rm_data]:
#         df['emr id'] = df['emr id'].fillna(
#             df['particulars'].astype(str).str.strip().str.lower().map(particular_to_code)
#         )
#         df['emr id'] = df['emr id'].astype(str).str.strip().str.upper()

#     # Source tagging
#     branded_data['source'] = 'branded'
#     rm_data['source'] = 'rm'
#     combined = pd.concat([branded_data, rm_data], ignore_index=True)

#     # Merge with master data (attributes)
#     master_cols_keep = ['emr id','region','zone','part','state','ba code','territory','city','type',
#                         'status','kisna/siva','party name','nsm','zone head']
#     final_rows = combined.merge(master_df[master_cols_keep].drop_duplicates('emr id'), on='emr id', how='left')

#     # Sales file (only for RM matching to fetch JSO)
#     sale_df = pd.read_excel(sale_file, header=0)
#     sale_df.columns = sale_df.columns.str.lower()
#     sale_df.rename(columns={
#         'doc. date': 'date',
#         'doc. no.': 'vch no.',
#         'account code': 'emr id',
#         'account name': 'party name',
#         'sr code': 'ba code',
#         'ref. code': 'state'
#     }, inplace=True)
#     if 'emr id' in sale_df.columns:
#         sale_df['emr id'] = sale_df['emr id'].astype(str).str.strip().str.upper()

#     # Dates
#     final_rows['date'] = pd.to_datetime(final_rows['date'], errors='coerce')
#     sale_df['date'] = pd.to_datetime(sale_df['date'], errors='coerce')

#     # Only RM part merge with Sale invoice for JSO
#     rm_only = final_rows[final_rows['source'] == "rm"].merge(
#         sale_df[['date', 'vch no.', 'emr id', 'party name', 'ba code', 'state', 'jso order no']],
#         on=['date', 'vch no.', 'emr id', 'party name', 'ba code', 'state'],
#         how='left',
#         suffixes=('', '_sale')
#     )
#     # Avoid FutureWarning
#     rm_only['jso order no'] = rm_only['jso order no'].combine_first(rm_only['jso order no_sale'])
#     rm_only.drop(columns=['jso order no_sale'], inplace=True)

#     branded_only = final_rows[final_rows['source'] == "branded"]
#     final_rows = pd.concat([branded_only, rm_only], ignore_index=True)

#     # Ensure numeric
#     for col in ['debit', 'credit']:
#         final_rows[col] = pd.to_numeric(final_rows[col], errors='coerce').fillna(0)

#     # Remark logic
#     def get_remark(order_no):
#         if pd.isna(order_no): return ''
#         order_no = str(order_no).upper()
#         if any(x in order_no for x in ['KCO', 'KCD']): return "KCO | Extra Gold & IGI"
#         elif any(x in order_no for x in ['RLS', 'SNL']): return "SNMCC | Line Sale"
#         elif any(x in order_no for x in ['KSN', 'RAD']): return "Invoice ready"
#         elif 'HKJ' in order_no: return "Retailer ledger Dr. | KIOS"
#         return ''

#     final_rows['remark'] = final_rows['jso order no'].apply(get_remark)

#     # Voucher-level aggregate of JSO & Remark (WITHOUT dropping ledger rows)
#     agg_orders = final_rows.groupby('vch no.', as_index=False).agg(
#         **{
#             'jso order no (all)': ('jso order no', lambda x: ', '.join(sorted(set(
#                 str(i).strip() for i in x if pd.notna(i) and str(i).strip()
#             )))),
#             'remark (all)': ('remark', lambda x: ', '.join(sorted(set(r for r in x if r))))
#         }
#     )
#     final_rows = final_rows.merge(agg_orders, on='vch no.', how='left')

#     # 🔹 Priority Column (first)
#     priority_ii_ids = {
#         "MPCCD","MPGJ2","TNPJ","UPAH","UPBPAKS","UPHG","UPHK","UPJP",
#         "UPMHJ","UPPLP","UPPLR","UPUBJH1","UPUDJB","UPUHKJHP","UPURJL",
#         "UPUSDJBW","UPUTRSJ"
#     }
#     final_rows['Priority'] = final_rows['emr id'].apply(
#         lambda x: "II" if str(x).strip().upper() in priority_ii_ids else "I"
#     )

#     # === Receivable processing (EMR-level, no double counting) ===
#     receivable_df = pd.read_excel(receivable_file, header=0)
#     receivable_df.columns = receivable_df.columns.str.lower()

#     def fuzzy_match(name, choices, threshold=85):
#         if pd.isna(name):
#             return None
#         match, score, _ = process.extractOne(name, choices, scorer=fuzz.token_sort_ratio)
#         return match if score >= threshold else None

#     receivable_df['matched_company'] = receivable_df['particulars'].apply(
#         lambda x: fuzzy_match(str(x).lower(), tally_df['company'].unique())
#     )
#     receivable_df = receivable_df.merge(
#         tally_df[['company', 'code']], left_on='matched_company', right_on='company', how='left'
#     )
#     receivable_df['emr id'] = receivable_df['code'].str.upper()
#     receivable_df['credit'] = pd.to_numeric(receivable_df['credit'], errors='coerce').fillna(0)

#     # Ledger totals per EMR
#     emr_ledger = final_rows.groupby('emr id', as_index=False).agg(
#         debit=('debit', 'sum'),
#         credit=('credit', 'sum')
#     )
#     # Receivable per EMR
#     emr_recv = receivable_df.groupby('emr id', as_index=False).agg(
#         receivable_credit=('credit', 'sum')
#     )

#     emr_bal = emr_ledger.merge(emr_recv, on='emr id', how='left').fillna({'receivable_credit': 0})
#     emr_bal['outstanding'] = (emr_bal['debit'] - emr_bal['credit']) - emr_bal['receivable_credit']
#     emr_bal['advance_payment'] = emr_bal['outstanding'].apply(lambda x: abs(x) if x < 0 else 0)
#     emr_bal['outstanding'] = emr_bal['outstanding'].apply(lambda x: x if x > 0 else 0)

#     # Row table me EMR balances dikhane ke liye (optional; summaries independent hain)
#     final_rows = final_rows.merge(
#         emr_bal[['emr id','receivable_credit','outstanding','advance_payment']],
#         on='emr id', how='left'
#     ).fillna({'receivable_credit':0,'outstanding':0,'advance_payment':0})

#     # === Monthly Sheets Logic (row-level ledger, correct totals) ===
#     final_rows['month'] = final_rows['date'].dt.to_period('M').astype(str)
#     monthly_groups = {m: d.drop(columns=['month']) for m, d in final_rows.groupby('month')}

#     # === Summaries (no double counting) ===
#     # unique mapping for EMR -> attributes
#     master_unique = master_df[['emr id','region','zone','party name']].drop_duplicates('emr id')

#     # Ledger-based debit by zone/region/company (row-level)
#     zone_debit = final_rows.groupby('zone', dropna=False)['debit'].sum().reset_index()
#     region_debit = final_rows.groupby('region', dropna=False)['debit'].sum().reset_index()
#     comp_debit = final_rows.groupby('party name', dropna=False)['debit'].sum().reset_index()

#     # EMR balances allocated to zone/region/company using master mapping (EMR-level)
#     emr_bal_attr = emr_bal.merge(master_unique, on='emr id', how='left')

#     zone_bal = emr_bal_attr.groupby('zone', dropna=False)[['receivable_credit','outstanding','advance_payment']].sum().reset_index()
#     region_bal = emr_bal_attr.groupby('region', dropna=False)[['receivable_credit','outstanding','advance_payment']].sum().reset_index()
#     comp_bal = emr_bal_attr.groupby('party name', dropna=False)[['receivable_credit','outstanding','advance_payment']].sum().reset_index()

#     summary_zone = zone_debit.merge(zone_bal, on='zone', how='outer').fillna(0)
#     summary_region = region_debit.merge(region_bal, on='region', how='outer').fillna(0)
#     summary_company = comp_debit.merge(comp_bal, on='party name', how='outer').fillna(0)

#     # EMR summary (straight from EMR-level table)
#     summary_emr = emr_bal[['emr id','debit','receivable_credit','outstanding','advance_payment']].copy()

#     # === Column order: Priority sabse pehle ===
#     first_cols = ['Priority']
#     other_cols = [c for c in final_rows.columns if c not in first_cols]
#     final_rows = final_rows[first_cols + other_cols]

#     # === Streamlit Preview ===
#     st.subheader("✅ Final Preview (Top 50 Rows)")
#     st.dataframe(final_rows.head(50))
#     st.subheader("📍 Zone-wise Summary")
#     st.dataframe(summary_zone)
#     st.subheader("📍 Region-wise Summary")
#     st.dataframe(summary_region)
#     st.subheader("🏢 Company-wise Summary")
#     st.dataframe(summary_company)
#     st.subheader("🆔 EMR ID-wise Summary")
#     st.dataframe(summary_emr)

#     # === Export to Excel ===
#     output = io.BytesIO()
#     with pd.ExcelWriter(output, engine='openpyxl') as writer:
#         final_rows.drop(columns=['month']).to_excel(writer, sheet_name="Final Merged", index=False)
#         summary_zone.to_excel(writer, sheet_name="Zone Summary", index=False)
#         summary_region.to_excel(writer, sheet_name="Region Summary", index=False)
#         summary_company.to_excel(writer, sheet_name="Company Summary", index=False)
#         summary_emr.to_excel(writer, sheet_name="EMR Summary", index=False)
#         for month, df_month in monthly_groups.items():
#             safe_name = month.replace("-", "_")
#             df_month.to_excel(writer, sheet_name=f"{safe_name}", index=False)
#     output.seek(0)

#     st.download_button(
#         label="📅 Download Final Excel with Monthly & Company/EMR Summaries",
#         data=output,
#         file_name="Final_Merged_Monthly_Summary.xlsx",
#         mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
#     )

# else:
#     st.warning("📂 Please upload all 5 required Excel files to proceed.")





#updated code on 5/9/2025





import streamlit as st
import pandas as pd
import io
from rapidfuzz import fuzz, process

st.set_page_config(page_title="📊 Final Merged & Summary Excel Generator", layout="wide")
st.title("📊 Final Merged Excel with Region/Zone/Company/EMR Summary")

# === File Uploads ===
st.sidebar.header("📂 Upload Excel Files")
branded_file = st.sidebar.file_uploader("Upload Branded Apr File", type=["xlsx"])
rm_file = st.sidebar.file_uploader("Upload RM Job File", type=["xlsx"])
master_file = st.sidebar.file_uploader("Upload Master Data File", type=["xlsx"])
sale_file = st.sidebar.file_uploader("Upload Sale Invoice File", type=["xlsx"])
receivable_file = st.sidebar.file_uploader("Upload Trade Receivable File", type=["xlsx"])

if all([branded_file, rm_file, master_file, sale_file, receivable_file]):

    # Step 1: Read Branded & RM Job (header at row 9)
    branded_all = pd.concat(pd.read_excel(branded_file, sheet_name=None, header=8), ignore_index=True)
    rm_all = pd.concat(pd.read_excel(rm_file, sheet_name=None, header=8), ignore_index=True)

    # Cleanup
    branded_all.columns = [col.strip().lower() for col in branded_all.columns]
    rm_all.columns = [col.strip().lower() for col in rm_all.columns]

    # 🔹 Normalize EMR columns
    if "emr" in branded_all.columns and "emr id" not in branded_all.columns:
        branded_all.rename(columns={"emr": "emr id"}, inplace=True)
    if "emr" in rm_all.columns and "emr id" not in rm_all.columns:
        rm_all.rename(columns={"emr": "emr id"}, inplace=True)

    # 🔹 Remove "Total" rows
    branded_all = branded_all[~branded_all['particulars'].astype(str).str.lower().str.contains("total", na=False)]
    rm_all = rm_all[~rm_all['particulars'].astype(str).str.lower().str.contains("total", na=False)]

    # 🔹 Branded ke liye JSO Order Number direct use karna hai
    jso_col = None
    for col in branded_all.columns:
        if "jso order number" in col or "jso no" in col:
            jso_col = col
            break

    if not jso_col:
        st.error("❌ Branded Excel must have a 'JSO Order Number' or 'JSO No' column")
        st.stop()

    branded_data = branded_all[['particulars', 'vch type', 'vch no.', 'date',
                                'debit', 'credit', 'emr id', jso_col]].copy()
    branded_data.rename(columns={jso_col: "jso order no"}, inplace=True)

    rm_data = rm_all[['particulars', 'vch type', 'vch no.', 'date',
                      'debit', 'credit', 'emr id']].copy()

    # Read master and tally
    master_df = pd.read_excel(master_file, sheet_name="Kisna Force Master Details ", header=0)
    tally_df = pd.read_excel(master_file, sheet_name="Tally Ledger Name", header=0)
    master_df.columns = master_df.columns.str.lower().str.strip()
    tally_df.columns = tally_df.columns.str.lower().str.strip()

    tally_df['company'] = tally_df['company'].astype(str).str.strip().str.lower()
    tally_df['code'] = tally_df['code'].astype(str).str.strip().str.upper()
    if 'emr id' in master_df.columns:
        master_df['emr id'] = master_df['emr id'].astype(str).str.strip().str.upper()

    # Map EMR if missing (branded & rm)
    particular_to_code = dict(zip(tally_df['company'], tally_df['code']))
    for df in [branded_data, rm_data]:
        df['emr id'] = df['emr id'].fillna(
            df['particulars'].astype(str).str.strip().str.lower().map(particular_to_code)
        )
        df['emr id'] = df['emr id'].astype(str).str.strip().str.upper()

    # Source tagging
    branded_data['source'] = 'branded'
    rm_data['source'] = 'rm'
    combined = pd.concat([branded_data, rm_data], ignore_index=True)

    # Merge with master data (attributes)
    master_cols_keep = ['emr id','region','zone','part','state','ba code','territory','city','type',
                        'status','kisna/siva','party name','nsm','zone head']
    final_rows = combined.merge(master_df[master_cols_keep].drop_duplicates('emr id'), on='emr id', how='left')

    # Sales file (only for RM matching to fetch JSO)
    sale_df = pd.read_excel(sale_file, header=0)
    sale_df.columns = sale_df.columns.str.lower()
    sale_df.rename(columns={
        'doc. date': 'date',
        'doc. no.': 'vch no.',
        'account code': 'emr id',
        'account name': 'party name',
        'sr code': 'ba code',
        'ref. code': 'state'
    }, inplace=True)
    if 'emr id' in sale_df.columns:
        sale_df['emr id'] = sale_df['emr id'].astype(str).str.strip().str.upper()

    # Dates
    final_rows['date'] = pd.to_datetime(final_rows['date'], errors='coerce')
    sale_df['date'] = pd.to_datetime(sale_df['date'], errors='coerce')

    # Only RM part merge with Sale invoice for JSO
    rm_only = final_rows[final_rows['source'] == "rm"].merge(
        sale_df[['date', 'vch no.', 'emr id', 'party name', 'ba code', 'state', 'jso order no']],
        on=['date', 'vch no.', 'emr id', 'party name', 'ba code', 'state'],
        how='left',
        suffixes=('', '_sale')
    )
    rm_only['jso order no'] = rm_only['jso order no'].combine_first(rm_only['jso order no_sale'])
    rm_only.drop(columns=['jso order no_sale'], inplace=True)

    branded_only = final_rows[final_rows['source'] == "branded"]
    final_rows = pd.concat([branded_only, rm_only], ignore_index=True)

    # Ensure numeric
    for col in ['debit', 'credit']:
        final_rows[col] = pd.to_numeric(final_rows[col], errors='coerce').fillna(0)

    # Remark logic
    def get_remark(order_no):
        if pd.isna(order_no): return ''
        order_no = str(order_no).upper()
        if any(x in order_no for x in ['KCO', 'KCD']): return "KCO | Extra Gold & IGI"
        elif any(x in order_no for x in ['RLS', 'SNL']): return "SNMCC | Line Sale"
        elif any(x in order_no for x in ['KSN', 'RAD']): return "Invoice ready"
        elif 'HKJ' in order_no: return "Retailer ledger Dr. | KIOS"
        return ''

    final_rows['remark'] = final_rows['jso order no'].apply(get_remark)

    # Voucher-level aggregate of JSO & Remark
    agg_orders = final_rows.groupby('vch no.', as_index=False).agg(
        **{
            'jso order no (all)': ('jso order no', lambda x: ', '.join(sorted(set(
                str(i).strip() for i in x if pd.notna(i) and str(i).strip()
            )))),
            'remark (all)': ('remark', lambda x: ', '.join(sorted(set(r for r in x if r))))
        }
    )
    final_rows = final_rows.merge(agg_orders, on='vch no.', how='left')

    # 🔹 Priority Column
    priority_ii_ids = {
        "MPCCD","MPGJ2","TNPJ","UPAH","UPBPAKS","UPHG","UPHK","UPJP",
        "UPMHJ","UPPLP","UPPLR","UPUBJH1","UPUDJB","UPUHKJHP","UPURJL",
        "UPUSDJBW","UPUTRSJ"
    }
    final_rows['Priority'] = final_rows['emr id'].apply(
        lambda x: "II" if str(x).strip().upper() in priority_ii_ids else "I"
    )

    # === Receivable processing ===
    receivable_df = pd.read_excel(receivable_file, header=0)
    receivable_df.columns = receivable_df.columns.str.lower()

    def fuzzy_match(name, choices, threshold=85):
        if pd.isna(name):
            return None
        match, score, _ = process.extractOne(name, choices, scorer=fuzz.token_sort_ratio)
        return match if score >= threshold else None

    receivable_df['matched_company'] = receivable_df['particulars'].apply(
        lambda x: fuzzy_match(str(x).lower(), tally_df['company'].unique())
    )
    receivable_df = receivable_df.merge(
        tally_df[['company', 'code']], left_on='matched_company', right_on='company', how='left'
    )
    receivable_df['emr id'] = receivable_df['code'].str.upper()
    receivable_df['credit'] = pd.to_numeric(receivable_df['credit'], errors='coerce').fillna(0)

    # Ledger totals per EMR
    emr_ledger = final_rows.groupby('emr id', as_index=False).agg(
        debit=('debit', 'sum'),
        credit=('credit', 'sum')
    )
    # Receivable per EMR
    emr_recv = receivable_df.groupby('emr id', as_index=False).agg(
        receivable_credit=('credit', 'sum')
    )

    emr_bal = emr_ledger.merge(emr_recv, on='emr id', how='left').fillna({'receivable_credit': 0})
    emr_bal['outstanding'] = (emr_bal['debit'] - emr_bal['credit']) - emr_bal['receivable_credit']
    emr_bal['advance_payment'] = emr_bal['outstanding'].apply(lambda x: abs(x) if x < 0 else 0)
    emr_bal['outstanding'] = emr_bal['outstanding'].apply(lambda x: x if x > 0 else 0)

    # Merge balances back to rows
    final_rows = final_rows.merge(
        emr_bal[['emr id','receivable_credit','outstanding','advance_payment']],
        on='emr id', how='left'
    ).fillna({'receivable_credit':0,'outstanding':0,'advance_payment':0})

    # === Monthly Sheets (safe, no NaT) ===
    final_rows['month'] = final_rows['date'].dt.to_period('M').astype(str)
    monthly_groups = {
        m: d.drop(columns=['month']) for m, d in final_rows.groupby('month') if m != "NaT"
    }

    # === Summaries ===
    master_unique = master_df[['emr id','region','zone','party name']].drop_duplicates('emr id')

    zone_debit = final_rows.groupby('zone', dropna=False)['debit'].sum().reset_index()
    region_debit = final_rows.groupby('region', dropna=False)['debit'].sum().reset_index()
    comp_debit = final_rows.groupby('party name', dropna=False)['debit'].sum().reset_index()

    emr_bal_attr = emr_bal.merge(master_unique, on='emr id', how='left')

    zone_bal = emr_bal_attr.groupby('zone', dropna=False)[['receivable_credit','outstanding','advance_payment']].sum().reset_index()
    region_bal = emr_bal_attr.groupby('region', dropna=False)[['receivable_credit','outstanding','advance_payment']].sum().reset_index()
    comp_bal = emr_bal_attr.groupby('party name', dropna=False)[['receivable_credit','outstanding','advance_payment']].sum().reset_index()

    summary_zone = zone_debit.merge(zone_bal, on='zone', how='outer').fillna(0)
    summary_region = region_debit.merge(region_bal, on='region', how='outer').fillna(0)
    summary_company = comp_debit.merge(comp_bal, on='party name', how='outer').fillna(0)
    summary_emr = emr_bal[['emr id','debit','receivable_credit','outstanding','advance_payment']].copy()

    # === Column order: Priority sabse pehle ===
    first_cols = ['Priority']
    other_cols = [c for c in final_rows.columns if c not in first_cols]
    final_rows = final_rows[first_cols + other_cols]

    # === Streamlit Preview ===
    st.subheader("✅ Final Preview (Top 50 Rows)")
    st.dataframe(final_rows.head(50))
    st.subheader("📍 Zone-wise Summary")
    st.dataframe(summary_zone)
    st.subheader("📍 Region-wise Summary")
    st.dataframe(summary_region)
    st.subheader("🏢 Company-wise Summary")
    st.dataframe(summary_company)
    st.subheader("🆔 EMR ID-wise Summary")
    st.dataframe(summary_emr)

    # === Export to Excel ===
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        final_rows.drop(columns=['month']).to_excel(writer, sheet_name="Final Merged", index=False)
        summary_zone.to_excel(writer, sheet_name="Zone Summary", index=False)
        summary_region.to_excel(writer, sheet_name="Region Summary", index=False)
        summary_company.to_excel(writer, sheet_name="Company Summary", index=False)
        summary_emr.to_excel(writer, sheet_name="EMR Summary", index=False)
        for month, df_month in monthly_groups.items():
            safe_name = month.replace("-", "_")
            df_month.to_excel(writer, sheet_name=f"{safe_name}", index=False)
    output.seek(0)

    st.download_button(
        label="📅 Download Final Excel with Monthly & Company/EMR Summaries",
        data=output,
        file_name="Final_Merged_Monthly_Summary.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

else:
    st.warning("📂 Please upload all 5 required Excel files to proceed.")
