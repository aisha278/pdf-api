from flask import Flask, request, send_file, jsonify
from pypdf import PdfReader, PdfWriter
from io import BytesIO
import tempfile
import os
from datetime import datetime

app = Flask(__name__)

# --- FILES ---
TEMPLATE_PDF_GUARDIAN = "ccgn041prefilled.pdf"
TEMPLATE_PDF_INVOICE  = "2026AMohammedAAPInvoicetemplate.pdf"
TEMPLATE_PDF_TOD      = "ROD39REVOCABLETRANSFERONDEATHDEED-FORM_editable.pdf"
TEMPLATE_PDF_PP_DC = "DCcustody_parenting_plan_fillable.pdf"
TEMPLATE_PDF_PP_MD = "ccdr109md parenting plan_fillable.pdf"   # <-- has spaces, verify against your repo listing


# =========================================================
# 1. STANDBY GUARDIAN PDF
# =========================================================
@app.route("/fill-standby-guardian", methods=["POST"])
def fill_standby_guardian():
    try:
        data = request.json or {}

        field_data = {
            "Client Names 1":                      data.get("parent_names", ""),
            "Street Address 1":                   data.get("parent_address", ""),
            "City, State, Zip 1":                 data.get("parent_city_state_zip", ""),
            "Street Address 2":                   data.get("parent2_address", ""),
            "City, State, Zip 2":                 data.get("parent2_city_state_zip", ""),
            "Name of Standby Guardian 1":          data.get("standby_guardian_name", ""),
            "primary guardian address":           data.get("standby_guardian_address", ""),
            "primary guardian Telephone Number":  data.get("standby_guardian_phone", ""),
            "primary guardian  E-mail":           data.get("standby_guardian_email", ""),
            "Name of Alternate guardian 1":        data.get("alternate_guardian_name", ""),
            "Alternate guardian Address":         data.get("alternate_guardian_address", ""),
            "Telephone Number 2":                 data.get("alternate_guardian_phone", ""),
            "Alternate guardian Email":           data.get("alternate_guardian_email", ""),
            "Name of Children 1":                 data.get("child1_name", ""),
            "Date of Birth 1":                    data.get("child1_dob", ""),
            "Name of Children 2":                 data.get("child2_name", ""),
            "Date of Birth 2":                    data.get("child2_dob", ""),
            "Name of Children 3":                 data.get("child3_name", ""),
            "Date of Birth 3":                    data.get("child3_dob", ""),
            "Name of Children 4":                 data.get("child4_name", ""),
            "Date of Birth 4":                    data.get("child4_dob", ""),
            "Name of Person with Parental rights":   data.get("other_parent_name", "NONE"),
            "Relationship to Minor  Child":          data.get("other_parent_relationship", "N/A"),
            "Name of Person with Parental Rights 2": data.get("other_parent_name_2", ""),
            "Relationship to Minor child 2":         data.get("other_parent_relationship_2", ""),
            "Box 3":                              data.get("guardian_person_limits", "NONE"),
            "Box 4":                              data.get("guardian_property_limits", "NONE"),
            "Location 1":                         data.get("child_property_location", "____"),
        }
          

        reader = PdfReader(TEMPLATE_PDF_GUARDIAN)
        writer = PdfWriter()

        writer.clone_reader_document_root(reader)
        writer.set_need_appearances_writer(True)

        for page in writer.pages:
            writer.update_page_form_field_values(page, field_data)

        checkbox_values = {
            "Check Box94":  "/Yes",
            "Check Box97":  "/Yes",
            "Check Box114": "/Yes",
            "Check Box115": "/Yes",
            "Check Box116": "/Yes",
            "Check Box117": "/Yes",
            "Check Box118": "/Yes",
            "Check Box119": "/Yes",
            "Check Box120": "/Yes",
            "Check Box121": "/Yes",
            "Check Box122": "/Yes",
            "Check Box123": "/Yes",
            "Check Box124": "/Yes",
        }

        for page in writer.pages:
            writer.update_page_form_field_values(page, checkbox_values)

        output = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        output.close()

        with open(output.name, "wb") as f:
            writer.write(f)

        filename = "filled_standby_guardian_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".pdf"

        return send_file(
            output.name,
            as_attachment=True,
            download_name=filename,
            mimetype="application/pdf"
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =========================================================
# 2. APPOINTED ATTORNEY INVOICE PDF
# =========================================================
@app.route("/fill-appointed-attorney-invoice", methods=["POST"])
def fill_appointed_attorney_invoice():
    try:
        data = request.json or {}

        assignment_date = data.get("assignment_date", "")
        start_time      = data.get("start_time", "")
        end_time        = data.get("end_time", "")
        hours           = str(data.get("hours", ""))
        total           = str(data.get("total", ""))

        formatted_date  = format_assignment_date(assignment_date)
        invoice_number  = "ATT" + format_invoice_date_for_number(assignment_date) + "AM"

        field_data = {
            "Invoice Number":                 invoice_number,
            "Invoice Date":                   formatted_date,
            "Assignment Date":                formatted_date,
            "Assignment Start Time":          start_time,
            "Assignment End Time":            end_time,
            "Enter the Hours for Compensation": hours,
            "Total Rate of Compensation":     total,
            "Total Reimbursement":            total,
            "Commissioner Location":          "Anne Arundel",
        }

        reader = PdfReader(TEMPLATE_PDF_INVOICE)
        writer = PdfWriter()

        writer.clone_reader_document_root(reader)
        writer.set_need_appearances_writer(True)

        for page in writer.pages:
            writer.update_page_form_field_values(page, field_data)

        output = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        output.close()

        with open(output.name, "wb") as f:
            writer.write(f)

        safe_date = assignment_date.replace(",", "").replace(" ", "_")
        filename = f"AAP_Invoice_{safe_date}_{datetime.now().strftime('%H%M%S')}.pdf"

        return send_file(
            output.name,
            as_attachment=True,
            download_name=filename,
            mimetype="application/pdf"
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# =========================================================
# 3. DC REVOCABLE TRANSFER ON DEATH DEED PDF
# =========================================================
@app.route("/fill-tod-deed", methods=["POST"])
def fill_tod_deed():
    try:
        data = request.get_json()

        reader = PdfReader(TEMPLATE_PDF_TOD)
        writer = PdfWriter()

        writer.clone_reader_document_root(reader)
        writer.set_need_appearances_writer(True)

        field_values = {
            "Printed name":                   data.get("owner1_name", ""),
            "Printed name_2":                 data.get("owner2_name", ""),
            "Mailing address":                data.get("owner1_address", ""),
            "Mailing address_2":              data.get("owner2_address", ""),
            "Legal Description":              data.get("legal_description", ""),
            "Trust name":                     data.get("primary_beneficiary_name", ""),
            "Mailing address if available":   data.get("primary_beneficiary_address", ""),
            "Alt Beneficiary  name":          data.get("alt_beneficiary_name", ""),
            "Mailing address if available_2": data.get("alt_beneficiary_address", ""),
        }

        for page in writer.pages:
            writer.update_page_form_field_values(page, field_values)

        output = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        output.close()

        with open(output.name, "wb") as f:
            writer.write(f)

        filename = "DC_TOD_Deed_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".pdf"

        return send_file(
            output.name,
            as_attachment=True,
            download_name=filename,
            mimetype="application/pdf"
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


===========================================================================
Add this whole block anywhere in app.py (e.g. right after the
fill_tod_deed() route, before "# HELPERS"). It's self-contained.
===========================================================================
 
import re
 
# ---------------------------------------------------------------------
# PARENTING PLAN — shared helpers
# ---------------------------------------------------------------------
 
def _pp_str(v):
    return "" if v is None else str(v).strip()
 
 
def _pp_parse_children(raw_text):
    """Best-effort split of the free-text children answer into
    [{"name": ..., "dob": ...}, ...]."""
    if not raw_text:
        return []
    date_pat = re.compile(r"\b(\d{1,2}/\d{1,2}/\d{2,4})\b")
    chunks = [c.strip() for c in re.split(r"[\n;]+", raw_text) if c.strip()]
    out = []
    for chunk in chunks:
        m = date_pat.search(chunk)
        dob = m.group(1) if m else ""
        name = date_pat.sub("", chunk)
        name = re.sub(r"[,\-–]\s*(born on)?\s*$", "", name, flags=re.IGNORECASE).strip(" ,-–")
        if name:
            out.append({"name": name, "dob": dob})
    return out
 
 
def _pp_split_address(addr):
    addr = _pp_str(addr)
    if "," in addr:
        street, rest = addr.rsplit(",", 1)
        return street.strip(), rest.strip()
    return addr, ""
 
 
def _pp_determine_mother_father_cols(p):
    client_g = _pp_str(p.get("client_gender")).lower()
    spouse_g = _pp_str(p.get("spouse_gender")).lower()
    if client_g == "female" or spouse_g == "male":
        return "parent1", "parent2"
    if client_g == "male" or spouse_g == "female":
        return "parent2", "parent1"
    return "parent1", "parent2"  # unresolved — defaults client -> Mother; verify manually
 
 
# DC legal custody grid: row -> {both, plaintiff, defendant} checkbox names.
# These checkboxes are unlabeled in the PDF ("Check Box37" etc.) — mapped by
# reading each box's page/x/y position against the visible form layout.
_DC_LEGAL_CUSTODY_ROWS = {
    "diet":                    {"both": "Check Box3",  "plaintiff": "Check Box15", "defendant": "Check Box27"},
    "religion":                {"both": "Check Box4",  "plaintiff": "Check Box16", "defendant": "Check Box28"},
    "medical_care":            {"both": "Check Box5",  "plaintiff": "Check Box17", "defendant": "Check Box29"},
    "mental_health_care":      {"both": "Check Box6",  "plaintiff": "Check Box18", "defendant": "Check Box30"},
    "discipline":              {"both": "Check Box7",  "plaintiff": "Check Box19", "defendant": "Check Box31"},
    "choice_of_school":        {"both": "Check Box8",  "plaintiff": "Check Box20", "defendant": "Check Box32"},
    "choice_of_study":         {"both": "Check Box9",  "plaintiff": "Check Box21", "defendant": "Check Box33"},
    "school_activities":       {"both": "Check Box10", "plaintiff": "Check Box22", "defendant": "Check Box34"},
    "extracurricular_activities": {"both": "Check Box11", "plaintiff": "Check Box23", "defendant": "Check Box35"},
    "custom_row_1":            {"both": "Check Box12", "plaintiff": "Check Box24", "defendant": "Check Box36"},
    "custom_row_2":            {"both": "Check Box13", "plaintiff": "Check Box25", "defendant": "Check Box37"},
    "custom_row_3":            {"both": "Check Box14", "plaintiff": "Check Box26", "defendant": "Check Box38"},
}
 
_DC_SCHEDULE_FREQUENCY = {
    "every week": "Check Box39", "every two weeks": "Check Box40", "other": "Check Box41",
}
_DC_CHILD_SUPPORT_PAYER = {"plaintiff": "Check Box61", "defendant": "Check Box62"}
_DC_CHILD_SUPPORT_FREQUENCY = {
    "every week": "Check Box63", "every two weeks": "Check Box65",
    "once a month": "Check Box64", "other": "Check Box66",
}
_DC_TAX_DEDUCTION_PLAINTIFF = {"year a": "Check Box67", "year b": "Check Box68", "every year": "Check Box69"}
_DC_TAX_DEDUCTION_DEFENDANT = {"year a": "Check Box70", "year b": "Check Box71", "every year": "Check Box72"}
_DC_COLLEGE = {
    "plaintiff pays all": "Check Box73", "defendant pays all": "Check Box74",
    "share": "Check Box75", "other": "Check Box76",
}
_DC_HOLIDAY_FIELD_MAP = {
    "martin luther king day": "Martin Luther King Day", "president's day": "Presidents Day",
    "memorial day": "Memorial Day", "fourth of july": "4 th of July", "labor day": "Labor Day",
    "thanksgiving": "Thanksgiving", "christmas": "Christmas Day",
    "child's birthday": "Childs Birthday", "mother's day": "Mothers Day", "father's day": "Fathers Day",
}
_MD_HOLIDAY_FIELD_MAP = {
    "martin luther king day": "Martin Luther King Day", "memorial day": "Memorial Day",
    "fourth of july": "Fourth of July", "labor day": "Labor Day", "thanksgiving": "Thanksgiving",
    "child's birthday": "Child(ren)'s Birthdays", "mother's day": "Mother's Day", "father's day": "Father's Day",
}
 
 
def _pp_build_dc_fields(p):
    text = {}
    boxes = {}
 
    text["PRINT PLAINTIFFS NAME"] = p.get("parent1_name")
    street1, csz1 = _pp_split_address(p.get("parent1_address"))
    text["STREET ADDRESS"] = street1
    text["CITY STATE AND ZIP CODE"] = csz1
 
    text["PRINT DEFENDANTS NAME"] = p.get("parent2_name")
    street2, csz2 = _pp_split_address(p.get("parent2_address"))
    text["STREET ADDRESS_2"] = street2
    text["CITY STATE AND ZIP CODE_2"] = csz2
 
    kids = _pp_parse_children(p.get("children_raw"))
    physical_custody_home = p.get("physical_custody_home", "")
    for i, kid in enumerate(kids[:7], start=1):
        text[f"Childs NameRow{i}"] = kid["name"]
        age = ""
        if kid["dob"]:
            try:
                dob = datetime.strptime(kid["dob"], "%m/%d/%Y")
                today = datetime.today()
                age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            except ValueError:
                age = ""
        text[f"AgeRow{i}"] = age
        text[f"Where does this child liveRow{i}"] = physical_custody_home
 
    lc = p.get("legal_custody_final_say", {})
    for category, choice in lc.items():
        row = _DC_LEGAL_CUSTODY_ROWS.get(category)
        if not row:
            continue
        choice = _pp_str(choice).lower()
        if "both" in choice:
            boxes[row["both"]] = True
        elif "spouse" in choice or "defendant" in choice:
            boxes[row["defendant"]] = True
        elif choice == "me" or "plaintiff" in choice:
            boxes[row["plaintiff"]] = True
 
    text["If you cannot agree which of you will make the final decision"] = p.get("legal_custody_tiebreaker", "")
    text["The childrens residence is with"] = physical_custody_home
 
    schedule = p.get("regular_schedule", {})
    day_field = {
        "sunday": "SundayRow1", "monday": "MondayRow1", "tuesday": "TuesdayRow1",
        "wednesday": "WednesdayRow1", "thursday": "ThursdayRow1",
        "friday": "FridayRow1", "saturday": "SaturdayRow1",
    }
    for day, field in day_field.items():
        text[field] = schedule.get(day, "")
 
    freq = _pp_str(p.get("schedule_frequency")).lower()
    if freq in _DC_SCHEDULE_FREQUENCY:
        boxes[_DC_SCHEDULE_FREQUENCY[freq]] = True
    elif freq:
        boxes[_DC_SCHEDULE_FREQUENCY["other"]] = True
        text["other"] = p.get("schedule_frequency_detail", p.get("schedule_frequency"))
 
    text["If not weekly which of you has the children the rest of the time"] = p.get("schedule_rest_of_time", "")
    text["Where"] = p.get("dropoff_location", "")
    text["When time and day"] = p.get("dropoff_time", "")
    text["Where_2"] = p.get("pickup_location", "")
    text["When time and day_2"] = p.get("pickup_time", "")
    text["If one of you doesnt show up how long will the other wait"] = p.get("no_show_wait", "")
    text["If there are extraordinary costs taxi train plane etc who will pay for which costs 1"] = p.get("extraordinary_costs", "")
 
    holidays = p.get("holidays", {})
    for key, choice in holidays.items():
        base = _DC_HOLIDAY_FIELD_MAP.get(key.lower())
        if not base:
            continue
        choice = _pp_str(choice)
        who, _, when = choice.partition(" — ")
        who_name = p.get("parent1_name") if who.lower().startswith("me") else p.get("parent2_name")
        if "every year" in when.lower():
            text[f"Every Year{base}"] = who_name
        else:
            text[f"Year A{base}"] = who_name
 
    text["Text42"] = p.get("summer_vacation_detail", "")
 
    payer = _pp_str(p.get("child_support_payer")).lower()
    if payer in ("plaintiff", "me"):
        boxes[_DC_CHILD_SUPPORT_PAYER["plaintiff"]] = True
    elif payer in ("defendant", "spouse", "my spouse"):
        boxes[_DC_CHILD_SUPPORT_PAYER["defendant"]] = True
    freq2 = _pp_str(p.get("child_support_frequency")).lower()
    if freq2 in _DC_CHILD_SUPPORT_FREQUENCY:
        boxes[_DC_CHILD_SUPPORT_FREQUENCY[freq2]] = True
    text["undefined_7"] = p.get("child_support_amount", "")
 
    expense_field_map = {
        "health insurance premium": "Health Insurance Coverage",
        "medical co-pays": "Medical Care including copays",
        "dental": "Dental braces fillings etc",
        "vision": "Vision eyeglasses contacts etc",
        "mental health care": "Mental Health Care",
        "education (tuition, books, fees)": "Education tuition books fees etc",
        "childcare (work-related)": "Childcare workrelated",
        "uncovered medical": "Other Health Care",
    }
    mother_col, father_col = _pp_determine_mother_father_cols(p)
    expenses = p.get("expenses_split", {})
    for key, choice in expenses.items():
        base = expense_field_map.get(key.lower())
        if not base:
            continue
        choice = _pp_str(choice).lower()
        mother_val = father_val = ""
        if "i pay 100" in choice:
            (mother_val, father_val) = ("100%", "0%") if mother_col == "parent1" else ("0%", "100%")
        elif "spouse pays 100" in choice:
            (mother_val, father_val) = ("0%", "100%") if mother_col == "parent1" else ("100%", "0%")
        elif "50/50" in choice:
            mother_val = father_val = "50%"
        elif "other" in choice:
            mother_val = father_val = p.get("expenses_other_pct_detail", "")
        text[f"Mother amount or {base}"] = mother_val
        text[f"Father  amount or {base}"] = father_val  # real field name has two spaces after "Father"
 
    dependent_claim = _pp_str(p.get("tax_dependent_claim")).lower()
    if "alternat" in dependent_claim:
        text["Other"] = "Alternating years"
    elif dependent_claim == "me, every year":
        boxes[_DC_TAX_DEDUCTION_PLAINTIFF["every year"]] = True
    elif dependent_claim == "spouse, every year":
        boxes[_DC_TAX_DEDUCTION_DEFENDANT["every year"]] = True
    else:
        text["Other"] = p.get("tax_dependent_claim", "")
 
    college = _pp_str(p.get("college_expenses")).lower()
    if "one parent pays all" in college:
        boxes[_DC_COLLEGE["plaintiff pays all"]] = True
    elif "split by percentage" in college:
        boxes[_DC_COLLEGE["share"]] = True
        text["Plaintiff will pay"] = p.get("college_pct_detail", "")
    else:
        boxes[_DC_COLLEGE["other"]] = True
        text["these must add up to 100"] = p.get("college_expenses", "")
 
    return text, boxes
 
 
def _pp_build_md_fields(p):
    text = {}
    boxes = {}
 
    boxes["Joint parenting plan of"] = True
    text["Name of Party 1"] = p.get("parent1_name")
    text["Party 1 Relationship to Child(ren)"] = "Parent"
    text["Name of Party 2"] = p.get("parent2_name")
    text["Party 2 Relationship to Child(ren)"] = "Parent"
    boxes["Initial Pleading"] = True
 
    text["Party 1 Full Name"] = p.get("parent1_name")
    street1, csz1 = _pp_split_address(p.get("parent1_address"))
    text["Party 1 Street Address"] = street1
    text["Party 1 City, State, Zip"] = csz1
    text["Party 1 Telephone"] = p.get("parent1_phone", "")
    text["Party 1 E-mail"] = p.get("parent1_email", "")
 
    text["Party 2 Full Name"] = p.get("parent2_name")
    street2, csz2 = _pp_split_address(p.get("parent2_address"))
    text["Party 2 Street Address"] = street2
    text["Party 2 City, State, Zip"] = csz2
    text["Party 2 Telephone"] = p.get("parent2_phone", "")
    text["Party 2 E-mail"] = p.get("parent2_email", "")
 
    kids = _pp_parse_children(p.get("children_raw"))
    for i, kid in enumerate(kids[:6], start=1):
        text[f"Child {i} Name"] = kid["name"]
        text[f"Child {i} Date of Birth"] = kid["dob"]
 
    lc_type = _pp_str(p.get("legal_custody_type")).lower()
    if "joint" in lc_type:
        boxes["Shared parental responsibility"] = True
    elif lc_type.startswith("sole legal to me"):
        boxes["Sole parenting responsibility"] = True
        text["Name of Person who will make major decisions for the child(ren)"] = p.get("parent1_name")
    elif lc_type.startswith("sole legal to my spouse"):
        boxes["Sole parenting responsibility"] = True
        text["Name of Person who will make major decisions for the child(ren)"] = p.get("parent2_name")
 
    lc_final_say = p.get("legal_custody_final_say", {})
    category_field = {
        "medical_care": "medical care", "mental_health_care": "mental health",
        "education": "education", "religious_training": "religious training",
        "extracurricular_activities": "extracurricular activities",
    }
    any_tiebreak = False
    for cat, suffix in category_field.items():
        choice = _pp_str(lc_final_say.get(cat)).lower()
        if not choice or "not applicable" in choice:
            continue
        if "both" in choice:
            boxes[f"No tie-breaking authority for {suffix}"] = True
        else:
            any_tiebreak = True
            name = p.get("parent1_name") if choice == "me" else p.get("parent2_name")
            text[f"Name of Person for tie-breaking authority of {suffix}"] = name
    if any_tiebreak:
        boxes["Shared parental responsibility with decision-making authority"] = True
 
    schedule = p.get("regular_schedule", {})
    days_with_parent1 = [d for d, v in schedule.items() if _pp_str(v).lower() == "me"]
    days_with_parent2 = [d for d, v in schedule.items() if _pp_str(v).lower() in ("my spouse", "spouse")]
    if days_with_parent1:
        boxes["Weekdays for Party 1"] = True
        text["List days for Party 1"] = ", ".join(d.title() for d in days_with_parent1)
    if days_with_parent2:
        boxes["Weekdays for Party 2"] = True
        text["List days for Party 2"] = ", ".join(d.title() for d in days_with_parent2)
        text["Party 2 Name"] = p.get("parent2_name")
 
    freq = _pp_str(p.get("schedule_frequency")).lower()
    if freq == "every two weeks":
        text["List Other Issues 1"] = "Regular schedule alternates every two weeks."
    elif freq == "other":
        text["List Other Issues 1"] = p.get("schedule_frequency_detail", "")
 
    text["List Other Transportation"] = p.get("dropoff_location", "")
    boxes["Exchanges will occur at"] = bool(p.get("dropoff_location"))
    text["List Location/place exchanges will occur at"] = p.get("dropoff_location", "")
    text["List Other exchanges of the child(ren)"] = p.get("no_show_wait", "")
 
    holidays = p.get("holidays", {})
    for key, choice in holidays.items():
        base = _MD_HOLIDAY_FIELD_MAP.get(key.lower())
        if not base:
            continue
        choice = _pp_str(choice)
        who, _, when = choice.partition(" — ")
        who_name = p.get("parent1_name") if who.lower().startswith("me") else p.get("parent2_name")
        if "every year" in when.lower():
            text[f"{base} Every Year"] = who_name
        else:
            text[f"{base} Even Years"] = who_name
    boxes["Holiday parenting time will follow the schedule below. It will take priority over the regular weekday, weekend, and summer schedules"] = bool(holidays)
 
    breaks = _pp_str(p.get("breaks_handling")).lower()
    if "follow the regular" in breaks:
        boxes["We will follow the regular weekday and weekend schedule for winter break"] = True
        boxes["We will follow the regular weekday and weekend schedule for spring break"] = True
        boxes["We will follow the regular weekday and weekend schedule for summer break"] = True
    elif "alternate breaks" in breaks:
        boxes["We will alternate winter breaks"] = True
        boxes["We will alternate spring breaks"] = True
    elif breaks:
        boxes["We will divide winter breaks as follows"] = True
        text["Explain how you will divide winter breaks"] = p.get("breaks_detail", "")
 
    schooling = _pp_str(p.get("schooling_type")).lower()
    if schooling == "public school":
        boxes["Attend public school"] = True
        text["Name of Public School"] = p.get("school_registration_address", "")
    elif schooling == "private school":
        boxes["Attend private school"] = True
    elif schooling == "homeschool":
        boxes["Be homeschooled"] = True
    elif schooling:
        boxes["Other Schooling"] = True
        text["List other Schooling"] = p.get("schooling_type", "")
 
    transport = _pp_str(p.get("extracurricular_transport")).lower()
    if "scheduled time" in transport:
        boxes["Each of us agrees that extracurricular activities may occur during each party's scheduled parenting time"] = True
    elif transport:
        boxes["Each of us agrees as to the following extracurricular activities"] = True
        text["List Extracurricular activities"] = p.get("extracurricular_transport", "")
 
    text["Number of Hours"] = p.get("childcare_notice_hours", "")
    if p.get("childcare_notice_hours"):
        boxes["Each of us must offer the other party/parties the opportunity to care for the child(ren) before using a child care provider for any period exceeding"] = True
 
    text["Number of days' written notice must be given before traveling out of state"] = p.get("travel_notice_domestic_days", "")
    if p.get("travel_notice_domestic_days"):
        boxes["Each of us may travel within the United States with the child(ren) during our parenting time/vacation"] = True
    text["Number of days' written notice must be given before traveling out of the country"] = p.get("travel_notice_intl_days", "")
    if p.get("travel_notice_intl_days"):
        boxes["Each of us may travel out of the country with the child(ren) during our parenting time/vacation"] = True
 
    mediation = _pp_str(p.get("mediation_agreement")).lower()
    if mediation == "yes":
        boxes["We agree to attend mediation session(s) before asking the court to intervene"] = True
        text["Number of Mediation Session(s)"] = p.get("mediation_sessions", "1")
    elif mediation and mediation != "no":
        boxes["Other Disputes"] = True
        text["List Other Disputes"] = p.get("mediation_agreement", "")
 
    if _pp_str(p.get("domestic_abuse_flag")).lower() == "yes":
        boxes["Allegation of domestic abuse"] = True
 
    return text, boxes
 
 
def _pp_write_pdf(template_path, field_data, checkbox_values, filename_prefix):
    reader = PdfReader(template_path)
    writer = PdfWriter()
 
    writer.clone_reader_document_root(reader)
    writer.set_need_appearances_writer(True)
 
    clean_text = {k: v for k, v in field_data.items() if _pp_str(v)}
    for page in writer.pages:
        writer.update_page_form_field_values(page, clean_text)
 
    checked = {k: "/Yes" for k, v in checkbox_values.items() if v}
    for page in writer.pages:
        writer.update_page_form_field_values(page, checked)
 
    output = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    output.close()
    with open(output.name, "wb") as f:
        writer.write(f)
 
    filename = filename_prefix + "_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".pdf"
    return output.name, filename
 
 
# ---------------------------------------------------------------------
# PARENTING PLAN — routes
# ---------------------------------------------------------------------
 
@app.route("/fill-parenting-plan-dc", methods=["POST"])
def fill_parenting_plan_dc():
    try:
        data = request.json or {}
        if _pp_str(data.get("domestic_abuse_flag")).lower() == "yes":
            return jsonify({"error": "Domestic abuse / supervised parenting time flagged — route to Attorney Mohammed, do not auto-draft."}), 409
 
        text, boxes = _pp_build_dc_fields(data)
        path, filename = _pp_write_pdf(TEMPLATE_PDF_PP_DC, text, boxes, "DC_Parenting_Plan")
 
        return send_file(path, as_attachment=True, download_name=filename, mimetype="application/pdf")
    except Exception as e:
        return jsonify({"error": str(e)}), 500
 
 
@app.route("/fill-parenting-plan-md", methods=["POST"])
def fill_parenting_plan_md():
    try:
        data = request.json or {}
        if _pp_str(data.get("domestic_abuse_flag")).lower() == "yes":
            return jsonify({"error": "Domestic abuse / supervised parenting time flagged — route to Attorney Mohammed, do not auto-draft."}), 409
 
        text, boxes = _pp_build_md_fields(data)
        path, filename = _pp_write_pdf(TEMPLATE_PDF_PP_MD, text, boxes, "MD_Parenting_Plan")
 
        return send_file(path, as_attachment=True, download_name=filename, mimetype="application/pdf")
    except Exception as e:
        return jsonify({"error": str(e)}), 500
 
 
# Debug routes matching your existing /list-fields pattern
@app.route("/list-parenting-plan-dc-fields", methods=["GET"])
def list_parenting_plan_dc_fields():
    reader = PdfReader(TEMPLATE_PDF_PP_DC)
    fields = reader.get_fields()
    return jsonify(list(fields.keys()))
 
 
@app.route("/list-parenting-plan-md-fields", methods=["GET"])
def list_parenting_plan_md_fields():
    reader = PdfReader(TEMPLATE_PDF_PP_MD)
    fields = reader.get_fields()
    return jsonify(list(fields.keys()))
 


# =========================================================
# HELPERS
# =========================================================
def format_invoice_date_for_number(date_text):
    try:
        clean = date_text.split(",", 1)[1].strip()
        dt = datetime.strptime(clean, "%B %d, %Y")
        return dt.strftime("%m%d%Y")
    except Exception:
        return datetime.now().strftime("%m%d%Y")


def format_assignment_date(date_text):
    try:
        clean = date_text.split(",", 1)[1].strip()
        dt = datetime.strptime(clean, "%B %d, %Y")
        return dt.strftime("%m/%d/%Y")
    except Exception:
        return date_text


# =========================================================
# DEBUG ROUTES
# =========================================================
@app.route("/list-fields", methods=["GET"])
def list_fields():
    reader = PdfReader(TEMPLATE_PDF_GUARDIAN)
    fields = reader.get_fields()
    return jsonify(list(fields.keys()))


@app.route("/list-invoice-fields", methods=["GET"])
def list_invoice_fields():
    reader = PdfReader(TEMPLATE_PDF_INVOICE)
    fields = reader.get_fields()
    return jsonify(list(fields.keys()))


@app.route("/list-tod-fields", methods=["GET"])
def list_tod_fields():
    reader = PdfReader(TEMPLATE_PDF_TOD)
    fields = reader.get_fields()
    return jsonify(list(fields.keys()))


# =========================================================
# RUN
# =========================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
