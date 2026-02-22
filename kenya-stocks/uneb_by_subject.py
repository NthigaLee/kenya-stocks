import csv
from pathlib import Path

in_path = Path('UNEB.csv')
out_path = Path('UNEB_by_subject.csv')

with in_path.open('r', encoding='utf-8', newline='') as f_in:
    reader = csv.reader(f_in)
    rows = list(reader)

if not rows:
    raise SystemExit('UNEB.csv is empty')

header = rows[0]

# Find indices for Item columns and Final
item_indices = [i for i, name in enumerate(header) if name.startswith('Item ')]
final_idx = header.index('Final') if 'Final' in header else None

# Discover all subject codes from Item columns
subjects = set()
for row in rows[1:]:
    for i in item_indices:
        token = row[i].strip()
        if '-' in token:
            subj, _grade = token.split('-', 1)
            subjects.add(subj)

subject_list = sorted(subjects)

print('Detected subjects:', subject_list)

# Build new header
new_header = []
# Keep Index_No, SEX, NAME if present
for key in ['Index_No', 'SEX', 'NAME']:
    if key in header:
        new_header.append(key)

new_header.extend(subject_list)
if final_idx is not None:
    new_header.append('Final')

with out_path.open('w', encoding='utf-8', newline='') as f_out:
    writer = csv.writer(f_out)
    writer.writerow(new_header)

    for row in rows[1:]:
        # Start with core fields
        new_row = []
        values = {subj: '' for subj in subject_list}

        # Map Item tokens into subject columns
        for i in item_indices:
            token = row[i].strip()
            if '-' in token:
                subj, grade = token.split('-', 1)
                subj = subj.strip()
                grade = grade.strip()
                if subj in values and not values[subj]:
                    # store just the grade; change to token if you prefer subj-grade
                    values[subj] = grade

        for key in ['Index_No', 'SEX', 'NAME']:
            if key in header:
                new_row.append(row[header.index(key)])

        # Subjects in fixed order
        for subj in subject_list:
            new_row.append(values[subj])

        if final_idx is not None:
            new_row.append(row[final_idx])

        writer.writerow(new_row)

print('Wrote', out_path)
