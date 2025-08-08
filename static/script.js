document.addEventListener('DOMContentLoaded', () => {
    // --- DOM Elements ---
    const setupSection = document.getElementById('setup-section');
    const lessonSection = document.getElementById('lesson-section');
    const quizSection = document.getElementById('quiz-section');
    const resultSection = document.getElementById('result-section');
    const loadingSpinner = document.getElementById('loading-spinner');

    const generateBtn = document.getElementById('generate-btn');
    const startQuizBtn = document.getElementById('start-quiz-btn');
    const submitAnswerBtn = document.getElementById('submit-answer-btn');
    const restartBtn = document.getElementById('restart-btn');

    const subjectEl = document.getElementById('subject');
    const topicEl = document.getElementById('topic');
    const levelEl = document.getElementById('level');

    const lessonTitleEl = document.getElementById('lesson-title');
    const lessonContentEl = document.getElementById('lesson-content');
    const quizContentEl = document.getElementById('quiz-content');
    const feedbackSectionEl = document.getElementById('feedback-section');
    const resultTextEl = document.getElementById('result-text');

    // --- State Variables ---
    let quizData = null;
    let currentQuestionIndex = 0;
    let score = 0;
    let userSelections = {};

    // --- Functions ---
    const toggleLoading = (isLoading) => {
        loadingSpinner.classList.toggle('hidden', !isLoading);
    };

    const resetUI = () => {
        setupSection.classList.remove('hidden');
        lessonSection.classList.add('hidden');
        quizSection.classList.add('hidden');
        resultSection.classList.add('hidden');
        startQuizBtn.classList.add('hidden');
        feedbackSectionEl.innerHTML = '';
        topicEl.value = '';
        quizData = null;
        currentQuestionIndex = 0;
        score = 0;
    };

    const fetchAPI = async (endpoint, body) => {
        toggleLoading(true);
        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body),
            });
            if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error(`Error fetching from ${endpoint}:`, error);
            alert(`An error occurred. Please check the console and try again.`);
            return null;
        } finally {
            toggleLoading(false);
        }
    };
    
    // --- Event Handlers ---
    generateBtn.addEventListener('click', async () => {
        const subject = subjectEl.value;
        const topic = topicEl.value;
        const level = levelEl.value;

        if (!topic) {
            alert('Please enter a topic.');
            return;
        }
        
        userSelections = { subject, topic, level };

        const data = await fetchAPI('/generate_lesson', userSelections);
        if (data && data.lesson_html) {
            lessonTitleEl.textContent = `Lesson: ${topic}`;
            // Use marked library to parse Markdown to HTML
            lessonContentEl.innerHTML = marked.parse(data.lesson_html);
            setupSection.classList.add('hidden');
            lessonSection.classList.remove('hidden');
            startQuizBtn.classList.remove('hidden');
        }
    });

    startQuizBtn.addEventListener('click', async () => {
        const data = await fetchAPI('/generate_quiz', userSelections);
        if (data && data.questions) {
            quizData = data.questions;
            lessonSection.classList.add('hidden');
            quizSection.classList.remove('hidden');
            displayQuestion();
        }
    });

    const displayQuestion = () => {
        feedbackSectionEl.innerHTML = '';
        submitAnswerBtn.classList.remove('hidden');
        const question = quizData[currentQuestionIndex];
        
        let optionsHTML = '<div class="options-container">';
        question.options.forEach((option, index) => {
            optionsHTML += `
                <div>
                    <input type="radio" id="option${index}" name="quiz_option" value="${option}">
                    <label for="option${index}" class="option-label">${option}</label>
                </div>
            `;
        });
        optionsHTML += '</div>';

        quizContentEl.innerHTML = `
            <p><strong>Question ${currentQuestionIndex + 1}/${quizData.length}:</strong></p>
            <p>${question.question}</p>
            ${optionsHTML}
        `;
    };

    submitAnswerBtn.addEventListener('click', () => {
        const selectedOption = document.querySelector('input[name="quiz_option"]:checked');
        if (!selectedOption) {
            alert('Please select an answer.');
            return;
        }

        const question = quizData[currentQuestionIndex];
        const userAnswer = selectedOption.value;
        
        let feedbackHTML = '';
        if (userAnswer === question.answer) {
            score++;
            feedbackHTML = `<div class="feedback-correct"><strong>Correct!</strong></div>`;
        } else {
            feedbackHTML = `<div class="feedback-incorrect"><strong>Incorrect.</strong> The correct answer is: <strong>${question.answer}</strong></div>`;
        }
        feedbackHTML += `<p><em>Explanation:</em> ${question.explanation}</p>`;
        
        feedbackSectionEl.innerHTML = feedbackHTML;
        submitAnswerBtn.classList.add('hidden');

        // Show next question or results after a delay
        setTimeout(() => {
            currentQuestionIndex++;
            if (currentQuestionIndex < quizData.length) {
                displayQuestion();
            } else {
                showResults();
            }
        }, 2500); // 2.5 second delay
    });

    const showResults = () => {
        quizSection.classList.add('hidden');
        resultSection.classList.remove('hidden');
        const percentage = ((score / quizData.length) * 100).toFixed(1);
        
        let message = `You scored ${score} out of ${quizData.length} (${percentage}%).`;
        if (percentage >= 80) {
            message += "<br>Excellent! You have a strong grasp of this topic.";
        } else if (percentage >= 60) {
            message += "<br>Good job! Review the lesson for any tricky points.";
        } else {
            message += "<br>It's a good start. Let's review the lesson and try again!";
        }
        resultTextEl.innerHTML = message;
    };

    restartBtn.addEventListener('click', resetUI);

    // --- Initial State ---
    resetUI();
});
