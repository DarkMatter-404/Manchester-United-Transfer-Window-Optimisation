"""Read United's wages from the saved payroll PDF into united_wages.csv.

The PDF is a browser printout of a public payroll table. Each player line
looks like:  "Mainoo Kobbie Mainoo M 20 GBR £1,300,000"  (short name, full
name, position, age, country, annual salary in pounds).

Only players who were at United on 31 May 2025 and are in the model
(existing players and the fixed arrival) get a wage from this file. Players
on loan at the cutoff are left out, and so are players United signed later.

A player who is missing from the PDF can be given a figure by hand in
united_wages_hand_entered.csv, with its source.

Run from the repository root:
    python src/extract_united_wages.py
"""

import csv
import os
import re
import unicodedata

import pdfplumber

HERE = os.path.dirname(os.path.abspath(__file__))
MANUAL = os.path.join(HERE, "..", "data", "manual")
DOCS = os.path.join(HERE, "..", "docs")

PDF_NAME = "2025-26 Manchester United F.C. Payroll Table.pdf"
SOURCE_URL = "https://www.spotrac.com/epl/manchester-united-fc/payroll/_/year/2025"
SEASON_OF_FIGURE = "2025/26"
VIEWED_ON = "2026-11-16"

# Spelling in the PDF that differs from the roster file
SAME_PLAYER = {"altay bayindir": "altay bayındır", "diego leon": "diego león"}


def plain(text):
    """Lower-case a name and remove accents so the two sources can be matched."""
    text = text.replace("ø", "o").replace("Ø", "O").replace("ı", "i")
    text = unicodedata.normalize("NFKD", text)
    return "".join(c for c in text if not unicodedata.combining(c)).lower().strip()


#########Read the PDF############

# A player line ends with: position, age, three-letter country, salary
line_pattern = re.compile(r"^(.+?)\s+(GK|D|M|F)\s+(\d{2})\s+([A-Z]{3})\s+£([\d,]+)$")

pdf_rows = []          # every player line found, with the table it was in
section = ""
with pdfplumber.open(os.path.join(MANUAL, PDF_NAME)) as pdf:
    for page in pdf.pages:
        for line in (page.extract_text() or "").split("\n"):
            line = line.strip()
            if "Active Roster" in line and "£" not in line:
                section = "active roster"
            elif "Loaned Out" in line:
                section = "loaned out during 2025/26"
            elif "Dead Money" in line and "£" not in line:
                section = "dead money"
            match = line_pattern.match(line)
            if match and section != "dead money":
                # The name part is the short name followed by the full name,
                # for example "de Ligt Matthijs de Ligt"
                pdf_rows.append({"name_part": match.group(1), "section": section,
                                 "annual_wage_gbp": int(match.group(5).replace(",", ""))})

print("Player lines read from the PDF:", len(pdf_rows))

#########Match to the roster file############

with open(os.path.join(DOCS, "roster_reconciliation.csv"), newline="") as file:
    roster = list(csv.DictReader(file))

# Figures entered by hand for players who are not in the PDF
with open(os.path.join(MANUAL, "united_wages_hand_entered.csv"), newline="") as file:
    hand_entered = {row["player_id"]: row for row in csv.DictReader(file)}

def find_in_pdf(roster_name):
    """Return the PDF line whose name part ends with this player's full name."""
    target = plain(roster_name)
    for row in pdf_rows:
        name_part = plain(row["name_part"])
        for pdf_spelling, roster_spelling in SAME_PLAYER.items():
            name_part = name_part.replace(pdf_spelling, plain(roster_spelling))
        if name_part.endswith(target):
            return row
    return None


out = []
used = []
for row in roster:
    # Wages are needed only for players in the model: existing players and the fixed arrival
    if row["model_set"] not in ("E", "K"):
        continue
    found = find_in_pdf(row["name"])
    by_hand = hand_entered.get(row["player_id"])
    note = ""
    if found is None and by_hand is not None:
        # Not in the PDF, but a figure was supplied by hand
        out.append({"player_id": row["player_id"], "name": row["name"], "model_set": row["model_set"],
                    "annual_wage_gbp": int(by_hand["annual_wage_gbp"]),
                    "weekly_wage_gbp": round(int(by_hand["annual_wage_gbp"]) / 52), "gross_or_net": "gross",
                    "season_of_figure": by_hand["season_of_figure"], "source_url": "",
                    "viewed_on": by_hand["viewed_on"], "note": "Entered by hand. " + by_hand["source"]})
        continue
    if found is None:
        annual, weekly = "", ""
        note = "Not in the 2025/26 table; wage still needed"
    else:
        used.append(found["name_part"])
        annual = found["annual_wage_gbp"]
        weekly = round(annual / 52)
        if found["section"] != "active roster":
            note = "Listed as loaned out during 2025/26; at United on 31 May 2025"
        if row["model_set"] == "K":
            note = "Contract began after the cutoff; the move was agreed before it"
    out.append({"player_id": row["player_id"], "name": row["name"], "model_set": row["model_set"],
                "annual_wage_gbp": annual, "weekly_wage_gbp": weekly, "gross_or_net": "gross",
                "season_of_figure": SEASON_OF_FIGURE if found else "",
                "source_url": SOURCE_URL if found else "", "viewed_on": VIEWED_ON if found else "",
                "note": note})

columns = ["player_id", "name", "model_set", "annual_wage_gbp", "weekly_wage_gbp", "gross_or_net",
           "season_of_figure", "source_url", "viewed_on", "note"]
with open(os.path.join(MANUAL, "united_wages.csv"), "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(columns)
    for row in out:
        writer.writerow([row[c] for c in columns])

#########Summary############

known = [row for row in out if row["annual_wage_gbp"] != ""]
missing = [row["name"] for row in out if row["annual_wage_gbp"] == ""]
total = sum(row["annual_wage_gbp"] for row in known if row["model_set"] == "E")
print("Model players with a wage:", len(known), "of", len(out))
print("Still missing:", ", ".join(missing) or "nobody")
print("Annual wages of existing players with a figure (GBP million):", round(total / 1e6, 2))

# PDF players not used: on loan at the cutoff, leaving, or signed after the cutoff
not_used = [row["name_part"].split(" ", 1)[1] for row in pdf_rows if row["name_part"] not in used]
print("In the PDF but not used:", ", ".join(not_used))
