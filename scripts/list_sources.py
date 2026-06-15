#!/usr/bin/env python3
"""
Outputs all indexed sources with their hub URLs.

Hub URL = the organization or collection page we indexed from,
not the destination URLs of individual entries. For example,
AIMS Collaboratory entries point to LSU/etc., but the hub is aimscollab.org.

Usage: python meta/list-sources.py
"""

import csv
import json
from pathlib import Path

ROOT = Path(__file__).parent.parent
DATA_JSON = ROOT / "docs" / "data.json"
OUT_FILE = ROOT / "meta" / "sources-list.txt"
CSV_FILE = ROOT / "meta" / "sources-list.csv"

# Hub URLs keyed by exact source value as it appears in the corpus (data.json).
# Organized loosely by category for readability.
HUB_URLS = {

    # --- Evidence reviews & research summaries ---
    "What Works Clearinghouse":
        "https://ies.ed.gov/ncee/wwc/",
    "IES Regional Education Labs":
        "https://ies.ed.gov/ncee/rel/",
    "Learning Policy Institute":
        "https://learningpolicyinstitute.org/research/",
    "National Academies of Sciences, Engineering, and Medicine":
        "https://nap.nationalacademies.org/",
    "The Education Trust":
        "https://edtrust.org/research/",
    "Evidence for ESSA":
        "https://evidenceforessa.org/",
    "Brookings Institution":
        "https://www.brookings.edu/",
    "Brookings Institution (Brown Center on Education Policy)":
        "https://www.brookings.edu/",  # same site, narrower editorial scope
    "Campbell Collaboration":
        "https://campbellcollaboration.org/our-work/education/",
    "TNTP":
        "https://tntp.org/publications/",
    "Mathematica":
        "https://mathematica.org/evidence?focusArea=Education&contentType=Publication",
    "WestEd":
        "https://wested.org/resources/?type=research-evaluation",
    "UChicago Consortium on School Research":
        "https://consortium.uchicago.edu/publications",
    "CREDO at Stanford":
        "https://credo.stanford.edu/research-reports/report-finder/",

    # --- Datasets ---
    "AIMS Collaboratory":
        "https://aimscollab.org/",
    "National Center for Education Statistics (NCES)":
        "https://nces.ed.gov/",
    "IEA":
        "https://www.iea.nl/studies",
    "OECD":
        "https://www.oecd.org/pisa/",  # primary entry point; also covers TALIS and PIAAC
    "National Student Clearinghouse":
        "https://nscresearchcenter.org/",
    "Harvard University":
        "https://opportunityinsights.org/",  # Opportunity Insights education data
    "ICPSR (U. Michigan)":
        "https://www.icpsr.umich.edu/",
    "NBER":
        "https://www.nber.org/",
    "Stanford CEPA":
        "https://edopportunity.org/",  # SEDA and related data
    "The Open University":
        "https://analyse.kmi.open.ac.uk/open-dataset",  # OULAD dataset
    "Urban Institute":
        "https://educationdata.urban.org/",
    "World Bank":
        "https://datatopics.worldbank.org/education/",  # EdStats
    "Worcester Polytechnic Institute":
        "https://new.assistments.org/download",  # ASSISTments public dataset
    "U.S. Department of Education":
        "https://ed.gov/data",  # College Scorecard + ESF COVID relief data
    "U.S. Department of Education Office for Civil Rights":
        "https://civilrightsdata.ed.gov/",
    "Riiid":
        "https://github.com/riiid/ednet",  # EdNet dataset
    "Duolingo":
        "https://research.duolingo.com/",  # entries span sharedtask.duolingo.com and Harvard Dataverse
    "Carnegie Mellon University LearnLab":
        "https://pslcdatashop.web.cmu.edu/",

    # --- Journals ---
    "Journal of Educational Data Mining":
        "https://jedm.educationaldatamining.org/",
    "Journal of Learning Analytics":
        "https://learning-analytics.info/index.php/JLA/",

    # --- Frameworks, platforms, and policy ---
    "Collaborative for Academic, Social, and Emotional Learning (CASEL)":
        "https://casel.org/",
    "CAST":
        "https://udlguidelines.cast.org/",
    "UNESCO":
        "https://www.unesco.org/en/digital-education/artificial-intelligence",
    "Tools Competition":
        "https://www.toolscompetition.org/",
    "The Learning Agency":
        "https://www.the-learning-agency.com/",
    "Digital Promise":
        "https://digitalpromise.dspacedirect.org",
    "LEVI Math":
        "https://learning-engineering-virtual-institute.org/",
    "AI-for-Education.org":
        "https://ai-for-education.org/find-benchmarks/",
    "Learning Commons":
        "https://learningcommons.org/",

    # --- Code, benchmarks, and tools ---
    "ADL Initiative":
        "https://github.com/adlnet",  # xAPI tooling (Advanced Distributed Learning)
    "UC Berkeley CAHLR":
        "https://github.com/CAHLR",  # pyBKT + OATutor
    "pyKT Team":
        "https://github.com/pykt-team/pykt-toolkit",
    "University of Notre Dame":
        "https://github.com/nd-ball/py-irt",  # py-irt library
    "ETH Zurich":
        "https://eth-lre.github.io/mathtutorbench/",  # MathTutorBench
    "Scale AI":
        "https://labs.scale.com/leaderboard/tutorbench",  # TutorBench leaderboard
    "Carnegie Mellon University / Educational Testing Service":
        "https://achievethecore.org/page/3367/",  # EMERALDS project (hosted on Achieve the Core)

    "NWEA Research":
        "https://www.nwea.org/research/",
}


def main():
    with open(DATA_JSON, encoding="utf-8") as f:
        data = json.load(f)

    sources = data["meta"]["sources"]

    # Count entries and collect content types per source from the entries array.
    counts = {}
    types = {}
    for entry in data["entries"]:
        src = entry["source"]
        counts[src] = counts.get(src, 0) + 1
        types.setdefault(src, set()).add(entry["type"])

    missing = []
    lines = []
    for source in sorted(sources):
        url = HUB_URLS.get(source, "")
        if not url:
            missing.append(source)
        n = counts.get(source, 0)
        t = ", ".join(sorted(types.get(source, set())))
        lines.append(f"{source} | {url or 'TODO'} | {n} | {t}")

    output = "\n".join(lines)
    print(output)

    OUT_FILE.write_text(output + "\n", encoding="utf-8")

    with CSV_FILE.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Source", "Hub URL", "# Indexed", "Content Types"])
        for source in sorted(sources):
            url = HUB_URLS.get(source, "TODO")
            n = counts.get(source, 0)
            t = ", ".join(sorted(types.get(source, set())))
            writer.writerow([source, url, n, t])

    if missing:
        print(f"\n--- {len(missing)} source(s) without a mapped hub URL ---")
        for s in missing:
            print(f"  {s}")
    else:
        print(f"\n--- All {len(sources)} sources mapped. Written to {OUT_FILE} and {CSV_FILE} ---")


if __name__ == "__main__":
    main()
