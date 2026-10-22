# import os
# import pandas as pd

# def process_kisna_files(branded_file, rm_file, master_file, sale_file, output_file):
#     # Read branded & rm (all sheets)
#     branded_all = pd.concat(pd.read_excel(branded_file, sheet_name=None), ignore_index=True)
#     rm_all = pd.concat(pd.read_excel(rm_file, sheet_name=None), ignore_index=True)
#     branded_all.columns = [col.strip().lower() for col in branded_all.columns]
#     rm_all.columns = [col.strip().lower() for col in rm_all.columns]

#     # Filter columns
#     branded_data = branded_all[['particulars', 'vch type', 'vch no.', 'date', 'debit', 'credit']].copy()
#     rm_data = rm_all[['particulars', 'vch type', 'vch no.', 'date', 'debit', 'credit']].copy()
#     branded_data = branded_data[~branded_data['particulars'].astype(str).str.lower().str.contains("total")]
#     rm_data = rm_data[~rm_data['particulars'].astype(str).str.lower().str.contains("total")]

#     # Master & Tally
#     master_df = pd.read_excel(master_file, sheet_name="Kisna Force Master Details ")
#     tally_df = pd.read_excel(master_file, sheet_name="Tally Ledger Name")
#     master_df.columns = master_df.columns.str.lower().str.strip()
#     tally_df.columns = tally_df.columns.str.lower().str.strip()
#     tally_df['company'] = tally_df['company'].astype(str).str.strip().str.lower()
#     tally_df['code'] = tally_df['code'].astype(str).str.strip()

#     # Map EMR ID
#     particular_to_code = dict(zip(tally_df['company'], tally_df['code']))
#     for df in [branded_data, rm_data]:
#         df['emr id'] = df['particulars'].astype(str).str.strip().str.lower().map(particular_to_code)
#         df['emr id'] = df['emr id'].str.upper()

#     # Tag source and combine
#     branded_data['source'] = 'branded'
#     rm_data['source'] = 'rm'
#     combined = pd.concat([branded_data, rm_data], ignore_index=True)

#     # Merge with master
#     final = combined.merge(master_df, on='emr id', how='left')
#     final['sr no'] = range(1, len(final) + 1)
#     final = final[['vch type', 'vch no.', 'date', 'debit', 'credit', 'sr no', 'emr id',
#                    'region', 'zone', 'part', 'state', 'ba code', 'territory', 'city',
#                    'type', 'status', 'kisna/siva', 'party name', 'nsm', 'zone head', 'source']]

#     # Sale file processing
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
#     sale_df['date'] = pd.to_datetime(sale_df['date'], errors='coerce')
#     final['date'] = pd.to_datetime(final['date'], errors='coerce')

#     # Merge sale to final
#     merged = pd.merge(
#         final,
#         sale_df[['date', 'vch no.', 'emr id', 'party name', 'ba code', 'state', 'jso order no']],
#         on=['date', 'vch no.', 'emr id', 'party name', 'ba code', 'state'],
#         how='left'
#     )

#     # Define remark generator
#     def get_remark(order_no):
#         if pd.isna(order_no): return ''
#         order_no = str(order_no).upper()
#         if 'KCO' in order_no or 'KCD' in order_no:
#             return "KCO | Extra Gold IGI"
#         elif 'RLS' in order_no or 'SNL' in order_no:
#             return "SNMCC | Line Sale"
#         elif 'KSN' in order_no or 'RAD' in order_no:
#             return "Invoice ready"
#         elif 'HKJ' in order_no:
#             return "Retailer ledger Dr. | KIOS"
#         return ''

#     # Explode JSO Order No and apply remarks
#     exploded = merged.dropna(subset=['jso order no']).copy()
#     exploded['jso order no'] = exploded['jso order no'].astype(str).str.split(',')
#     exploded = exploded.explode('jso order no')
#     exploded['jso order no'] = exploded['jso order no'].str.strip()
#     exploded['remark'] = exploded['jso order no'].apply(get_remark)

#     # Blank repeated voucher data in exploded
#     exploded['row_number'] = exploded.groupby('vch no.').cumcount()
#     for col in ['vch no.', 'debit', 'credit']:
#         exploded.loc[exploded['row_number'] > 0, col] = None
#     exploded.drop(columns=['row_number'], inplace=True)

#     # Save to Excel
#     exploded.to_excel(output_file, index=False)
#     print("✅ File saved:", output_file)


import pandas as pd

def process_kisna_files(branded_file, rm_file, master_file, sale_file):
    # Read branded & rm (all sheets)
    branded_all = pd.concat(pd.read_excel(branded_file, sheet_name=None), ignore_index=True)
    rm_all = pd.concat(pd.read_excel(rm_file, sheet_name=None), ignore_index=True)
    branded_all.columns = [col.strip().lower() for col in branded_all.columns]
    rm_all.columns = [col.strip().lower() for col in rm_all.columns]

    # Filter columns
    branded_data = branded_all[['particulars', 'vch type', 'vch no.', 'date', 'debit', 'credit']].copy()
    rm_data = rm_all[['particulars', 'vch type', 'vch no.', 'date', 'debit', 'credit']].copy()
    branded_data = branded_data[~branded_data['particulars'].astype(str).str.lower().str.contains("total")]
    rm_data = rm_data[~rm_data['particulars'].astype(str).str.lower().str.contains("total")]

    # Master & Tally
    master_df = pd.read_excel(master_file, sheet_name="Kisna Force Master Details ")
    tally_df = pd.read_excel(master_file, sheet_name="Tally Ledger Name")
    master_df.columns = master_df.columns.str.lower().str.strip()
    tally_df.columns = tally_df.columns.str.lower().str.strip()
    tally_df['company'] = tally_df['company'].astype(str).str.strip().str.lower()
    tally_df['code'] = tally_df['code'].astype(str).str.strip()

    # Map EMR ID
    particular_to_code = dict(zip(tally_df['company'], tally_df['code']))
    for df in [branded_data, rm_data]:
        df['emr id'] = df['particulars'].astype(str).str.strip().str.lower().map(particular_to_code)
        df['emr id'] = df['emr id'].str.upper()

    # Tag source and combine
    branded_data['source'] = 'branded'
    rm_data['source'] = 'rm'
    combined = pd.concat([branded_data, rm_data], ignore_index=True)

    # Merge with master
    final = combined.merge(master_df, on='emr id', how='left')
    final['sr no'] = range(1, len(final) + 1)
    final = final[['vch type', 'vch no.', 'date', 'debit', 'credit', 'sr no', 'emr id',
                   'region', 'zone', 'part', 'state', 'ba code', 'territory', 'city',
                   'type', 'status', 'kisna/siva', 'party name', 'nsm', 'zone head', 'source']]

    # Sale file processing
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
    sale_df['date'] = pd.to_datetime(sale_df['date'], errors='coerce')
    final['date'] = pd.to_datetime(final['date'], errors='coerce')

    # Merge sale to final
    merged = pd.merge(
        final,
        sale_df[['date', 'vch no.', 'emr id', 'party name', 'ba code', 'state', 'jso order no']],
        on=['date', 'vch no.', 'emr id', 'party name', 'ba code', 'state'],
        how='left'
    )

    # Define remark generator
    def get_remark(order_no):
        if pd.isna(order_no): return ''
        order_no = str(order_no).upper()
        if 'KCO' in order_no or 'KCD' in order_no:
            return "KCO | Extra Gold IGI"
        elif 'RLS' in order_no or 'SNL' in order_no:
            return "SNMCC | Line Sale"
        elif 'KSN' in order_no or 'RAD' in order_no:
            return "Invoice ready"
        elif 'HKJ' in order_no:
            return "Retailer ledger Dr. | KIOS"
        return ''

    # Explode JSO Order No and apply remarks
    exploded = merged.dropna(subset=['jso order no']).copy()
    exploded['jso order no'] = exploded['jso order no'].astype(str).str.split(',')
    exploded = exploded.explode('jso order no')
    exploded['jso order no'] = exploded['jso order no'].str.strip()
    exploded['remark'] = exploded['jso order no'].apply(get_remark)

    # Blank repeated voucher data in exploded
    exploded['row_number'] = exploded.groupby('vch no.').cumcount()
    for col in ['vch no.', 'debit', 'credit']:
        exploded.loc[exploded['row_number'] > 0, col] = None
    exploded.drop(columns=['row_number'], inplace=True)

    return exploded

# # ===== Example usage =====
# process_kisna_files(
#     branded_file=r"C:\Users\Rushikesh\Downloads\kisna 1\kisna\work\assets\Branded Apr- 25-Jun -25.xlsx",
#     rm_file=r"C:\Users\Rushikesh\Downloads\kisna 1\kisna\work\assets\RM JOb.xlsx",
#     master_file=r"C:\Users\Rushikesh\Downloads\kisna 1\kisna\work\assets\Master data.xlsx",
#     sale_file=r"C:\Users\Rushikesh\Downloads\kisna 1\kisna\work\assets\Sale Invoice vs Order Number.xlsx",
#     output_file="Final_Merged_JSO_Remarks.xlsx"
# )
import pandas as pd

import pandas as pd
import os

import pandas as pd

def process_with_outstanding_sorted(branded_file, rm_file, master_file, sale_file, receivable_file):
    # Read branded & rm (all sheets)
    branded_all = pd.concat(pd.read_excel(branded_file, sheet_name=None), ignore_index=True)
    rm_all = pd.concat(pd.read_excel(rm_file, sheet_name=None), ignore_index=True)
    
    branded_all.columns = [col.strip().lower() for col in branded_all.columns]
    rm_all.columns = [col.strip().lower() for col in rm_all.columns]

    # Filter columns
    branded_data = branded_all[['particulars', 'vch type', 'vch no.', 'date', 'debit', 'credit']].copy()
    rm_data = rm_all[['particulars', 'vch type', 'vch no.', 'date', 'debit', 'credit']].copy()
    branded_data = branded_data[~branded_data['particulars'].astype(str).str.lower().str.contains("total")]
    rm_data = rm_data[~rm_data['particulars'].astype(str).str.lower().str.contains("total")]

    # Master & Tally
    master_df = pd.read_excel(master_file, sheet_name="Kisna Force Master Details ")
    tally_df = pd.read_excel(master_file, sheet_name="Tally Ledger Name")
    master_df.columns = master_df.columns.str.lower().str.strip()
    tally_df.columns = tally_df.columns.str.lower().str.strip()
    tally_df['company'] = tally_df['company'].astype(str).str.strip().str.lower()
    tally_df['code'] = tally_df['code'].astype(str).str.strip()

    # Map EMR ID
    particular_to_code = dict(zip(tally_df['company'], tally_df['code']))
    for df in [branded_data, rm_data]:
        df['emr id'] = df['particulars'].astype(str).str.strip().str.lower().map(particular_to_code)
        df['emr id'] = df['emr id'].str.upper()

    # Tag source and combine
    branded_data['source'] = 'branded'
    rm_data['source'] = 'rm'
    combined = pd.concat([branded_data, rm_data], ignore_index=True)

    # Merge with master
    final = combined.merge(master_df, on='emr id', how='left')
    final['sr no'] = range(1, len(final) + 1)
    final = final[['vch type', 'vch no.', 'date', 'debit', 'credit', 'sr no', 'emr id',
                   'region', 'zone', 'part', 'state', 'ba code', 'territory', 'city',
                   'type', 'status', 'kisna/siva', 'party name', 'nsm', 'zone head', 'source']]

    # Trade Receivable
    receivable_df = pd.read_excel(receivable_file)
    receivable_df.columns = receivable_df.columns.str.lower().str.strip()
    receivable_df['particulars'] = receivable_df['particulars'].astype(str).str.strip().str.lower()

    # Prepare numeric
    final['debit']  = pd.to_numeric(final['debit'],  errors='coerce').fillna(0)
    final['credit'] = pd.to_numeric(final['credit'], errors='coerce').fillna(0)

    # Merge with tally codes
    receivable_df = receivable_df.merge(tally_df[['company', 'code']], left_on='particulars', right_on='company', how='left')
    receivable_df['code'] = receivable_df['code'].astype(str).str.strip().str.upper()

    for c in ['debit', 'credit']:
        if c in receivable_df.columns:
            receivable_df[c] = pd.to_numeric(receivable_df[c], errors='coerce').fillna(0)

    # Aggregate receivable by EMR ID
    recv_agg = receivable_df.groupby('code', dropna=True, as_index=False).agg(
        recv_debit=('debit', 'sum'),
        recv_credit=('credit', 'sum'),
        sample_party=('particulars', 'first')
    )

    # Adjust matched parties
    def pick_base_index(df, code):
        subset = df[(df['emr id'].astype(str).str.upper() == code) & (df['vch no.'].notna())]
        if subset.empty:
            return None
        return int(subset.index[0])

    present_codes = set(final['emr id'].dropna().astype(str).str.upper().unique())

    for _, r in recv_agg.iterrows():
        code = r['code']
        add_debit = float(r['recv_debit'] or 0.0)
        add_credit = float(r['recv_credit'] or 0.0)
        if not code or code.lower() == 'nan':
            continue
        if code in present_codes:
            idx = pick_base_index(final, code)
            if idx is not None:
                cur_d = final.at[idx, 'debit']
                cur_c = final.at[idx, 'credit']
                final.at[idx, 'debit'] = (0.0 if pd.isna(cur_d) else float(cur_d)) + add_debit
                final.at[idx, 'credit'] = (0.0 if pd.isna(cur_c) else float(cur_c)) + add_credit

    # Unmatched parties
    unmatched_rows = []
    for _, r in recv_agg.iterrows():
        code = r['code']
        adv_credit = float(r['recv_credit'] or 0.0)
        party_lower = r['sample_party']
        if not code or code.lower() == 'nan':
            continue
        if code not in present_codes:
            m = master_df[master_df['emr id'].astype(str).str.upper() == code]
            unmatched_rows.append({
                'vch type': '',
                'vch no.': '',
                'date': pd.NaT,
                'debit': 0.0,
                'credit': 0.0,
                'sr no': None,
                'emr id': code,
                'region': m['region'].iloc[0] if not m.empty else '',
                'zone': m['zone'].iloc[0] if not m.empty else '',
                'part': m['part'].iloc[0] if not m.empty else '',
                'state': m['state'].iloc[0] if not m.empty else '',
                'ba code': m['ba code'].iloc[0] if not m.empty else '',
                'territory': m['territory'].iloc[0] if not m.empty else '',
                'city': m['city'].iloc[0] if not m.empty else '',
                'type': m['type'].iloc[0] if not m.empty else '',
                'status': 'Unmatched',
                'kisna/siva': m['kisna/siva'].iloc[0] if not m.empty else '',
                'party name': m['party name'].iloc[0] if not m.empty else (party_lower.title() if isinstance(party_lower, str) else ''),
                'nsm': m['nsm'].iloc[0] if not m.empty else '',
                'zone head': m['zone head'].iloc[0] if not m.empty else '',
                'source': 'Unmatched',
                'advance_payment': adv_credit
            })

    unmatched_df = pd.DataFrame(unmatched_rows)
    if not unmatched_df.empty:
        if 'advance_payment' not in final.columns:
            final['advance_payment'] = 0.0
        final = pd.concat([final, unmatched_df], ignore_index=True)
    else:
        if 'advance_payment' not in final.columns:
            final['advance_payment'] = 0.0

    # Outstanding
    final['debit'] = pd.to_numeric(final['debit'], errors='coerce').fillna(0)
    final['credit'] = pd.to_numeric(final['credit'], errors='coerce').fillna(0)
    final['advance_payment'] = pd.to_numeric(final['advance_payment'], errors='coerce').fillna(0)
    final['outstanding'] = final['debit'] - final['credit']

    # Arrange columns: outstanding after credit, advance_payment after outstanding
    cols = list(final.columns)
    def move_after(col_name, after_name, cols_list):
        if col_name in cols_list and after_name in cols_list:
            cols_list.remove(col_name)
            insert_pos = cols_list.index(after_name) + 1
            cols_list.insert(insert_pos, col_name)
        return cols_list

    cols = move_after('outstanding', 'credit', cols)
    cols = move_after('advance_payment', 'outstanding', cols)
    final = final[cols]

    # Remove JSO & remark if present
    drop_cols = [c for c in ['jso order no', 'remark'] if c in final.columns]
    final = final.drop(columns=drop_cols, errors='ignore')

    # Sort: branded → rm → unmatched
    source_order = {'branded': 1, 'rm': 2, 'Unmatched': 3}
    final['sort_order'] = final['source'].map(source_order).fillna(4)
    final = final.sort_values(['sort_order', 'vch no.', 'date'], na_position='last').drop(columns=['sort_order'])

    return final

# # ===== Example usage =====
# process_with_outstanding_sorted(
#     branded_file=r"C:\Users\Rushikesh\Downloads\kisna 1\kisna\work\assets\Branded Apr- 25-Jun -25.xlsx",
#     rm_file=r"C:\Users\Rushikesh\Downloads\kisna 1\kisna\work\assets\RM JOb.xlsx",
#     master_file=r"C:\Users\Rushikesh\Downloads\kisna 1\kisna\work\assets\Master data.xlsx",
#     sale_file=r"C:\Users\Rushikesh\Downloads\kisna 1\kisna\work\assets\Sale Invoice vs Order Number.xlsx",
#     receivable_file=r"C:\Users\Rushikesh\Downloads\kisna 1\kisna\work\assets\Trade Receivable.xlsx",
#     output_file="Final_Merged_with_Receivable_and_Outstanding.xlsx"
# )
def calculate_region_zone_summary(final_df):
    for col in ['debit', 'credit', 'outstanding', 'advance_payment']:
        if col not in final_df.columns:
            final_df[col] = 0.0
        final_df[col] = pd.to_numeric(final_df[col], errors='coerce').fillna(0)

    region_summary = final_df.groupby('region', dropna=False, as_index=False).agg({
        'debit': 'sum', 'credit': 'sum', 'outstanding': 'sum', 'advance_payment': 'sum'
    })

    zone_summary = final_df.groupby('zone', dropna=False, as_index=False).agg({
        'debit': 'sum', 'credit': 'sum', 'outstanding': 'sum', 'advance_payment': 'sum'
    })

    return region_summary, zone_summary
