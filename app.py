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

MODEL_NAME = "gemini-1.5-pro"  # Update to your preferred model

st.title("MCQ Generator")
topic = st.text_input("Enter a topic:", placeholder="e.g., Political Theory")

# Display model information


# Initialize session state for MCQs and user answers
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
            # Create model with configuration
            model = genai.GenerativeModel(
                model_name=MODEL_NAME,
                generation_config=generation_config,
            )

            # Improved prompt with strict formatting
            prompt = f"""Generate 10 high-quality multiple choice questions about {topic}.
            Follow these rules STRICTLY:
            1. Format each question EXACTLY like this:
                Q1) [Question text]
                A) [Option 1]
                B) [Option 2]
                C) [Option 3]
                D) [Option 4]
                Answer: [Letter]
                
            2. Questions should cover different aspects of {topic}
            3. Options must be plausible but only one correct answer
            4. Avoid repeating question patterns
            5. Include both conceptual and practical questions"""

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
    st.subheader(f"Generated MCQs about {topic}")
    score = 0
    for idx, mcq in enumerate(st.session_state["mcqs"]):
        st.write(f"**Q{idx + 1}. {mcq['question']}**")
        
        # Create a list of options with both the letter and the text
        options = [f"{chr(65 + i)}. {mcq['options'][i]}" for i in range(4)]  # A, B, C, D
        options.insert(0, "Select an option")  # Add the default option
        
        # Display the radio button with the options
        selected_option = st.radio(
            f"Choose an option for Q{idx + 1}:",
            options=options,
            index=0,  # Default to "Select an option"
            key=f"q{idx + 1}"
        )
        
        # Extract the selected letter (A, B, C, D) from the selected option
        if selected_option and selected_option != "Select an option":
            selected_letter = selected_option.split(".")[0]  # Extract the letter (A, B, C, D)
            st.session_state["user_answers"][f"q{idx + 1}"] = selected_letter
            
            # Check if the selected answer is correct
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