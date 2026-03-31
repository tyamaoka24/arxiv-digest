"""Fetch papers from INSPIRE-HEP API for a given author."""

import json
import urllib.parse
import urllib.request


INSPIRE_API = "https://inspirehep.net/api/literature"
FIELDS = "titles,arxiv_eprints,publication_info,earliest_date,authors,dois,texkeys,document_type,inspire_categories"

# Map INSPIRE categories to arXiv-style categories (fallback when arxiv_eprints.categories is empty)
INSPIRE_TO_ARXIV = {
    "Phenomenology-HEP": "hep-ph",
    "Theory-HEP": "hep-th",
    "Experiment-HEP": "hep-ex",
    "Lattice": "hep-lat",
    "Astrophysics": "astro-ph",
    "Gravitation and Cosmology": "gr-qc",
    "Math and Math Physics": "math-ph",
    "General Physics": "physics",
    "Nuclear Physics - Theory": "nucl-th",
    "Nuclear Physics - Experiment": "nucl-ex",
    "Accelerators": "physics.acc-ph",
    "Instrumentation": "physics.ins-det",
    "Quantum Physics": "quant-ph",
}


AUTHORS_API = "https://inspirehep.net/api/authors"
AUTHORS_FIELDS = "name,ids,positions"


def lookup_author(bai):
    """Look up an author by BAI and return their name and affiliation.

    Returns dict with keys: name, bai, affiliation, inspire_id.
    Returns None if not found.
    """
    url = (
        f"{AUTHORS_API}?q=ids.value%3A{urllib.parse.quote(bai)}"
        f"&fields={AUTHORS_FIELDS}"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "arXiv-digest/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    hits = data.get("hits", {}).get("hits", [])
    if not hits:
        return None
    meta = hits[0].get("metadata", {})
    name = meta.get("name", {}).get("value", "")
    ids = meta.get("ids", [])
    inspire_id = ""
    for id_entry in ids:
        if id_entry.get("schema") == "INSPIRE ID":
            inspire_id = id_entry.get("value", "")
    positions = meta.get("positions", [])
    affiliation = ""
    for pos in positions:
        if pos.get("current", False):
            affiliation = pos.get("institution", "")
            break
    if not affiliation and positions:
        affiliation = positions[0].get("institution", "")
    return {"name": name, "bai": bai, "affiliation": affiliation, "inspire_id": inspire_id}


def search_authors(query, max_results=10):
    """Search INSPIRE for authors by name.

    Returns list of dicts with keys: name, bai, affiliation, inspire_id.
    """
    url = (
        f"{AUTHORS_API}?sort=bestmatch"
        f"&size={max_results}"
        f"&q={urllib.parse.quote(query)}"
        f"&fields={AUTHORS_FIELDS}"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "arXiv-digest/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    results = []
    for hit in data.get("hits", {}).get("hits", []):
        meta = hit.get("metadata", {})
        name = meta.get("name", {}).get("value", "")
        ids = meta.get("ids", [])
        bai = ""
        inspire_id = ""
        for id_entry in ids:
            if id_entry.get("schema") == "INSPIRE BAI":
                bai = id_entry.get("value", "")
            elif id_entry.get("schema") == "INSPIRE ID":
                inspire_id = id_entry.get("value", "")
        if not bai:
            continue
        positions = meta.get("positions", [])
        affiliation = ""
        for pos in positions:
            if pos.get("current", False):
                affiliation = pos.get("institution", "")
                break
        if not affiliation and positions:
            affiliation = positions[0].get("institution", "")
        results.append({
            "name": name,
            "bai": bai,
            "affiliation": affiliation,
            "inspire_id": inspire_id,
        })
    return results


def fetch_papers(bai, page_size=250):
    """Fetch all papers for an INSPIRE BAI (e.g. 'K.Y.Oda.1').

    Returns list of paper dicts with keys:
        inspire_id, arxiv_id, title, authors, year, categories, doi
    """
    all_papers = []
    page = 1

    while True:
        url = (
            f"{INSPIRE_API}?sort=mostrecent"
            f"&size={page_size}&page={page}"
            f"&q=find%20a%20{bai}"
            f"&fields={FIELDS}"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "arXiv-digest/1.0"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        hits = data.get("hits", {}).get("hits", [])
        if not hits:
            break

        for hit in hits:
            meta = hit.get("metadata", {})
            paper = _parse_paper(hit["id"], meta)
            if paper:
                all_papers.append(paper)

        total = data.get("hits", {}).get("total", 0)
        if page * page_size >= total:
            break
        page += 1

    return all_papers


def _parse_paper(inspire_id, meta):
    """Parse INSPIRE metadata into a paper dict."""
    titles = meta.get("titles", [])
    title = titles[0].get("title", "") if titles else ""

    arxiv = meta.get("arxiv_eprints", [])
    arxiv_id = arxiv[0].get("value", "") if arxiv else ""
    categories = arxiv[0].get("categories", []) if arxiv else []

    # Fallback: derive categories from inspire_categories when arXiv categories are empty
    if not categories:
        for ic in meta.get("inspire_categories", []):
            mapped = INSPIRE_TO_ARXIV.get(ic.get("term", ""))
            if mapped and mapped not in categories:
                categories.append(mapped)

    date = meta.get("earliest_date", "")
    year = int(date[:4]) if date and len(date) >= 4 else 0

    authors = []
    for a in meta.get("authors", []):
        name = a.get("full_name", "")
        if name:
            authors.append(name)

    dois = meta.get("dois", [])
    doi = dois[0].get("value", "") if dois else ""

    return {
        "inspire_id": str(inspire_id),
        "arxiv_id": arxiv_id,
        "title": title,
        "authors": authors,
        "year": year,
        "categories": categories,
        "doi": doi,
    }


if __name__ == "__main__":
    import sys
    bai = sys.argv[1] if len(sys.argv) > 1 else "K.Y.Oda.1"
    papers = fetch_papers(bai)
    print(f"Fetched {len(papers)} papers for {bai}")
    for p in papers[:5]:
        print(f"  [{p['arxiv_id']}] {p['title'][:80]}")
