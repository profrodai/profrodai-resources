"""Evidence for one phone identifier, and the policy this
exercise applies to it. Teaching code for the class.

THE IDENTIFIER: "55 0100" is a short fictional classroom
identifier, not a usable phone number. For this fixture a
COMPLETE identifier is two digits, one space, four digits.
Nothing here says six digits make a dialable number.

THE POLICY (this exercise, stated here and nowhere else): the
five checks are evidence dimensions, not five mandatory gates.
  - format must pass (a complete identifier in the fixture's
    shape);
  - at least two readers must return the same value
    (corroboration: two tools can make the same mistake, so this
    is not proof that the errors are independent) AND at least
    one of those readers must supply a page region;
  - a supplier record, WHEN ONE EXISTS, may only confirm or
    contradict: a mismatch means investigate, never replace; no
    record is not a failure (a new supplier has none);
  - the role of the line is read from its own label and must not
    be billing; a plain "Tel." line is a supplier line whose
    role is not stated, which this exercise allows for the
    supplier's main contact.
A CANDIDATE extraction is not an ACCEPTED fact. Downstream code
reads only accepted_fact, which carries its provenance.
Jev RECOMMENDS in the class; this code APPLIES the policy. The
inputs are the strings each reader returned, the page regions
the readers reported, and whether the page was readable at all.
Nothing is recomputed here.
ASSERTED TEACHING INPUTS (not observed by this code): the
supplier record equals the value card 21 wrote; the regions come
from the layout trace of the research run; page readability is a
threshold chosen for the class."""
import re, json
FORMAT = re.compile(r"^\d{2} \d{4}$")
RECORD = {"Fresas del Norte": "55 0100"}
RULE = "two digits, optional space, four digits, written as dd dddd"

def normalise(raw):
    """Find two digits, an optional space, four digits; write
    them as 'dd dddd'. Anything else in the raw text is dropped."""
    m = re.search(r"(?<!\d)(\d{2})\s?(\d{4})(?!\d)", raw or "")
    if m:
        return f"{m.group(1)} {m.group(2)}", RULE
    return None, "no match for two digits and four digits"

def role_of(line):
    t = (line or "").lower()
    if re.search(r"billing|facturaci", t): return "billing"
    if re.search(r"ordering|pedidos", t): return "ordering"
    return "supplier line, role not stated"

def corrupt(text):
    """Digits mixed with look-alike letters, like 55 O1OO: the
    text exists but not as a number."""
    m = re.search(r"tel\.?\s*([\w ]+)", text or "", re.I)
    return bool(m and re.search(r"\d", m.group(1))
                and re.search(r"[OolI]", m.group(1)))

def judge(supplier, reads, regions, page_readable=True):
    """reads: {reader: raw phone line or None}
    regions: {reader: {"page": n, "box": [l, t, r, b]}} for the
    readers that reported one
    page_readable: False when the page as a whole could not be
    read (then an absent phone line proves nothing)."""
    raw = dict(reads)
    norm = {t: normalise(x) for t, x in raw.items()}
    full = {t: n[0] for t, n in norm.items() if n[0]}
    out = {"raw": raw,
           "normalised": {t: {"value": n[0], "rule": n[1]}
                          for t, n in norm.items()},
           "candidate": None, "accepted_fact": None}
    if not raw:
        return {**out, "state": "not_yet_processed",
                "action": "run the readers"}
    seen = [t for t, x in raw.items()
            if x and re.search(r"tel", x, re.I)]
    if not seen:
        if not page_readable:
            return {**out, "state": "unreadable", "action": (
                "the page could not be read, so we do not know "
                "whether it has a phone line: ask for a better "
                "source")}
        return {**out, "state": "not_present", "action": (
            "the page was readable and no reader found a phone "
            "line: record the absence and ask Lucy if she "
            "expects one")}
    if not full and any(corrupt(x) for x in raw.values()):
        return {**out, "state": "unreadable", "action": (
            "the text layer is wrong at the digits: read the "
            "rendered page picture too, then ask for a better "
            "source if that fails")}
    if not full:
        return {**out, "state": "unreadable", "action": (
            "ask for a better source: a phone line was seen but "
            "no complete identifier could be read")}
    values = set(full.values())
    out["candidate"] = (sorted(values)[0] if len(values) == 1
                        else sorted(values))
    rec = RECORD.get(supplier)
    roles = {t: role_of(raw[t]) for t in full}
    supporting = sorted(full)
    with_region = [t for t in supporting if t in regions]
    ev = {"format": all(FORMAT.match(v) for v in values),
          "source_region": bool(with_region),
          "corroboration": len(full) >= 2 and len(values) == 1,
          "supplier_record": ("no record" if rec is None
                              else values == {rec}),
          "role_not_billing": all(r != "billing"
                                  for r in roles.values())}
    out["evidence"] = ev
    out["roles_observed"] = roles
    if len(values) > 1:
        return {**out, "state": "conflicting",
                "action": "investigate: readers disagree"}
    if rec is not None and values != {rec}:
        return {**out, "state": "conflicting", "action": (
            "investigate; never replace the record "
            "automatically")}
    need = ("format", "source_region", "corroboration",
            "role_not_billing")
    missing = [k for k in need if not ev[k]]
    if not missing:
        value = sorted(values)[0]
        fact = {"value": value, "readers": supporting,
                "raw": {t: raw[t] for t in supporting},
                "regions": {t: regions[t] for t in with_region},
                "role_observed": sorted(set(roles.values())),
                "uncertainty": [
                    "readers share tools and can make the same "
                    "mistake",
                    "the supplier record is what card 21 wrote, "
                    "a weak check"]}
        return {**out, "state": "accepted", "accepted_fact": fact,
                "action": "remember with provenance"}
    return {**out, "state": "not accepted", "action": (
        "keep as a candidate only; ask for a better source or a "
        "second reader; missing: " + ", ".join(missing)),
        "candidate_evidence": {
            "readers_with_the_whole_value": supporting,
            "readers_with_a_region": with_region}}
