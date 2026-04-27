from flask import Flask, request, send_file, jsonify
from pypdf import PdfReader, PdfWriter
import tempfile
import os

app = Flask(__name__)

TEMPLATE_PDF = "ccgn041prefilled.pdf"

@app.route("/fill-standby-guardian", methods=["POST"])
def fill_standby_guardian():
    try:
        data = request.json or {}

   field_data = {
    "Your Name 1": data.get("parent_names", ""),
    "Address 1": data.get("parent_address", ""),
    "Telephone Number 1": data.get("parent_phone", ""),
    "E-mail 1": data.get("parent_email", ""),

    # signature page address fields
    "Street Address 1": data.get("parent_address", ""),
    "City, State, Zip 1": data.get("parent_city_state_zip", ""),

    "Street Address 2": data.get("parent2_address", ""),
    "City, State, Zip 2": data.get("parent2_city_state_zip", ""),

    "Name of Standby Guardian": data.get("standby_guardian_name", ""),
    "Address 2": data.get("standby_guardian_address", ""),
    "Telephone Number 2": data.get("standby_guardian_phone", ""),
    "Email 2": data.get("standby_guardian_email", ""),

    "Name of Alternate guardian": data.get("alternate_guardian_name", ""),

    "Name of Children 1": data.get("child1_name", ""),
    "Date of Birth 1": data.get("child1_dob", ""),
    "Name of Children 2": data.get("child2_name", ""),
    "Date of Birth 2": data.get("child2_dob", ""),
    "Name of Children 3": data.get("child3_name", ""),
    "Date of Birth 3": data.get("child3_dob", ""),
    "Name of Children 4": data.get("child4_name", ""),
    "Date of Birth 4": data.get("child4_dob", ""),

    "Name of Person with Parental Rights": data.get("other_parent_name", "NONE"),
    "Relationship to Minor Child": data.get("other_parent_relationship", "N/A"),
    "Name of Person with Parental Rights 2": data.get("other_parent_name_2", ""),
    "Relationship to Minor child 2": data.get("other_parent_relationship_2", ""),

    "Box 3": data.get("guardian_person_limits", "NONE"),
    "Box 4": data.get("guardian_property_limits", "NONE"),
    "Location 1": data.get("child_property_location", "____"),
}

        reader = PdfReader(TEMPLATE_PDF)
        writer = PdfWriter()

        writer.clone_reader_document_root(reader)
        writer.set_need_appearances_writer(True)

        for page in writer.pages:
            writer.update_page_form_field_values(page, field_data)

        checkbox_values = {
            "Check Box94": "/Yes",
            "Check Box97": "/Yes",
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

        return send_file(
            output.name,
            as_attachment=True,
            download_name="filled_standby_guardian.pdf",
            mimetype="application/pdf"
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/list-fields", methods=["GET"])
def list_fields():
    reader = PdfReader(TEMPLATE_PDF)
    fields = reader.get_fields()
    return jsonify(list(fields.keys()))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
