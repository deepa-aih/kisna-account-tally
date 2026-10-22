"""
api.py  -  FastAPI backend for the Excel merger & summary generator.

Expected uploads (strict filename matching - wrong names are rejected):
  branded_file    -> filename must contain "branded"    (case-insensitive)
  rm_file         -> filename must contain "rm"         (case-insensitive)
  master_file     -> filename must contain "master"     (case-insensitive)
  sale_file       -> filename must contain "sale"       (case-insensitive)
  receivable_file -> filename must contain "receivable" (case-insensitive)

Install dependencies:
    pip install fastapi uvicorn python-multipart

Run with:
    uvicorn api:app --reload --port 8000

Interactive docs:
    http://localhost:8000/docs

Endpoint:
    POST /process  ->  multipart/form-data with the five .xlsx files
                   ->  returns Final_Merged_Monthly_Summary.xlsx as download
"""
