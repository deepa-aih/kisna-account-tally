# import streamlit as st
# import pandas as pd
# from io import BytesIO
# from datetime import datetime

# st.set_page_config(page_title="Kisna Merger App", layout="wide")
# st.title("📊 Kisna Master + JSO Order Merger Tool")

# # === Optional: Use default file paths for testing ===
# USE_LOCAL_FILES = False  # Change to True to use paths below for local dev
# default_paths = {
#     "master": r"D:\kisna\work\assets\Master data.xlsx",
#     "branded": r"D:\kisna\work\assets\Branded Apr- 25-Jun -25.xlsx",
#     "rm": r"D:\kisna\work\assets\RM JOb.xlsx",
#     "sales": r"D:\kisna\work\assets\Sale Invoice vs Order Number.xlsx"
# }

# # === Step 1: Upload UI ===
# st.header("Step 1: Upload Excel Files")

# if USE_LOCAL_FILES:
#     master_file = default_paths["master"]
#     branded_file = default_paths["branded"]
#     rm_file = default_paths["rm"]
#     sales_file = default_paths["sales"]
# else:
#     master_file = st.file_uploader("Upload Master Data Excel", type=["xlsx"])
#     branded_file = st.file_uploader("Upload Branded APR Excel", type=["xlsx"])
#     rm_file = st.file_uploader("Upload RM Job Excel", type=["xlsx"])
#     sales_file = st.file_uploader("Upload Sales Invoice vs Order Excel", type=["xlsx"])

# # === Process Button ===
# if st.button("🚀 Process and Download Output"):

#     try:
#         # === Step 2: Read Files ===
#         branded_all = pd.concat(pd.read_excel(branded_file if not USE_LOCAL_FILES else default_paths["branded"], sheet_name=None), ignore_index=True)
#         rm_all = pd.concat(pd.read_excel(rm_file if not USE_LOCAL_FILES else default_paths["rm"], sheet_name=None), ignore_index=True)

#         branded_all.columns = [col.strip().lower() for col in branded_all.columns]
#         rm_all.columns = [col.strip().lower() for col in rm_all.columns]

#         # === Step 3: Filter columns ===
#         branded_data = branded_all[['particulars', 'vch type', 'vch no.', 'date', 'debit', 'credit']].copy()
#         branded_data = branded_data[~branded_data['particulars'].astype(str).str.lower().str.contains("total")]

#         rm_data = rm_all[['particulars', 'vch type', 'vch no.', 'date', 'debit', 'credit']].copy()
#         rm_data = rm_data[~rm_data['particulars'].astype(str).str.lower().str.contains("total")]

#         # === Step 4: Master Data Load ===
#         master_df = pd.read_excel(master_file if not USE_LOCAL_FILES else default_paths["master"], sheet_name="Kisna Force Master Details ")
#         tally_df = pd.read_excel(master_file if not USE_LOCAL_FILES else default_paths["master"], sheet_name="Tally Ledger Name")

#         master_df.columns = [col.strip().lower() for col in master_df.columns]
#         tally_df.columns = [col.strip().lower() for col in tally_df.columns]

#         # Map particulars → emr id (code)
#         tally_df['company'] = tally_df['company'].astype(str).str.strip().str.lower()
#         tally_df['code'] = tally_df['code'].astype(str).str.strip()
#         particular_to_code = dict(zip(tally_df['company'], tally_df['code']))

#         for df in [branded_data, rm_data]:
#             df['emr id'] = df['particulars'].astype(str).str.strip().str.lower().map(particular_to_code)

#         branded_data['source'] = 'branded'
#         rm_data['source'] = 'rm'
#         combined = pd.concat([branded_data, rm_data], ignore_index=True)

#         # === Step 5: Merge with master ===
#         final = combined.merge(master_df, on='emr id', how='left')
#         final['sr no'] = range(1, len(final) + 1)

#         final_columns = [
#             'vch type', 'vch no.', 'date', 'debit', 'credit', 'sr no', 'emr id',
#             'region', 'zone', 'part', 'state', 'ba code', 'territory', 'city',
#             'type', 'status', 'kisna/siva', 'party name', 'nsm', 'zone head'
#         ]
#         final = final[[col for col in final_columns if col in final.columns]]

#         # === Step 6: Sales Merge ===
#         sale_df = pd.read_excel(sales_file if not USE_LOCAL_FILES else default_paths["sales"])
#         final.columns = final.columns.str.lower()
#         sale_df.columns = sale_df.columns.str.lower()

#         sale_df.rename(columns={
#             'doc. date': 'date',
#             'doc. no.': 'vch no.',
#             'account code': 'emr id',
#             'account name': 'party name',
#             'sr code': 'ba code',
#             'ref. code': 'state'
#         }, inplace=True)

#         final['date'] = pd.to_datetime(final['date'], errors='coerce')
#         sale_df['date'] = pd.to_datetime(sale_df['date'], errors='coerce')

#         merged = pd.merge(
#             final,
#             sale_df[['date', 'vch no.', 'emr id', 'party name', 'ba code', 'state', 'jso order no']],
#             on=['date', 'vch no.', 'emr id', 'party name', 'ba code', 'state'],
#             how='left'
#         )

#         # === Step 7: Download Button ===
#         output = BytesIO()
#         merged.to_excel(output, index=False)
#         output.seek(0)

#         st.success("✅ Merging completed successfully!")
#         st.download_button(
#             label="📥 Download Final File",
#             data=output,
#             file_name=f"Final_Merged_With_JSO_Order_No_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
#             mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
#         )

#     except Exception as e:
#         st.error(f"❌ Error occurred: {e}")





import streamlit as st
import pandas as pd
from io import BytesIO

def process_files(master_file, branded_file, rm_file, sale_file):
    # ==== Step 1: Read files ====
    branded_all = pd.concat(pd.read_excel(branded_file, sheet_name=None), ignore_index=True)
    rm_all = pd.concat(pd.read_excel(rm_file, sheet_name=None), ignore_index=True)

    # Normalize column names
    branded_all.columns = [col.strip().lower() for col in branded_all.columns]
    rm_all.columns = [col.strip().lower() for col in rm_all.columns]

    # Remove 'total' rows
    branded_data = branded_all[['particulars', 'vch type', 'vch no.', 'date', 'debit', 'credit']].copy()
    branded_data = branded_data[~branded_data['particulars'].astype(str).str.lower().str.contains("total")]

    rm_data = rm_all[['particulars', 'vch type', 'vch no.', 'date', 'debit', 'credit']].copy()
    rm_data = rm_data[~rm_data['particulars'].astype(str).str.lower().str.contains("total")]

    # ==== Step 2: Master mapping ====
    master_df = pd.read_excel(master_file, sheet_name="Kisna Force Master Details ")
    tally_df = pd.read_excel(master_file, sheet_name="Tally Ledger Name")
    master_df.columns = [col.strip().lower() for col in master_df.columns]
    tally_df.columns = [col.strip().lower() for col in tally_df.columns]

    # Map EMR ID
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

    final_columns = [
        'vch type', 'vch no.', 'date', 'debit', 'credit', 'sr no', 'emr id',
        'region', 'zone', 'part', 'state', 'ba code', 'territory', 'city',
        'type', 'status', 'kisna/siva', 'party name', 'nsm', 'zone head'
    ]
    final = final[[col for col in final_columns if col in final.columns]]

    # ==== Step 3: Sale File Merge ====
    sale_df = pd.read_excel(sale_file)
    final.columns = final.columns.str.lower()
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

    merged = pd.merge(
        final,
        sale_df[['date', 'vch no.', 'emr id', 'party name', 'ba code', 'state', 'jso order no']],
        on=['date', 'vch no.', 'emr id', 'party name', 'ba code', 'state'],
        how='left'
    )

    # ==== Step 4: Remarks Logic ====
    def get_remark(jso):
        if isinstance(jso, str):
            jso = jso.upper()
            if 'KCO' in jso or 'KCD' in jso:
                return "KCO | Extra Gold IGI"
            elif 'RLS' in jso or 'SNL' in jso:
                return "SNMCC | Line Sale"
            elif 'KSN' in jso or 'RAD' in jso:
                return "Invoice ready"
            elif 'HKJ' in jso:
                return "Retailer ledger Dr. | KIOS"
        return ""


    merged['remark'] = merged['jso order no'].apply(get_remark)

    # Export to BytesIO buffer
    output = BytesIO()
    merged.to_excel(output, index=False)
    output.seek(0)
    return output, merged

# ==== Streamlit UI ====
st.title("📊 Kisna - RM & Branded Data Merger")

with st.form("upload_form"):
    st.write("### Upload Required Excel Files")
    master_file = st.file_uploader("Upload Master data Excel", type="xlsx")
    branded_file = st.file_uploader("Upload Branded Apr-25-Jun-25 Excel", type="xlsx")
    rm_file = st.file_uploader("Upload RM Job Excel", type="xlsx")
    sale_file = st.file_uploader("Upload Sale Invoice vs Order Number Excel", type="xlsx")
    submitted = st.form_submit_button("Generate Final File")

if submitted:
    if not (master_file and branded_file and rm_file and sale_file):
        st.error("⚠️ Please upload all 4 files.")
    else:
        with st.spinner("Processing and merging files..."):
            output, preview_df = process_files(master_file, branded_file, rm_file, sale_file)
            st.success("✅ Merged file generated with remarks.")

            st.write("### Preview of Final Merged Data")
            st.dataframe(preview_df.head(50))

            st.download_button(
                label="📥 Download Final Excel File",
                data=output,
                file_name="Final_Merged_With_JSO_Order_No.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )







#app7 is current one latest which gives capital code for emr id



