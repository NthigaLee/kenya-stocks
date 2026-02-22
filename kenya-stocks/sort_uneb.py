import csv
from pathlib import Path

in_path = Path('UNEB.csv')
out_path = Path('UNEB_sorted.csv')

with in_path.open('r', encoding='utf-8', newline='') as f_in:
    reader = csv.reader(f_in)
    rows = list(reader)

if not rows:
    raise SystemExit('UNEB.csv is empty')

header = rows[0]
# Find indices for Item 1..Item 9
item_indices = [i for i, name in enumerate(header) if name.startswith('Item ')]

with out_path.open('w', encoding='utf-8', newline='') as f_out:
    writer = csv.writer(f_out)
    writer.writerow(header)
    for row in rows[1:]:
        subjects = [row[i] for i in item_indices if row[i]]
        # only SUBJECT-GRADE tokens (have a dash)
        subjects = [s for s in subjects if '-' in s]
        subjects_sorted = sorted(subjects, key=lambda s: s.split('-')[0])
        # pad back to original length
        subjects_sorted += [''] * (len(item_indices) - len(subjects_sorted))
        for idx, subj in zip(item_indices, subjects_sorted):
            row[idx] = subj
        writer.writerow(row)

print('Wrote', out_path)
