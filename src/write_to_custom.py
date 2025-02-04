import os

with open("Noun.name.csv", "r", encoding="euc_jp") as f:
    print(f.read()[:200])
with open("Noun.proper.csv", "r", encoding="euc_jp") as f:
    print(f.read()[:200])
try:
    with open("Noun.custom.csv", "r", encoding="euc_jp") as f:
        print(f.read()[:200])
except:
    pass
for filename in os.listdir():
    # if filename.startswith("Noun"):
    if filename.endswith("csv"):
        with open(filename, "r", encoding="euc_jp") as f:
            for line in f.readlines():
                if "鷗外" in line:
                    print(filename, line)
for filename in os.listdir():
    # if filename.startswith("Noun"):
    if filename.endswith("csv"):
        with open(filename, "r", encoding="euc_jp") as f:
            for line in f.readlines():
                if "適確" in line:
                    print(filename, line)


# Define the filename
filename = "Noun.custom.csv"

# Define the lines to be written
lines = [
    "適確,1285,1285,5000,名詞,一般,*,*,*,*,適確,テキカク,テキカク",
    "鴎外,1291,1291,5000,名詞,固有名詞,人名,名,*,*,鷗外,オウガイ,オウガイ",
    "以って,1287,1287,5000,名詞,副詞可能,*,*,*,*,以って,モッテ,モッテ",
]

# Open the file in write mode with the correct encoding
with open(filename, "w", encoding="euc_jp") as file:
    # Write each line to the file
    for line in lines:
        file.write(line + "\n")

print(f"The lines have been written to {filename}")

if os.path.exists("sys.dic"):
    os.remove("sys.dic")

os.popen("mecab-dict-index -f euc-jp -t utf-8")

print(f"The dictionary has been recompiled")
