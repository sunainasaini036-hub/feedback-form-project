from flask import (
    Flask,
    render_template,
    request,
    Response,
    session,
    redirect,
    url_for
)

from gemini_api import generate_form, analyze_feedback


from database import (

    create_database,

    save_form,

    get_form,

    save_response,

    get_responses,

    clean_responses,

    get_all_forms,

    update_form_db,

    count_total_responses,

    get_latest_responses,

    get_average_rating,

    get_question_statistics,

    get_rating_statistics,

    delete_form,

    create_user,

    get_user_by_email

)


from openpyxl import Workbook

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)


import uuid
import json
import os



# ==========================================
# Initialize Flask App
# ==========================================


app = Flask(__name__)


app.secret_key = os.environ.get(
    "SECRET_KEY",
    "development-secret-key"
)


# Create Database

create_database()



# ==========================================
# Authentication
# ==========================================


# -------------------------
# Register
# -------------------------

@app.route("/register", methods=["GET","POST"])
def register():


    if request.method == "POST":


        name = request.form["name"]

        email = request.form["email"]

        password = request.form["password"]



        hashed_password = generate_password_hash(
            password
        )


        create_user(
            name,
            email,
            hashed_password
        )


        return redirect(
            url_for("login")
        )


    return render_template(
        "register.html"
    )



# -------------------------
# Login
# -------------------------


@app.route("/login", methods=["GET","POST"])
def login():


    if request.method == "POST":


        email = request.form["email"]

        password = request.form["password"]



        user = get_user_by_email(
            email
        )


        if user and check_password_hash(
            user["password"],
            password
        ):


            session["user_id"] = user["id"]

            session["user_name"] = user["name"]



            return redirect(
                url_for("home")
            )


        return "Invalid Email or Password"



    return render_template(
        "login.html"
    )



# -------------------------
# Logout
# -------------------------


@app.route("/logout")
def logout():

    session.clear()


    return redirect(
        url_for("login")
    )




# ==========================================
# Home Page
# ==========================================
@app.route("/")
def home():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    return render_template(
        "home.html"
    )
# ==========================================
# My Forms
# ==========================================


@app.route("/myforms")
def my_forms():


    if "user_id" not in session:

        return redirect(
            url_for("login")
        )



    forms = get_all_forms(
        session["user_id"]
    )


    form_list = []



    for form in forms:


        responses = get_responses(
            form["form_id"]
        )


        form_list.append({

            "form_id":form["form_id"],

            "title":form["title"],

            "description":form["description"],

            "created_at":form["created_at"],

            "responses":len(responses)

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


    if "user_id" not in session:

        return redirect(
            url_for("login")
        )



    prompt = request.form["prompt"]



    form = generate_form(
        prompt
    )



    form_id = str(
        uuid.uuid4()
    )[:8]



    save_form(

        form_id,

        form,

        session["user_id"]

    )



    share_link = url_for(

        "open_form",

        form_id=form_id,

        _external=True

    )



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


    form = get_form(
        form_id
    )


    if form is None:

        return "<h2>❌ Form Not Found!</h2>"



    return render_template(

        "form.html",

        form=form,

        form_id=form_id

    )



# ==========================================
# Submit Response
# ==========================================


@app.route("/submit", methods=["POST"])
def submit():


    form_id = request.form["form_id"]


    answers = {}



    for key in request.form:


        if key=="form_id":

            continue



        values = request.form.getlist(
            key
        )



        if len(values)==1:

            answers[key]=values[0]


        else:

            answers[key]=values



    save_response(

        form_id,

        answers

    )



    return render_template(
        "thankyou.html"
    )

# ==========================================
# View Responses Dashboard
# ==========================================


@app.route("/responses/<form_id>")
def responses(form_id):


    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    form = get_form(
        form_id
    )


    if form is None:

        return "<h2>❌ Form Not Found!</h2>"



    responses = get_responses(
        form_id
    )


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


    if "user_id" not in session:

        return redirect(
            url_for("login")
        )



    form = get_form(
        form_id
    )



    if form is None:

        return "<h2>❌ Form Not Found!</h2>"



    all_responses = get_responses(
        form_id
    )



    cleaned_responses = clean_responses(
        all_responses
    )



    latest_responses = get_latest_responses(
        form_id
    )



    total_responses = count_total_responses(
        form_id
    )



    average_rating = get_average_rating(
        form_id
    )


    if average_rating is None:

        average_rating = 0


    average_rating = float(
        average_rating
    )



    question_statistics = get_question_statistics(
        form_id
    )



    rating_statistics = get_rating_statistics(
        form_id
    )



    ai_summary = analyze_feedback(

        form,

        cleaned_responses

    )



    if "sentiment" not in ai_summary:

        ai_summary["sentiment"]={

            "positive":0,

            "neutral":0,

            "negative":0

        }



    if "strengths" not in ai_summary:

        ai_summary["strengths"]=[]



    if "issues" not in ai_summary:

        ai_summary["issues"]=[]



    if "recommendations" not in ai_summary:

        ai_summary["recommendations"]=[]



    if "summary" not in ai_summary:

        ai_summary["summary"]="No AI summary available."




    if latest_responses:

        latest_submission = latest_responses[0]["submitted_at"]

    else:

        latest_submission = "No Responses Yet"



    return render_template(

        "analytics.html",

        form=form,

        form_id=form_id,

        responses=latest_responses,

        total_responses=total_responses,

        average_rating=average_rating,

        latest_submission=latest_submission,

        question_statistics=question_statistics,

        rating_statistics=rating_statistics,

        ai_summary=ai_summary

    )





# ==========================================
# Export CSV
# ==========================================


@app.route("/export/csv/<form_id>")
def export_csv(form_id):


    if "user_id" not in session:

        return redirect(
            url_for("login")
        )



    responses = get_responses(
        form_id
    )


    if not responses:

        return "<h2>No responses available.</h2>"



    first = responses[0]["answers"]


    headers = list(
        first.keys()
    )



    def generate_csv():


        yield ",".join(headers)+"\n"



        for response in responses:


            row=[]


            for key in headers:


                value=response["answers"].get(
                    key,
                    ""
                )



                if isinstance(value,list):

                    value=", ".join(value)



                row.append(
                    f'"{value}"'
                )



            yield ",".join(row)+"\n"



    return Response(

        generate_csv(),

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


    if "user_id" not in session:

        return redirect(
            url_for("login")
        )



    responses=get_responses(
        form_id
    )



    if not responses:

        return "<h2>No responses available.</h2>"



    workbook=Workbook()


    sheet=workbook.active


    sheet.title="Responses"



    headers=list(
        responses[0]["answers"].keys()
    )


    sheet.append(headers)



    for response in responses:


        row=[]


        for header in headers:


            value=response["answers"].get(
                header,
                ""
            )


            if isinstance(value,list):

                value=", ".join(value)


            row.append(value)



        sheet.append(row)



    filename=f"{form_id}_responses.xlsx"



    workbook.save(filename)



    return Response(

        open(filename,"rb").read(),

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


    if "user_id" not in session:

        return redirect(
            url_for("login")
        )



    form=get_form(
        form_id
    )



    if form is None:

        return "<h2>❌ Form Not Found!</h2>"



    return render_template(

        "edit_form.html",

        form=form,

        form_id=form_id

    )





# ==========================================
# Update Form
# ==========================================


@app.route("/update/<form_id>", methods=["POST"])
def update_form(form_id):


    if "user_id" not in session:

        return redirect(
            url_for("login")
        )



    form=get_form(
        form_id
    )



    if form is None:

        return "<h2>Form Not Found!</h2>"



    form["title"]=request.form.get(
        "title",
        ""
    )



    form["description"]=request.form.get(
        "description",
        ""
    )



    questions_json=request.form.get(
        "questions"
    )



    if questions_json:

        form["questions"]=json.loads(
            questions_json
        )



    update_form_db(

        form_id,

        form

    )



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


    if "user_id" not in session:

        return redirect(
            url_for("login")
        )



    delete_form(
        form_id
    )


    return redirect(
        url_for("my_forms")
    )





# ==========================================
# Run Application
# ==========================================


if __name__=="__main__":

    app.run(
        debug=False
    )