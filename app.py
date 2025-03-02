import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os
import re

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini with error handling
try:
    genai.configure(api_key=GOOGLE_API_KEY)
except Exception as e:
    st.error(f"Error configuring Gemini API: {str(e)}")
    st.stop()

# Configure model parameters
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

MODEL_NAME = "gemini-1.5-pro"

st.title("Political Science MCQ Generator")
topic = st.text_input("Enter a topic:", placeholder="e.g., Political Theory")
difficulty = st.selectbox("Select difficulty level:", ["Easy", "Medium", "Hard"], index=0)

# Initialize session state
if "mcqs" not in st.session_state:
    st.session_state["mcqs"] = []

if "user_answers" not in st.session_state:
    st.session_state["user_answers"] = {}

if st.button("Generate MCQs"):
    if not topic:
        st.warning("Please enter a topic first!")
        st.stop()

    with st.spinner("Generating MCQs..."):
        try:
            model = genai.GenerativeModel(
                model_name=MODEL_NAME,
                generation_config=generation_config,
            )

            # Custom prompt based on difficulty level
            prompt = f"""Generate 10 high-quality multiple choice questions about {topic} at {difficulty} difficulty level.
            Follow these rules STRICTLY:
            1. Format each question EXACTLY like this:
                Q1) [Question text]
                A) [Option 1]
                B) [Option 2]
                C) [Option 3]
                D) [Option 4]
                Answer: [Letter]
                
            2. Difficulty levels:
                - Easy: Basic concepts, straightforward answers.
                - Medium: Requires analysis or application of concepts.
                - Hard: Focus on theories, statements, and identifying the correct theorist.
                  - Include quotes or statements and ask whose theory it is.
                  - Include questions about specific political theories and their proponents.
                
            3. Questions should cover different aspects of {topic}.
            4. Options must be plausible but only one correct answer.
            5. Avoid repeating question patterns.
            6. Include both conceptual and practical questions.
            7. Adjust question complexity strictly based on {difficulty} level."""

            response = model.generate_content(prompt)

            if not response.text:
                st.error("No response generated. Please try again.")
            else:
                questions = re.findall(r"(Q\d+\).*?Answer: [A-D])", response.text, re.DOTALL)
                mcqs = []
                for q in questions:
                    match = re.search(r"(Q\d+\))\s*(.*?)(A\))\s*(.*?)(B\))\s*(.*?)(C\))\s*(.*?)(D\))\s*(.*?)(Answer:)\s*([A-D])", q, re.DOTALL)
                    if match:
                        mcqs.append({
                            "question": match.group(2).strip(),
                            "options": [
                                match.group(4).strip(),
                                match.group(6).strip(),
                                match.group(8).strip(),
                                match.group(10).strip(),
                            ],
                            "correct": match.group(12).strip()
                        })

                st.session_state["mcqs"] = mcqs
                st.session_state["user_answers"] = {}

        except Exception as e:
            st.error(f"Error generating MCQs: {str(e)}")
            st.error("Please check your API key and internet connection")

if "mcqs" in st.session_state and st.session_state["mcqs"]:
    st.subheader(f"Generated {difficulty} MCQs about {topic}")
    score = 0
    for idx, mcq in enumerate(st.session_state["mcqs"]):
        st.write(f"**Q{idx + 1}. {mcq['question']}**")
        options = [f"{chr(65 + i)}. {mcq['options'][i]}" for i in range(4)]
        options.insert(0, "Select an option")
        
        selected_option = st.radio(
            f"Choose an option for Q{idx + 1}:",
            options=options,
            index=0,
            key=f"q{idx + 1}"
        )
        
        if selected_option and selected_option != "Select an option":
            selected_letter = selected_option.split(".")[0]
            st.session_state["user_answers"][f"q{idx + 1}"] = selected_letter
            
            if selected_letter == mcq['correct']:
                st.success(f"Correct! ✅ The answer is {mcq['correct']}.")
                score += 1
            else:
                st.error(f"Incorrect ❌. The correct answer is {mcq['correct']}.")
        else:
            st.warning("Please select an option to check your answer.")

        st.markdown("---")

    st.subheader(f"Your Score: {score} / {len(st.session_state['mcqs'])}")
    
st.markdown("---")
st.caption("Powered by Manas Singhal☠️")
