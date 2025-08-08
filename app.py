# app.py

import streamlit as st
import json
import google.generativeai as genai

# --- Configuration and Initialization ---

# Set up the page configuration
st.set_page_config(
    page_title="Interactive Learning Assistant",
    page_icon="🎓",
    layout="wide"
)

# IMPORTANT: Use Streamlit's secrets management for the API key
# Create a file .streamlit/secrets.toml and add your key there:
# GEMINI_API_KEY = "YOUR_API_KEY_HERE"
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
except (KeyError, AttributeError):
    st.error("🚨 Gemini API Key not found! Please add it to your Streamlit secrets.", icon="🚨")
    st.stop()


# Initialize the model (with error handling)
try:
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"Error initializing the model: {e}")
    model = None # Set model to None if initialization fails

# --- Data and Constants ---

SUBJECTS = {
    "Math": ["Algebra", "Geometry", "Calculus", "Statistics", "Trigonometry"],
    "Science": ["Physics", "Chemistry", "Biology", "Astronomy", "Earth Science"],
    "History": ["Ancient History", "World Wars", "American History", "European History", "Asian History"],
    "English": ["Grammar", "Literature", "Writing Skills", "Poetry", "Shakespeare"],
    "Computer Science": ["Programming Basics", "Algorithms", "Web Development", "Data Science", "Artificial Intelligence"]
}

# --- Core Functions (from your original code, with slight modifications) ---

# Use Streamlit's caching to avoid re-running the API call on every interaction
@st.cache_data(show_spinner="Generating your lesson...")
def generate_lesson(topic: str, level: str, subject: str) -> str:
    """Generate a lesson on the given topic."""
    if not model:
        return "Model not initialized. Cannot generate lesson."
    prompt = f"""
    Create a comprehensive lesson on {topic} for a {level} level student.
    Subject: {subject}

    Include:
    1) Clear Learning Objectives
    2) Detailed Explanation with examples (use Markdown and LaTeX for formulas if applicable).
    3) Practical Applications
    4) Summary of Key Concepts
    5) Common mistakes to avoid

    Keep it between 400-500 words and use clear, engaging language. Format the output using Markdown.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"An error occurred while generating the lesson: {e}"

@st.cache_data(show_spinner="Creating your quiz...")
def generate_quiz(topic: str, level: str, subject: str) -> dict:
    """Generate a quiz on the given topic."""
    if not model:
        return {"questions": []} # Return empty quiz if model fails
    prompt = f"""
    Create a 5-question assessment on {topic} ({subject}) for {level} level students.
    Include multiple choice questions with 4 options each.
    Format as a single, valid JSON object with a key "questions" which is a list of question objects.
    Each question object must have these exact keys: "question", "options" (a list of 4 strings), "answer" (the correct string from options), and "explanation".
    Make questions progressively harder.
    """
    try:
        response = model.generate_content(prompt)
        # Clean up the response to ensure it's valid JSON
        json_text = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(json_text)
    except Exception:
         # Fallback in case of API or JSON parsing error
        return {
            "questions": [
                {
                    "question": f"Could not generate a quiz for {topic}. Please try again.",
                    "options": ["N/A", "N/A", "N/A", "N/A"],
                    "answer": "N/A",
                    "explanation": "There was an error communicating with the AI model to generate the quiz."
                }
            ]
        }


# --- Streamlit UI Flow ---

st.title("🎓 Interactive Learning Assistant")
st.markdown("Your personal AI tutor. Choose a subject and topic to get started!")

# Initialize session state to manage the app's flow
if 'stage' not in st.session_state:
    st.session_state.stage = 'selection'
if 'lesson_content' not in st.session_state:
    st.session_state.lesson_content = None
if 'quiz_data' not in st.session_state:
    st.session_state.quiz_data = None


# -- Stage 1: Topic Selection --
if st.session_state.stage == 'selection':
    st.header("1. Choose Your Topic")
    
    # Create columns for a cleaner layout
    col1, col2 = st.columns(2)
    
    with col1:
        subject = st.selectbox("Choose a subject:", list(SUBJECTS.keys()))
        level = st.selectbox("Enter your level:", ["Beginner", "Intermediate", "Advanced"])
    
    with col2:
        # Dynamically update topic options based on subject
        topic_options = SUBJECTS[subject]
        topic = st.text_input("What specific topic?", placeholder=f"e.g., {topic_options[0]}")

    if st.button("Generate Lesson", type="primary"):
        if topic and subject and level and model:
            st.session_state.subject = subject
            st.session_state.level = level
            st.session_state.topic = topic
            st.session_state.lesson_content = generate_lesson(topic, level, subject)
            st.session_state.quiz_data = generate_quiz(topic, level, subject)
            st.session_state.stage = 'lesson'
            st.rerun() # Rerun the script to move to the next stage
        else:
            st.warning("Please fill in all fields before generating a lesson.")

# -- Stage 2: Display Lesson and Offer Quiz --
if st.session_state.stage == 'lesson':
    st.header(f"📚 Lesson: {st.session_state.topic}")
    st.markdown(st.session_state.lesson_content)
    
    st.markdown("---")
    st.info("Read through the lesson. When you're ready, start the quiz to test your knowledge!")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Start Quiz", type="primary"):
            st.session_state.stage = 'quiz'
            st.rerun()
    with col2:
        if st.button("Choose a New Topic"):
             # Reset state by re-initializing stage
            st.session_state.stage = 'selection'
            st.rerun()


# -- Stage 3: Administer Quiz --
if st.session_state.stage == 'quiz':
    st.header(f"📝 Quiz: {st.session_state.topic}")
    quiz = st.session_state.quiz_data
    
    if not quiz or not quiz.get("questions"):
        st.error("Sorry, we couldn't load the quiz. Please go back and try generating the lesson again.")
        if st.button("Go Back"):
            st.session_state.stage = 'selection'
            st.rerun()
    else:
        with st.form("quiz_form"):
            user_answers = []
            for i, q in enumerate(quiz["questions"]):
                options = q.get("options", [])
                # Ensure options are presented in a consistent order
                user_answer = st.radio(f"**Question {i+1}:** {q['question']}", options, key=f"q{i}")
                user_answers.append(user_answer)
            
            submitted = st.form_submit_button("Submit Answers")

            if submitted:
                score = 0
                for i, q in enumerate(quiz["questions"]):
                    if user_answers[i] == q["answer"]:
                        score += 1
                
                st.session_state.score = score
                st.session_state.user_answers = user_answers
                st.session_state.stage = 'results'
                st.rerun()

# -- Stage 4: Show Results --
if st.session_state.stage == 'results':
    st.header("📊 Quiz Results")
    quiz = st.session_state.quiz_data
    score = st.session_state.score
    total_questions = len(quiz['questions'])
    percentage = (score / total_questions) * 100 if total_questions > 0 else 0
    
    # Display score with a progress bar
    st.progress(percentage / 100)
    st.markdown(f"**You scored: {score}/{total_questions} ({percentage:.2f}%)**")
    
    # Provide feedback
    if percentage == 100:
        st.balloons()
        st.success("Excellent! You've mastered this topic.")
    elif percentage >= 60:
        st.info("Good work! Review the explanations below to improve.")
    else:
        st.warning("Let's review the material again. Check the explanations for each question.")
        
    st.markdown("---")
    
    # Display detailed answers and explanations
    st.subheader("Review Your Answers")
    for i, q in enumerate(quiz["questions"]):
        user_ans = st.session_state.user_answers[i]
        correct_ans = q["answer"]
        
        if user_ans == correct_ans:
            st.markdown(f"**Question {i+1}:** {q['question']} - ✅ Correct!")
        else:
            st.markdown(f"**Question {i+1}:** {q['question']} - ❌ Incorrect")
            st.markdown(f"&nbsp;&nbsp;&nbsp;*Your answer: {user_ans}*")
            st.markdown(f"&nbsp;&nbsp;&nbsp;*Correct answer: {correct_ans}*")
        st.info(f"**Explanation:** {q['explanation']}", icon="💡")
        st.markdown("---")
        
    if st.button("Learn Another Topic"):
        st.session_state.stage = 'selection'
        st.rerun()
