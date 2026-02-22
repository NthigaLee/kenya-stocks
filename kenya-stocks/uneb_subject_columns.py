import csv
from pathlib import Path

# Input will be the original UNEB.csv; output will have only subject columns
in_path = Path('UNEB.csv')
out_path = Path('UNEB_subject_columns.csv')

with in_path.open('r', encoding='utf-8', newline='') as f_in:
    reader = csv.reader(f_in)
    rows = list(reader)

if not rows:
    raise SystemExit('UNEB.csv is empty')

header = rows[0]
# Find indices for Item 1..Item 9
item_indices = [i for i, name in enumerate(header) if name.startswith('Item ')]

# Build new header: keep Index_No, NAME, then Subject1..Subject9
try:
    idx_index_no = header.index('Index_No')
except ValueError:
    idx_index_no = None
try:
    idx_name = header.index('NAME')
except ValueError:
    idx_name = None

new_header = []
if idx_index_no is not None:
    new_header.append('Index_No')
if idx_name is not None:
    new_header.append('NAME')
new_header += [f'Subject{i+1}' for i in range(len(item_indices))]

with out_path.open('w', encoding='utf-8', newline='') as f_out:
    writer = csv.writer(f_out)
    writer.writerow(new_header)

    for row in rows[1:]:
        subjects = [row[i] for i in item_indices if row[i]]
        # keep only SUBJECT-GRADE tokens (have a dash)
        subjects = [s for s in subjects if '-' in s]
        subjects_sorted = sorted(subjects, key=lambda s: s.split('-')[0])
        # pad to full width
        subjects_sorted += [''] * (len(item_indices) - len(subjects_sorted))

        new_row = []
        if idx_index_no is not None:
            new_row.append(row[idx_index_no])
        if idx_name is not None:
            new_row.append(row[idx_name])
        new_row.extend(subjects_sorted)
        writer.writerow(new_row)

print('Wrote', out_path)
