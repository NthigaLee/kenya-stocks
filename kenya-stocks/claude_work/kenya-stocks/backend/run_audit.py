"""Wrapper to run audit and capture output to UTF-8 file."""
import sys
import io

outfile = open("../audit_report.txt", "w", encoding="utf-8")
sys.stdout = outfile

import audit_company_pdfs
audit_company_pdfs.main()

outfile.close()
