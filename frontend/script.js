const API_URL = "http://127.0.0.1:8000";

let currentQuestion = "";
let currentTopic = "";


// ======================================
// START INTERVIEW
// ======================================

function startInterview() {

    const topicElement =
        document.getElementById("topic");

    if (!topicElement) {
        return;
    }

    currentTopic =
        topicElement.value;

    localStorage.setItem(
        "topic",
        currentTopic
    );

    window.location.href =
        "interview.html";
}


// ======================================
// LOAD QUESTION
// ======================================

async function loadInterview() {

    const questionElement =
        document.getElementById("question");

    if (!questionElement) {
        return;
    }

    currentTopic =
        localStorage.getItem("topic")
        || "General Interview";

    const topicDisplay =
        document.getElementById("topicDisplay");

    if (topicDisplay) {

        topicDisplay.innerText =
            "Interview Topic: " +
            currentTopic;
    }

    questionElement.innerText =
        "🤖 AI is preparing your question...";

    try {

        const response =
            await fetch(
                API_URL + "/api/start",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        topic:
                            currentTopic
                    })
                }
            );

        const data =
            await response.json();

        if (!response.ok) {

            throw new Error(
                data.error ||
                "Unable to generate question"
            );
        }

        if (data.success) {

            currentQuestion =
                data.question;

            questionElement.innerText =
                currentQuestion;

        } else {

            questionElement.innerText =
                "Error: " +
                data.error;
        }

    }

    catch (error) {

        console.error(error);

        questionElement.innerText =
            "❌ " +
            error.message;
    }
}


// ======================================
// SUBMIT ANSWER
// ======================================

async function submitAnswer() {

    const answerElement =
        document.getElementById("answer");

    const result =
        document.getElementById("result");

    if (!answerElement || !result) {
        return;
    }

    const answer =
        answerElement.value.trim();

    if (!answer) {

        result.innerText =
            "⚠️ Please enter your answer.";

        answerElement.focus();

        return;
    }

    if (!currentQuestion) {

        result.innerText =
            "⚠️ No question found.";

        return;
    }


    // Show loading message

    result.innerText =
        "🤖 AI is evaluating your answer...\n\n" +
        "Please wait...";


    try {

        const response =
            await fetch(
                API_URL + "/api/answer",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({

                        topic:
                            currentTopic,

                        question:
                            currentQuestion,

                        answer:
                            answer

                    })
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.error ||
                "Evaluation failed"
            );
        }


        if (data.success) {

            // IMPORTANT:
            // Keep the result on screen.

            result.innerText =
                "🎯 SCORE: " +
                data.score +
                "/10\n\n" +
                data.feedback;


            const nextButton =
                document.getElementById(
                    "nextButton"
                );

            if (nextButton) {

                nextButton.style.display =
                    "block";
            }


            // Scroll to the result

            result.scrollIntoView({
                behavior: "smooth",
                block: "start"
            });

        }

        else {

            result.innerText =
                "❌ Error: " +
                data.error;
        }

    }

    catch (error) {

        console.error(error);

        result.innerText =
            "❌ " +
            error.message;
    }
}


// ======================================
// NEXT QUESTION
// ======================================

function nextQuestion() {

    const answer =
        document.getElementById("answer");

    const result =
        document.getElementById("result");

    const nextButton =
        document.getElementById("nextButton");


    if (answer) {

        answer.value = "";
    }


    if (result) {

        result.innerText = "";
    }


    if (nextButton) {

        nextButton.style.display =
            "none";
    }


    currentQuestion = "";


    loadInterview();
}


// ======================================
// LOAD HISTORY
// ======================================

async function loadHistory() {

    const historyElement =
        document.getElementById("history");

    // IMPORTANT:
    // interview.html does not have #history.
    // Therefore this function stops here.

    if (!historyElement) {

        return;
    }


    historyElement.innerHTML =
        "<p>Loading interview history...</p>";


    try {

        const response =
            await fetch(
                API_URL + "/api/history"
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.error ||
                "Unable to load history"
            );
        }


        // Backend returns:
        //
        // {
        //     success: true,
        //     history: [...]
        // }

        if (
            !data.success ||
            !Array.isArray(data.history) ||
            data.history.length === 0
        ) {

            historyElement.innerHTML =
                "<p>No interviews yet.</p>";

            return;
        }


        historyElement.innerHTML =
            data.history.map(
                function (item) {

                    return `

                    <div class="history-item">

                        <h2>
                            ${escapeHTML(
                                item.topic
                            )}
                        </h2>

                        <p>
                            <strong>
                                Question:
                            </strong>

                            ${escapeHTML(
                                item.question
                            )}
                        </p>

                        <p>
                            <strong>
                                Your Answer:
                            </strong>

                            ${escapeHTML(
                                item.answer
                            )}
                        </p>

                        <p class="score">

                            <strong>
                                Score:
                            </strong>

                            ${item.score}/10

                        </p>

                        <p>

                            <strong>
                                AI Feedback:
                            </strong>

                        </p>

                        <pre class="feedback">${escapeHTML(
                            item.feedback
                        )}</pre>

                        <small>
                            ${escapeHTML(
                                item.created_at
                            )}
                        </small>

                    </div>

                    `;

                }
            ).join("");

    }

    catch (error) {

        console.error(error);

        historyElement.innerHTML =
            "<p>❌ Unable to load history.</p>";
    }
}


// ======================================
// ESCAPE HTML
// ======================================

function escapeHTML(value) {

    if (
        value === null ||
        value === undefined
    ) {

        return "";
    }

    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}


// ======================================
// NAVIGATION
// ======================================

function openHistory() {

    window.location.href =
        "history.html";
}


function goHome() {

    window.location.href =
        "index.html";
}


// ======================================
// PAGE LOAD
// ======================================

window.addEventListener(
    "DOMContentLoaded",
    function () {

        loadInterview();

        loadHistory();

    }
);