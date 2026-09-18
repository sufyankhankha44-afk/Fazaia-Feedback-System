from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    session,
    redirect,
    url_for
)

from supabase import create_client, Client
from dotenv import load_dotenv

from datetime import datetime, timezone
import os


# ==========================================
# LOAD ENVIRONMENT
# ==========================================

load_dotenv()


# ==========================================
# FLASK APP
# ==========================================

app = Flask(__name__)

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "FAZAIA_CHANGE_THIS_SECRET_KEY"
)


# ==========================================
# SUPABASE
# ==========================================

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
        "SUPABASE_URL and SUPABASE_KEY must be set in .env"
    )

supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)


# ==========================================
# ADMIN LOGIN
# ==========================================

ADMIN_USERNAME = os.environ.get(
    "ADMIN_USERNAME",
    "admin"
)

ADMIN_PASSWORD = os.environ.get(
    "ADMIN_PASSWORD",
    "fazaia123"
)


# ==========================================
# HELPER FUNCTIONS
# ==========================================

def get_feedback():

    response = (
        supabase
        .table("feedback")
        .select("*")
        .execute()
    )

    return response.data or []


def first_value(row, *names):

    for name in names:

        value = row.get(name)

        if value is not None and value != "":
            return value

    return ""


def normalize_feedback(row):

    return {

        "id": row.get("id"),

        "student_name": first_value(
            row,
            "student_name"
        ),

        "school_id": first_value(
            row,
            "school_id"
        ),

        "class_name": first_value(
            row,
            "class_name",
            "class"
        ),

        "class_id": row.get(
            "class_id"
        ),

        "section": first_value(
            row,
            "section"
        ),

        "feedback_type": first_value(
            row,
            "feedback_type",
            "category"
        ),

        "category_id": row.get(
            "category_id"
        ),

        "subject": first_value(
            row,
            "subject",
            "subject_name"
        ),

        "teacher_name": first_value(
            row,
            "teacher_name"
        ),

        "problems": first_value(
            row,
            "problem",
            "problems"
        ),

        "rating": row.get(
            "rating"
        ),

        "additional_feedback": first_value(
            row,
            "additional_description",
            "additional_feedback",
            "description"
        ),

        "description": first_value(
            row,
            "description",
            "additional_description"
        ),

        "status": first_value(
            row,
            "status"
        ) or "New",

        "created_at": first_value(
            row,
            "created_at"
        ),

        "updated_at": first_value(
            row,
            "updated_at"
        )
    }


def normalize_all_feedback(rows):

    return [
        normalize_feedback(row)
        for row in rows
    ]


# ==========================================
# OPTIONAL RELATED ID LOOKUP
# ==========================================

def find_related_id(table_name, wanted_value):

    if not wanted_value:
        return None

    try:

        response = (
            supabase
            .table(table_name)
            .select("*")
            .execute()
        )

        rows = response.data or []

        wanted = str(
            wanted_value
        ).strip().lower()

        for row in rows:

            for key in [
                "name",
                "class_name",
                "class",
                "category",
                "category_name",
                "title",
                "label"
            ]:

                value = row.get(key)

                if value is None:
                    continue

                if (
                    str(value)
                    .strip()
                    .lower()
                    == wanted
                ):

                    return row.get("id")

    except Exception as error:

        print(
            "OPTIONAL RELATED LOOKUP ERROR:",
            error
        )

    return None


# ==========================================
# CURRENT UTC TIME
# ==========================================

def current_utc_time():

    return datetime.now(
        timezone.utc
    ).isoformat()


# ==========================================
# STUDENT PAGE
# ==========================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# ==========================================
# SUBMIT FEEDBACK
# ==========================================

@app.route(
    "/submit-feedback",
    methods=["POST"]
)
def submit_feedback():

    try:

        data = request.get_json() or {}

        # ==================================
        # GET FORM DATA
        # ==================================

        student_name = str(
            data.get(
                "student_name",
                ""
            )
        ).strip()

        school_id = str(
            data.get(
                "school_id",
                ""
            )
        ).strip()

        class_name = str(
            data.get(
                "class_name",
                ""
            )
        ).strip()

        section = str(
            data.get(
                "section",
                ""
            )
        ).strip()

        # ==================================
        # GET MULTIPLE FEEDBACK TYPES
        # ==================================

        feedback_types = data.get(
            "feedback_type",
            []
        )

        if isinstance(
            feedback_types,
            str
        ):

            feedback_types = [
                feedback_types
            ]

        feedback_types = [

            str(item).strip()

            for item in feedback_types

            if str(item).strip()

        ]

        subject = str(
            data.get(
                "subject",
                ""
            )
        ).strip()

        teacher_name = str(
            data.get(
                "teacher_name",
                ""
            )
        ).strip()

        problems = data.get(
            "problems",
            []
        )

        problem_description = str(
            data.get(
                "problem_description",
                ""
            )
        ).strip()

        rating = data.get(
            "rating"
        )

        additional_feedback = str(
            data.get(
                "additional_feedback",
                ""
            )
        ).strip()


        # ==================================
        # VALIDATION
        # ==================================

        if not student_name:

            return jsonify({
                "success": False,
                "message":
                    "Please enter your name."
            }), 400


        if not school_id:

            return jsonify({
                "success": False,
                "message":
                    "Please enter your School ID."
            }), 400


        if not class_name:

            return jsonify({
                "success": False,
                "message":
                    "Please select your class."
            }), 400


        if not feedback_types:

            return jsonify({
                "success": False,
                "message":
                    "Please select at least one feedback type."
            }), 400


        # ==================================
        # PREPARE PROBLEM TEXT
        # ==================================

        if isinstance(
            problems,
            list
        ):

            problem_text = ", ".join(
                str(item)
                for item in problems
            )

        else:

            problem_text = str(
                problems
            )


        if problem_description:

            if problem_text:

                problem_text += (
                    " | Description: "
                    + problem_description
                )

            else:

                problem_text = (
                    problem_description
                )


        # ==================================
        # CURRENT TIME
        # ==================================

        current_time = current_utc_time()


        # ==================================
        # MAIN FEEDBACK RECORD
        #
        # This is the common information.
        # A separate copy will be created
        # for every selected feedback type.
        # ==================================

        feedback_record = {

            "student_name":
                student_name,

            "school_id":
                school_id,

            "section":
                section,

            "subject":
                subject,

            "teacher_name":
                teacher_name,

            "rating":
                rating,

            "description":
                (
                    problem_description
                    + (
                        " | Additional: "
                        + additional_feedback
                        if additional_feedback
                        else ""
                    )
                ),

            "status":
                "New",

            "created_at":
                current_time,

            "updated_at":
                current_time,

            "class_name":
                class_name,

            "feedback_type":
                "",

            "problems":
                problem_text
        }


        # ==================================
        # OPTIONAL CLASS ID
        #
        # If a matching class exists,
        # save its ID.
        #
        # If it doesn't exist, DO NOT
        # reject the student's feedback.
        # ==================================

        class_id = find_related_id(
            "classes",
            class_name
        )

        if class_id is not None:

            feedback_record[
                "class_id"
            ] = class_id


        # ==================================
        # INSERT ONE RECORD FOR EACH
        # SELECTED FEEDBACK TYPE
        # ==================================

        for feedback_type in feedback_types:

            record = feedback_record.copy()

            record[
                "feedback_type"
            ] = feedback_type


            # ==================================
            # OPTIONAL CATEGORY ID
            # ==================================

            category_id = find_related_id(
                "feedback_categories",
                feedback_type
            )

            if category_id is not None:

                record[
                    "category_id"
                ] = category_id


            # ==================================
            # INSERT INTO SUPABASE
            # ==================================

            print(
                "SUBMITTING FEEDBACK:"
            )

            print(
                record
            )


            response = (
                supabase
                .table("feedback")
                .insert(record)
                .execute()
            )


            print(
                "FEEDBACK INSERTED:",
                response.data
            )


        # ==================================
        # SUCCESS RESPONSE
        # ==================================

        return jsonify({

            "success":
                True,

            "message":
                "Your feedback has been "
                "submitted successfully."

        })


    except Exception as error:

        print(
            "FEEDBACK ERROR:",
            error
        )

        return jsonify({

            "success":
                False,

            "message":
                "Something went wrong while "
                "submitting your feedback: "
                + str(error)

        }), 500


# ==========================================
# ADMIN LOGIN
# ==========================================

@app.route(
    "/admin-login",
    methods=["GET", "POST"]
)
def admin_login():

    if session.get(
        "admin_logged_in"
    ):

        return redirect(
            url_for(
                "admin_dashboard"
            )
        )


    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )


        if (
            username == ADMIN_USERNAME
            and
            password == ADMIN_PASSWORD
        ):

            session[
                "admin_logged_in"
            ] = True

            return redirect(
                url_for(
                    "admin_dashboard"
                )
            )


        return render_template(
            "login.html",
            error=
                "Incorrect username or password."
        )


    return render_template(
        "login.html"
    )


# ==========================================
# ADMIN LOGOUT
# ==========================================

@app.route("/admin-logout")
def admin_logout():

    session.pop(
        "admin_logged_in",
        None
    )

    return redirect(
        url_for(
            "admin_login"
        )
    )


# ==========================================
# ADMIN DASHBOARD
# ==========================================

@app.route("/admin")
def admin_dashboard():

    if not session.get(
        "admin_logged_in"
    ):

        return redirect(
            url_for(
                "admin_login"
            )
        )


    try:

        # ==================================
        # GET DATA
        # ==================================

        raw_feedback = get_feedback()

        feedback = normalize_all_feedback(
            raw_feedback
        )


        # ==================================
        # FILTERS
        # ==================================

        selected_class = request.args.get(
            "class",
            ""
        ).strip()

        selected_type = request.args.get(
            "type",
            ""
        ).strip()

        selected_subject = request.args.get(
            "subject",
            ""
        ).strip()


        # ==================================
        # APPLY FILTERS
        # ==================================

        filtered_feedback = []


        for item in feedback:

            if (
                selected_class
                and
                item["class_name"]
                != selected_class
            ):
                continue


            if (
                selected_type
                and
                item["feedback_type"]
                != selected_type
            ):
                continue


            if (
                selected_subject
                and
                item["subject"]
                != selected_subject
            ):
                continue


            filtered_feedback.append(
                item
            )


        # ==================================
        # SORT NEWEST FIRST
        # ==================================

        filtered_feedback.sort(
            key=lambda item:
                item.get("id") or 0,
            reverse=True
        )


        # ==================================
        # TOTAL FEEDBACK
        # ==================================

        total_feedback = len(
            filtered_feedback
        )


        # ==================================
        # STATUS COUNTS
        # ==================================

        new_feedback = sum(
            1
            for item in filtered_feedback
            if item["status"] == "New"
        )


        under_review = sum(
            1
            for item in filtered_feedback
            if item["status"] == "Under Review"
        )


        reviewed = sum(
            1
            for item in filtered_feedback
            if item["status"] == "Reviewed"
        )


        resolved = sum(
            1
            for item in filtered_feedback
            if item["status"] == "Resolved"
        )


        # ==================================
        # FEEDBACK BY CLASS
        # ==================================

        class_counts = {}


        for item in filtered_feedback:

            name = (
                item["class_name"]
                or "Unknown"
            )

            class_counts[name] = (
                class_counts.get(
                    name,
                    0
                ) + 1
            )


        class_data = [

            {
                "class_name":
                    name,

                "count":
                    count
            }

            for name, count
            in class_counts.items()

        ]


        class_data.sort(
            key=lambda item:
                item["count"],
            reverse=True
        )


        # ==================================
        # FEEDBACK BY TYPE
        # ==================================

        type_counts = {}


        for item in filtered_feedback:

            name = (
                item["feedback_type"]
                or "Unknown"
            )

            type_counts[name] = (
                type_counts.get(
                    name,
                    0
                ) + 1
            )


        type_data = [

            {
                "feedback_type":
                    name,

                "count":
                    count
            }

            for name, count
            in type_counts.items()

        ]


        type_data.sort(
            key=lambda item:
                item["count"],
            reverse=True
        )


        # ==================================
        # RATING DATA
        # ==================================

        rating_counts = {}


        for item in filtered_feedback:

            rating = item.get(
                "rating"
            )


            if rating is None:
                continue


            try:

                rating = int(
                    rating
                )

            except (ValueError, TypeError):

                continue


            rating_counts[rating] = (
                rating_counts.get(
                    rating,
                    0
                ) + 1
            )


        rating_data = [

            {
                "rating":
                    rating,

                "count":
                    count
            }

            for rating, count
            in rating_counts.items()

        ]


        rating_data.sort(
            key=lambda item:
                item["rating"]
        )


        # ==================================
        # CONCERN ANALYTICS
        # ==================================

        concern_names = [

            "Subject Difficulty",

            "Teaching Method",

            "Teacher Behaviour",

            "Strictness / Discipline",

            "Student Environment",

            "Facilities",

            "School Activity",

            "Workload",

            "Other"

        ]


        concern_data = []


        for concern in concern_names:

            count = 0


            for item in filtered_feedback:

                problem = str(
                    item.get(
                        "problems"
                    )
                    or ""
                ).lower()


                if concern.lower() in problem:

                    count += 1


            concern_data.append({

                "name":
                    concern,

                "count":
                    count

            })


        concern_data.sort(
            key=lambda item:
                item["count"],
            reverse=True
        )


        # ==================================
        # ADMINISTRATION INSIGHTS
        # ==================================

        most_reported_concern = "No data"


        if (
            concern_data
            and
            concern_data[0]["count"] > 0
        ):

            most_reported_concern = (
                concern_data[0]["name"]
            )


        top_class = "No data"


        if class_data:

            top_class = (
                class_data[0]["class_name"]
            )


        top_feedback_type = "No data"


        if type_data:

            top_feedback_type = (
                type_data[0]["feedback_type"]
            )


        # ==================================
        # AVERAGE RATING
        # ==================================

        rating_values = []


        for item in filtered_feedback:

            rating = item.get(
                "rating"
            )


            if rating is None:
                continue


            try:

                rating_values.append(
                    float(rating)
                )

            except (ValueError, TypeError):

                pass


        if rating_values:

            average_rating = round(

                sum(
                    rating_values
                )
                /
                len(
                    rating_values
                ),

                1

            )

        else:

            average_rating = 0


        # ==================================
        # FILTER OPTIONS
        # ==================================

        classes = []


        class_names = sorted({

            item["class_name"]

            for item in feedback

            if item["class_name"]

        })


        for name in class_names:

            classes.append({

                "class_name":
                    name

            })


        feedback_types = []


        type_names = sorted({

            item["feedback_type"]

            for item in feedback

            if item["feedback_type"]

        })


        for name in type_names:

            feedback_types.append({

                "feedback_type":
                    name

            })


        subjects = []


        subject_names = sorted({

            item["subject"]

            for item in feedback

            if item["subject"]

        })


        for name in subject_names:

            subjects.append({

                "subject":
                    name

            })


        # ==================================
        # RENDER DASHBOARD
        # ==================================

        return render_template(

            "admin.html",

            feedback=
                filtered_feedback,

            total_feedback=
                total_feedback,

            new_feedback=
                new_feedback,

            under_review=
                under_review,

            reviewed=
                reviewed,

            resolved=
                resolved,

            class_data=
                class_data,

            type_data=
                type_data,

            concern_data=
                concern_data,

            rating_data=
                rating_data,

            classes=
                classes,

            feedback_types=
                feedback_types,

            subjects=
                subjects,

            selected_class=
                selected_class,

            selected_type=
                selected_type,

            selected_subject=
                selected_subject,

            most_reported_concern=
                most_reported_concern,

            top_class=
                top_class,

            top_feedback_type=
                top_feedback_type,

            average_rating=
                average_rating
        )


    except Exception as error:

        print(
            "ADMIN DASHBOARD ERROR:",
            error
        )


        return (

            "Administration dashboard error: "
            + str(error),

            500

        )


# ==========================================
# UPDATE FEEDBACK STATUS
# ==========================================

@app.route(
    "/update-status",
    methods=["POST"]
)
def update_status():

    if not session.get(
        "admin_logged_in"
    ):

        return jsonify({

            "success":
                False,

            "message":
                "Administration login required."

        }), 401


    try:

        data = (
            request.get_json()
            or {}
        )


        feedback_id = data.get(
            "id"
        )


        new_status = data.get(
            "status"
        )


        allowed_statuses = [

            "New",

            "Under Review",

            "Reviewed",

            "Resolved"

        ]


        if new_status not in allowed_statuses:

            return jsonify({

                "success":
                    False,

                "message":
                    "Invalid status."

            }), 400


        response = (

            supabase

            .table("feedback")

            .update({

                "status":
                    new_status,

                "updated_at":
                    current_utc_time()

            })

            .eq(
                "id",
                feedback_id
            )

            .execute()

        )


        print(
            "STATUS UPDATED:",
            response.data
        )


        return jsonify({

            "success":
                True,

            "message":
                "Status updated."

        })


    except Exception as error:

        print(
            "STATUS ERROR:",
            error
        )


        return jsonify({

            "success":
                False,

            "message":
                "Could not update feedback status."

        }), 500


# ==========================================
# START SERVER
# ==========================================

if __name__ == "__main__":

    app.run(

        host="0.0.0.0",

        port=5000,

        debug=True

    )