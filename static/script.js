const form = document.getElementById("feedbackForm");
const message = document.getElementById("message");

form.addEventListener("submit", async function (event) {

    event.preventDefault();

    // Get selected rating
    const selectedRating = document.querySelector(
        'input[name="rating"]:checked'
    );

    // Get selected concerns
    const selectedProblems = Array.from(
        document.querySelectorAll(
            'input[name="problem"]:checked'
        )
    ).map(function (checkbox) {
        return checkbox.value;
    });

    // Get written problem description
    const problemDescription = document.getElementById(
        "problem_description"
    ).value.trim();


    // Require at least one concern
    if (selectedProblems.length === 0) {

        message.textContent =
            "Please select at least one concern.";

        message.style.color = "#c0392b";

        return;
    }


    // Prepare feedback data
    const data = {

        student_name: document.getElementById(
            "student_name"
        ).value.trim(),

        school_id: document.getElementById(
            "school_id"
        ).value.trim(),

        class_name: document.getElementById(
            "class_name"
        ).value,

        section: document.getElementById(
            "section"
        ).value.trim(),

        feedback_type: document.getElementById(
            "feedback_type"
        ).value,

        subject: document.getElementById(
            "subject"
        ).value.trim(),

        problems: selectedProblems,

        problem_description: problemDescription,

        rating: selectedRating
            ? selectedRating.value
            : null,

        additional_feedback:
            document.getElementById(
                "additional_feedback"
            ).value.trim()

    };


    // Show submitting message
    message.textContent =
        "Submitting your feedback...";

    message.style.color = "#2457e6";


    try {

        const response = await fetch(
            "/submit-feedback",
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify(data)
            }
        );


        const result = await response.json();


        if (response.ok && result.success) {

            message.textContent =
                "✓ " + result.message;

            message.style.color =
                "#16803c";

            // Clear the form
            form.reset();

            // Return to top
            window.scrollTo({
                top: 0,
                behavior: "smooth"
            });


        } else {

            message.textContent =
                "⚠ " +
                (result.message ||
                "Something went wrong.");

            message.style.color =
                "#c0392b";
        }


    } catch (error) {

        console.error(
            "Submission error:",
            error
        );

        message.textContent =
            "Unable to connect to the server.";

        message.style.color =
            "#c0392b";
    }

});