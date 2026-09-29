import pandas as pd

p = "汽车车罩标签词 - 副本.xlsx"
x = pd.ExcelFile(p)
print(x.sheet_names)
for sheet in x.sheet_names:
    df = pd.read_excel(p, sheet_name=sheet)
    print("SHEET", sheet, df.shape)
    for raw in df.iloc[:180, 1].dropna().astype(str):
        tag = raw.split("\n", 1)[0].strip()
        if tag.startswith("#") and len(tag) <= 30:
            print(len(tag), tag)
