"""Auto-update INSPIRE profiles when new papers by registrants are detected."""

from .config import load_config, list_profiles, PROFILES_DIR


def _parse_bai(bai):
    """Extract surname and initials from INSPIRE BAI.

    E.g. "K.Y.Oda.1" → ("Oda", ["K", "Y"])
         "N.Ogawa.3" → ("Ogawa", ["N"])
    """
    parts = bai.split(".")
    # Last part is disambiguator number, second-to-last is surname
    if len(parts) < 3:
        return None, []
    surname = parts[-2]
    initials = [p for p in parts[:-2] if p]
    return surname, initials


def _author_matches(author_name, surname, initials, inspire_name=None):
    """Check if an arXiv author name matches a registered profile author.

    If inspire_name is provided (e.g. "Oda, Kin-ya"), uses full name matching
    to avoid false positives from same-surname-and-initial co-authors.
    Falls back to surname + first initial if inspire_name is not available.

    Author names from arXiv are typically "Firstname Lastname" or "F. Lastname".
    INSPIRE names are typically "Lastname, Firstname".
    """
    author_name = author_name.strip()
    words = author_name.split()
    if not words:
        return False

    # Prefer full-name matching when inspire_name is available
    if inspire_name:
        # Normalize both to "Lastname Firstname" for comparison
        # inspire_name format: "Oda, Kin-ya" → ["Oda", "Kin-ya"]
        inspire_parts = [p.strip() for p in inspire_name.replace(",", " ").split()]
        if not inspire_parts:
            pass  # fall through to initial matching
        else:
            inspire_surname = inspire_parts[0].lower()
            # arXiv format: "Kin-ya Oda" — last word is surname
            if words[-1].lower() != inspire_surname:
                return False
            # If both have more than one word, compare first name initial
            if len(inspire_parts) >= 2 and len(words) >= 2:
                return words[0][0].upper() == inspire_parts[1][0].upper()
            return True

    # Fallback: surname + first initial
    if words[-1].lower() != surname.lower():
        return False
    if initials and words[0]:
        return words[0][0].upper() == initials[0].upper()
    return True


def check_for_profile_updates(papers):
    """Check if any fetched papers are by INSPIRE-registered profile authors.

    Scans all profiles for inspire_bai config, matches against paper authors,
    and regenerates inspire_profile.txt for any matches.

    Returns list of (profile_name, bai) that were updated.
    """
    # Lazy import to avoid circular dependency
    from tools.setup_inspire import regenerate_profile

    # Collect BAI info from all profiles
    profile_bais = []
    for prof_name in list_profiles():
        cfg = load_config(prof_name)
        bai = cfg.get("inspire_bai")
        if bai:
            surname, initials = _parse_bai(bai)
            if surname:
                inspire_name = cfg.get("inspire_name")
                inspire_affiliation = cfg.get("inspire_affiliation")
                profile_bais.append(
                    (prof_name, bai, surname, initials, inspire_name, inspire_affiliation)
                )

    if not profile_bais:
        return []

    # Check each paper's authors against registered profiles
    matched = set()
    for paper in papers:
        for author in paper.get("authors", []):
            for prof_name, bai, surname, initials, inspire_name, _ in profile_bais:
                if prof_name not in matched and _author_matches(
                    author, surname, initials, inspire_name
                ):
                    matched.add(prof_name)

    # Regenerate matched profiles
    updated = []
    for prof_name, bai, _, _, inspire_name, inspire_affiliation in profile_bais:
        if prof_name in matched:
            print(f"  New paper detected for {prof_name} ({bai}), regenerating INSPIRE profile...")
            if regenerate_profile(bai, prof_name, inspire_name, inspire_affiliation):
                updated.append((prof_name, bai))
                print(f"    Updated profiles/{prof_name}/inspire_profile.txt")
            else:
                print(f"    Warning: INSPIRE fetch failed for {bai}")

    return updated
