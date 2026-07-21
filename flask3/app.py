from flask import (
    Flask,
    render_template,
    request,
    Response
)
from gemini_api import generate_form
from database import (
    create_database,
    save_form,
    get_form,
    save_response,
    get_responses,
    get_all_forms,
    update_form_db,
    count_total_responses,
    get_latest_responses,
    get_average_rating,
    get_question_statistics,
    get_rating_statistics
)
from openpyxl import Workbook
import uuid
import csv
from database import delete_form
import json

# ==========================================
# Initialize App
# ==========================================

app = Flask(__name__)

# Create database tables
create_database()


# ==========================================
# Home Page
# ==========================================

@app.route("/")
def home():
    return render_template("home.html")
# ==========================================
# My Forms
# ==========================================

@app.route("/myforms")
def my_forms():

    forms = get_all_forms()

    form_list = []

    for form in forms:

        responses = get_responses(form["form_id"])

        form_list.append({

            "form_id": form["form_id"],

            "title": form["title"],

            "description": form["description"],

            "created_at": form["created_at"],

            "responses": len(responses)

        })

    return render_template(

        "myforms.html",

        forms=form_list

    )


# ==========================================
# Generate AI Form
# ==========================================

@app.route("/generate", methods=["POST"])
def generate():

    # User Prompt
    prompt = request.form["prompt"]

    # Generate Form using Gemini
    form = generate_form(prompt)

    # Generate Unique Form ID
    form_id = str(uuid.uuid4())[:8]

    # Save Form into Database
    save_form(form_id, form)

    share_link = url_for(
    "open_form",
    form_id=form_id,
    _external=True
)
    # Show Preview Page
    return render_template(
    "preview.html",
    form=form,
    form_id=form_id,
    share_link=share_link,
    total_responses=0
)

# ==========================================
# Open Shared Form
# ==========================================

@app.route("/form/<form_id>")
def open_form(form_id):

    form = get_form(form_id)

    if form is None:
        return "<h2>❌ Form Not Found!</h2>"

    return render_template(
        "form.html",
        form=form,
        form_id=form_id
    )


# ==========================================
# Submit Student Response
# ==========================================
@app.route("/submit", methods=["POST"])
def submit():

    form_id = request.form["form_id"]

    answers = {}

    for key in request.form:

        if key == "form_id":
            continue

        values = request.form.getlist(key)

        if len(values) == 1:
            answers[key] = values[0]
        else:
            answers[key] = values

    print(answers)      # <-- for testing

    save_response(form_id, answers)

    return render_template("thankyou.html")
# ==========================================
# View Responses Dashboard
# ==========================================

@app.route("/responses/<form_id>")
def responses(form_id):

    # Get form details
    form = get_form(form_id)

    if form is None:
        return "<h2>❌ Form Not Found!</h2>"

    # Get all responses
    responses = get_responses(form_id)

    return render_template(
    "responses.html",
    form=form,
    form_id=form_id,
    responses=responses,
    total_responses=len(responses)
)
# ==========================================
# Analytics Dashboard
# ==========================================
@app.route("/analytics/<form_id>")
def analytics(form_id):

    form = get_form(form_id)

    if form is None:

        return "<h2>❌ Form Not Found!</h2>"

    responses = get_latest_responses(form_id)

    total_responses = count_total_responses(form_id)

    average_rating = get_average_rating(form_id)
    question_statistics = get_question_statistics(form_id)
    rating_statistics = get_rating_statistics(form_id)

    if responses:

        latest_submission = responses[0]["submitted_at"]

    else:

        latest_submission = "No Responses Yet"

    return render_template(

        "analytics.html",

        form=form,

        form_id=form_id,

        responses=responses,

        total_responses=total_responses,

        average_rating=average_rating,

        latest_submission=latest_submission,
        question_statistics=question_statistics,
        rating_statistics=rating_statistics

    )
# ==========================================
# Export CSV
# ==========================================
@app.route("/export/csv/<form_id>")
def export_csv(form_id):

    responses = get_responses(form_id)

    if not responses:

        return "<h2>No responses available.</h2>"

    first = responses[0]["answers"]

    headers = list(first.keys())

    def generate():

        yield ",".join(headers) + "\n"

        for response in responses:

            row = []

            for key in headers:

                value = response["answers"].get(key, "")

                if isinstance(value, list):

                    value = ", ".join(value)

                row.append(f'"{value}"')

            yield ",".join(row) + "\n"

    return Response(

        generate(),

        mimetype="text/csv",

        headers={

            "Content-Disposition":

            f"attachment; filename={form_id}_responses.csv"

        }

    )
# ==========================================
# Export Excel
# ==========================================
@app.route("/export/excel/<form_id>")
def export_excel(form_id):

    responses = get_responses(form_id)

    if not responses:
        return "<h2>No responses available.</h2>"

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Responses"

    # Get column headers
    headers = list(responses[0]["answers"].keys())
    sheet.append(headers)

    # Add response rows
    for response in responses:

        row = []

        for header in headers:

            value = response["answers"].get(header, "")

            if isinstance(value, list):
                value = ", ".join(value)

            row.append(value)

        sheet.append(row)

    filename = f"{form_id}_responses.xlsx"

    workbook.save(filename)

    return Response(
        open(filename, "rb").read(),
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition":
            f"attachment; filename={filename}"
        }
    )
# ==========================================
# Edit Form
# ==========================================

@app.route("/edit/<form_id>")
def edit_form(form_id):

    form = get_form(form_id)

    if form is None:
        return "<h2>❌ Form Not Found!</h2>"

    return render_template(
        "edit_form.html",
        form=form,
        form_id=form_id
    )
from flask import redirect, url_for
@app.route("/update/<form_id>", methods=["POST"])
def update_form(form_id):

    form = get_form(form_id)

    if form is None:
        return "<h2>Form Not Found!</h2>"


    # Update title and description

    form["title"] = request.form.get("title", "")
    form["description"] = request.form.get("description", "")


    # Get complete questions list from frontend

    questions_json = request.form.get("questions")


    if questions_json:

        form["questions"] = json.loads(questions_json)


    # Save into SQLite

    update_form_db(form_id, form)


    return redirect(
        url_for(
            "edit_form",
            form_id=form_id
        )
    )

# ==========================================
# Delete Form
# ==========================================

@app.route("/delete/<form_id>")
def delete_form_route(form_id):

    delete_form(form_id)

    return redirect(url_for("my_forms"))
# ==========================================
# Run Application
# ==========================================

if __name__ == "__main__":
 app.run(debug=False)