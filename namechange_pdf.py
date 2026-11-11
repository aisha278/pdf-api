"""
Name-change PDF filler (Flask blueprint).

Same pattern as the wills PDF API: Apps Script POSTs JSON, this service fills the
court's own fillable PDF and returns the filled PDF bytes.

POST /fill-form
  {
    "form":   "md_adult_name_change",          # one of FORMS below
    "text":   { "<pdf field name>": "value" },  # text boxes and drop-downs
    "checks": { "<pdf field name>": true }     # check boxes (true = checked)
  }

GET  /forms                 -> list of form keys
GET  /fields/<form>         -> every field: name, type, page, rect, options (for mapping/debugging)

Field names are the PDF's own names. For a few court forms several boxes share ONE
field name (so Acrobat would type the same text in all of them). SPLIT_FIELDS below
turns those into separate boxes named "Name#0", "Name#1", ... in reading order
(top to bottom, then left to right).
"""
import io
import json
import os

from flask import Blueprint, Response, abort, jsonify, request
from pypdf import PdfReader, PdfWriter
from pypdf.generic import (
    ArrayObject, BooleanObject, NameObject, NumberObject, TextStringObject,
)

try:  # optional: exact text widths for shrink-to-fit
    from reportlab.pdfbase.pdfmetrics import stringWidth as _sw
except Exception:  # pragma: no cover
    _sw = None

TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")

FORMS = {
    "md_adult_name_change":    "md_adult_name_change.pdf",     # CC-DR-060
    "md_restoration_of_name":  "md_restoration_of_name.pdf",   # CC-DR-097
    "md_new_marriage_record":  "md_new_marriage_record.pdf",   # CC-FM-072
    "md_petition_to_seal":     "md_petition_to_seal.pdf",      # CC-DC-053
    "dc_name_change":          "dc_name_change.pdf",           # DC Superior Court adult name change packet
    "ss5":                     "ss5.pdf",                      # SSA SS-5
}

# Fields whose several on-page boxes share one name in the court's PDF.
SPLIT_FIELDS = {
    "md_new_marriage_record": ["Name", "Current Name"],
}

namechange_bp = Blueprint("namechange", __name__)


# ---------------------------------------------------------------- helpers
def _api_key_ok():
    want = os.environ.get("API_KEY", "")
    return (not want) or request.headers.get("X-API-Key", "") == want


def _ft(obj):
    cur = obj
    while cur is not None:
        if "/FT" in cur:
            return str(cur["/FT"])
        cur = cur.get("/Parent")
        cur = cur.get_object() if cur is not None else None
    return None


def _flags(obj):
    cur = obj
    while cur is not None:
        if "/Ff" in cur:
            return int(cur["/Ff"])
        cur = cur.get("/Parent")
        cur = cur.get_object() if cur is not None else None
    return 0


def _inherited(obj, key):
    cur = obj
    while cur is not None:
        if key in cur:
            return cur[key]
        cur = cur.get("/Parent")
        cur = cur.get_object() if cur is not None else None
    return None


def _qualified(obj):
    parts, cur = [], obj
    while cur is not None:
        if "/T" in cur:
            parts.append(str(cur["/T"]))
        cur = cur.get("/Parent")
        cur = cur.get_object() if cur is not None else None
    return ".".join(reversed(parts))


def _widgets(writer):
    """Yield (page_index, widget_dict) for every widget annotation."""
    for pi, page in enumerate(writer.pages):
        for a in page.get("/Annots", []) or []:
            a = a.get_object()
            if a.get("/Subtype") == "/Widget":
                yield pi, a


def _drop_xfa(writer):
    af = writer._root_object.get("/AcroForm")
    af = af.get_object() if af is not None else None
    if af is not None and "/XFA" in af:
        del af["/XFA"]


def _split_shared(writer, names):
    """Give each box of a shared-name field its own name (Name#0, Name#1, ...)."""
    af = writer._root_object["/AcroForm"].get_object()
    fields = af["/Fields"].get_object()
    for top_ref in list(fields):
        top = top_ref.get_object()
        if str(top.get("/T")) not in names or "/Kids" not in top:
            continue
        base = str(top["/T"])
        kids = [k for k in top["/Kids"]]
        pos = []
        for k in kids:
            ko = k.get_object()
            r = [float(x) for x in ko["/Rect"]]
            pos.append((-round(r[3]), round(r[0]), k))
        pos.sort(key=lambda t: (t[0], t[1]))
        for i, (_, _, k) in enumerate(pos):
            ko = k.get_object()
            for key in ("/FT", "/DA", "/Ff", "/MaxLen", "/Q"):
                if key not in ko and key in top:
                    ko[NameObject(key)] = top[key]
            ko[NameObject("/T")] = TextStringObject(f"{base}#{i}")
            if "/Parent" in ko:
                del ko["/Parent"]
            fields.append(k)
        fields.remove(top_ref)


def _on_state(widget):
    """The 'checked' appearance name of a check box (anything other than /Off)."""
    ap = widget.get("/AP")
    if ap is not None and "/N" in ap:
        for k in ap["/N"].keys():
            if str(k) != "/Off":
                return NameObject(k)
    return NameObject("/Yes")


def _fit_font(widget, text):
    """Shrink single-line text so it fits the box (keeps court forms legible)."""
    r = [float(x) for x in widget["/Rect"]]
    w, h = r[2] - r[0] - 4, r[3] - r[1]
    da = str(_inherited(widget, "/DA") or "/Helv 0 Tf 0 g")
    font = da.split()[0] if da.split() else "/Helv"
    size = min(11.0, max(6.0, h - 3.0))
    if _sw:
        while size > 6.0 and _sw(text, "Helvetica", size) > w:
            size -= 0.5
    else:
        while size > 6.0 and 0.52 * size * len(text) > w:
            size -= 0.5
    widget[NameObject("/DA")] = TextStringObject(f"{font} {size:g} Tf 0 g")


def _options(widget):
    opts = _inherited(widget, "/Opt") or []
    out = []
    for o in opts:
        o = o.get_object()
        out.append(str(o[1] if isinstance(o, ArrayObject) else o))
    return out


def _match_option(value, opts):
    v = value.strip().lower()
    for o in opts:
        if o.strip().lower() == v:
            return o
    # forgiving: "Prince George's" / "Howard" / "Baltimore City" -> option containing it
    cands = [o for o in opts if o.strip() and v and v in o.lower()]
    cands = [c for c in cands if "locations" not in c.lower()]
    if cands:
        cc = [c for c in cands if c.endswith("(CC)")]
        return (cc or cands)[0]
    return None


# ------------------------------------------------------------------ core
def fill_form(form, text, checks):
    if form not in FORMS:
        raise KeyError(f"Unknown form '{form}'")
    path = os.path.join(TEMPLATE_DIR, FORMS[form])
    writer = PdfWriter(clone_from=PdfReader(path))
    _drop_xfa(writer)
    if form in SPLIT_FIELDS:
        _split_shared(writer, SPLIT_FIELDS[form])

    text = {k: ("" if v is None else str(v)) for k, v in (text or {}).items()}
    checks = {k: bool(v) for k, v in (checks or {}).items()}
    seen_t, seen_c = set(), set()
    warnings = []

    for pi, page in enumerate(writer.pages):
        to_set = {}
        for a in page.get("/Annots", []) or []:
            a = a.get_object()
            if a.get("/Subtype") != "/Widget":
                continue
            q = _qualified(a)
            short = str(a.get("/T")) if a.get("/T") is not None else None
            ft = _ft(a)
            key_t = q if q in text else (short if short in text else None)
            key_c = q if q in checks else (short if short in checks else None)
            if ft == "/Tx" and key_t is not None and text[key_t] != "":
                val = text[key_t]
                seen_t.add(key_t)
                ml = _inherited(a, "/MaxLen")
                if ml is not None and len(val) > int(ml):
                    warnings.append(f"'{key_t}' truncated to {int(ml)} characters")
                    val = val[: int(ml)]
                if _flags(a) & 4096:  # multiline
                    a[NameObject("/DA")] = TextStringObject(
                        str(_inherited(a, "/DA") or "/Helv 0 Tf 0 g").split()[0] + " 10 Tf 0 g")
                else:
                    _fit_font(a, val)
                to_set[q] = val
            elif ft == "/Ch" and key_t is not None and text[key_t] != "":
                seen_t.add(key_t)
                opt = _match_option(text[key_t], _options(a))
                if opt is None:
                    warnings.append(f"'{key_t}': no drop-down option matches '{text[key_t]}'")
                else:
                    a[NameObject("/V")] = TextStringObject(opt)
                    # draw it like a text box so every viewer shows it
                    a[NameObject("/FT")] = NameObject("/Tx")
                    a[NameObject("/Ff")] = NumberObject(0)
                    _fit_font(a, opt)
                    to_set[q] = opt
            elif ft == "/Btn" and key_c is not None:
                seen_c.add(key_c)
                on = _on_state(a)
                if checks[key_c]:
                    a[NameObject("/AS")] = on
                    tgt = a if "/V" in a or "/Parent" not in a else a["/Parent"].get_object()
                    tgt[NameObject("/V")] = on
                else:
                    a[NameObject("/AS")] = NameObject("/Off")
        if to_set:
            writer.update_page_form_field_values(page, to_set, auto_regenerate=False)

    for k in text:
        if k not in seen_t and text[k] != "":
            warnings.append(f"text field not found: {k}")
    for k in checks:
        if k not in seen_c:
            warnings.append(f"check box not found: {k}")

    writer._root_object["/AcroForm"].get_object()[NameObject("/NeedAppearances")] = BooleanObject(True)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue(), warnings


def list_fields(form):
    path = os.path.join(TEMPLATE_DIR, FORMS[form])
    writer = PdfWriter(clone_from=PdfReader(path))
    _drop_xfa(writer)
    if form in SPLIT_FIELDS:
        _split_shared(writer, SPLIT_FIELDS[form])
    out = []
    for pi, a in _widgets(writer):
        r = [round(float(x)) for x in a["/Rect"]]
        item = {"name": _qualified(a), "type": _ft(a), "page": pi + 1, "rect": r}
        if _ft(a) == "/Ch":
            item["options"] = _options(a)
        out.append(item)
    return out


# ---------------------------------------------------------------- routes
@namechange_bp.route("/health")
def health():
    return jsonify(ok=True)


@namechange_bp.route("/forms")
def forms():
    if not _api_key_ok():
        abort(401)
    return jsonify(sorted(FORMS))


@namechange_bp.route("/fields/<form>")
def fields(form):
    if not _api_key_ok():
        abort(401)
    if form not in FORMS:
        abort(404)
    return jsonify(list_fields(form))


@namechange_bp.route("/fill-form", methods=["POST"])
def fill_form_route():
    if not _api_key_ok():
        abort(401)
    data = request.get_json(force=True, silent=True) or {}
    form = data.get("form")
    if form not in FORMS:
        return jsonify(error=f"Unknown form '{form}'", forms=sorted(FORMS)), 400
    pdf, warnings = fill_form(form, data.get("text"), data.get("checks"))
    resp = Response(pdf, mimetype="application/pdf")
    resp.headers["X-Fill-Warnings"] = json.dumps(warnings)[:3000]
    return resp
