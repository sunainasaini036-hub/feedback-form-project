import sqlite3
import json

DATABASE = "database.db"


# ==========================================
# Create Database
# ==========================================

def create_database():

    conn = sqlite3.connect(DATABASE)

    cursor = conn.cursor()

    # -----------------------------
    # Forms Table
    # -----------------------------

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS forms(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        form_id TEXT UNIQUE,

        title TEXT,

        description TEXT,

        questions TEXT,

        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )

    """)

    # -----------------------------
    # Responses Table
    # -----------------------------

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS responses(

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        form_id TEXT,

        answers TEXT,

        submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

    )

    """)

    conn.commit()

    conn.close()


# ==========================================
# Save Generated Form
# ==========================================

def save_form(form_id, form):

    conn = sqlite3.connect(DATABASE)

    cursor = conn.cursor()

    cursor.execute("""

    INSERT INTO forms
    (form_id,title,description,questions)

    VALUES(?,?,?,?)

    """,(

        form_id,

        form["title"],

        form["description"],

        json.dumps(form["questions"])

    ))

    conn.commit()

    conn.close()


# ==========================================
# Load Form
# ==========================================

def get_form(form_id):

    conn = sqlite3.connect(DATABASE)

    cursor = conn.cursor()

    cursor.execute(

        "SELECT * FROM forms WHERE form_id=?",

        (form_id,)

    )

    row = cursor.fetchone()

    conn.close()

    if row is None:

        return None

    return{

        "form_id":row[1],

        "title":row[2],

        "description":row[3],

        "questions":json.loads(row[4])

    }


# ==========================================
# Save Student Response
# ==========================================

def save_response(form_id, answers):

    conn = sqlite3.connect(DATABASE)

    cursor = conn.cursor()

    cursor.execute("""

    INSERT INTO responses
    (form_id,answers)

    VALUES(?,?)

    """,(

        form_id,

        json.dumps(answers)

    ))

    conn.commit()

    conn.close()


# ==========================================
# Get Responses
# ==========================================
def get_responses(form_id):

    conn = sqlite3.connect(DATABASE)

    cursor = conn.cursor()

    cursor.execute("""

    SELECT answers, submitted_at

    FROM responses

    WHERE form_id=?

    ORDER BY submitted_at DESC

    """,(form_id,))

    rows = cursor.fetchall()

    conn.close()

    responses = []

    for row in rows:

        responses.append({

            "answers": json.loads(row[0]),

            "submitted_at": row[1]

        })

    return responses
# ==========================================
# Get All Forms
# ==========================================

def get_all_forms():

    conn = sqlite3.connect(DATABASE)

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute("""

    SELECT *

    FROM forms

    ORDER BY created_at DESC

    """)

    forms = cursor.fetchall()

    conn.close()

    return forms
# ==========================================
# Update Form
# ==========================================

def update_form_db(form_id, form):

    conn = sqlite3.connect(DATABASE)

    cursor = conn.cursor()

    cursor.execute("""

    UPDATE forms

    SET
        title=?,
        description=?,
        questions=?

    WHERE form_id=?

    """,(

        form["title"],

        form["description"],

        json.dumps(form["questions"]),

        form_id

    ))

    conn.commit()

    conn.close()
# ==========================================
# Question Statistics
# ==========================================

def get_question_statistics(form_id):

    form = get_form(form_id)
    responses = get_responses(form_id)

    statistics = {}

    if form is None:
        return statistics

    # Create empty dictionary for every question
    for question in form["questions"]:

        statistics[question["label"]] = {}

    # Count answers
    for response in responses:

        answers = response["answers"]

        for question, answer in answers.items():

            if question not in statistics:
                statistics[question] = {}

            # Checkbox (list of answers)
            if isinstance(answer, list):

                for option in answer:

                    option = str(option).strip()

                    if option == "":
                        continue

                    statistics[question][option] = (
                        statistics[question].get(option, 0) + 1
                    )

            # Normal text / radio / dropdown / rating
            else:

                answer = str(answer).strip()

                if answer == "":
                    continue

                statistics[question][answer] = (
                    statistics[question].get(answer, 0) + 1
                )

    return statistics
# ==========================================
# Count Total Responses
# ==========================================

def count_total_responses(form_id):

    responses = get_responses(form_id)

    return len(responses)


# ==========================================
# Get Latest Responses
# ==========================================

def get_latest_responses(form_id, limit=5):

    responses = get_responses(form_id)

    return responses[:limit]


# ==========================================
# Calculate Average Rating
# ==========================================

def get_average_rating(form_id):

    form = get_form(form_id)

    responses = get_responses(form_id)

    if form is None:

        return "N/A"

    rating_questions = []

    for question in form["questions"]:

        if question["type"] == "rating":

            rating_questions.append(question["label"])

    if not rating_questions:

        return "N/A"

    total = 0

    count = 0

    for response in responses:

        answers = response["answers"]

        for label in rating_questions:

            if label in answers:

                try:

                    total += int(answers[label])

                    count += 1

                except:

                    pass

    if count == 0:

        return "N/A"

    return round(total / count, 1)
# ==========================================
# Rating Statistics
# ==========================================

def get_rating_statistics(form_id):

    form = get_form(form_id)
    responses = get_responses(form_id)

    result = {}

    if form is None:
        return result

    for question in form["questions"]:

        if question["type"] != "rating":
            continue

        label = question["label"]

        ratings = []

        for response in responses:

            answers = response["answers"]

            if label in answers:

                try:
                    ratings.append(int(answers[label]))
                except:
                    pass

        if ratings:

            result[label] = {

                "average": round(sum(ratings)/len(ratings),1),

                "highest": max(ratings),

                "lowest": min(ratings),

                "count": len(ratings)

            }

    return result
# ==========================================
# Delete Form
# ==========================================

def delete_form(form_id):

    conn = sqlite3.connect(DATABASE)

    cursor = conn.cursor()

    # Delete all responses of this form
    cursor.execute("""

    DELETE FROM responses

    WHERE form_id=?

    """, (form_id,))

    # Delete the form
    cursor.execute("""

    DELETE FROM forms

    WHERE form_id=?

    """, (form_id,))

    conn.commit()

    conn.close()
def get_form_responses(form_id):

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT answers 
        FROM responses 
        WHERE form_id=?
        """,
        (form_id,)
    )

    data = cursor.fetchall()

    conn.close()

    return data