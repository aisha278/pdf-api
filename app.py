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
            "Your Name(s)": data.get("parent_names", ""),
            "Name of Standby Guardian": data.get("standby_guardian_name", ""),
            "Name of Alternate Standby Guardian": data.get("alternate_guardian_name", ""),

            "Name of Person with Parental Rights 2": data.get("other_parent_name", "NONE"),
            "Relationship to Minor child 2": data.get("other_parent_relationship", "N/A"),

            "Box 3": data.get("guardian_person_limits", "NONE"),
            "Box 4": data.get("guardian_property_limits", "NONE"),

            "Location 1": data.get("child_property_location", "____"),
        }

        reader = PdfReader(TEMPLATE_PDF)
        writer = PdfWriter()

        for page in reader.pages:
            writer.add_page(page)

        writer.set_need_appearances_writer(True)

        for page in writer.pages:
            writer.update_page_form_field_values(page, field_data)

        # checkboxes based on your PDF fields
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

        writer.update_page_form_field_values(writer.pages[0], checkbox_values)
        writer.update_page_form_field_values(writer.pages[1], checkbox_values)
        writer.update_page_form_field_values(writer.pages[2], checkbox_values)

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
