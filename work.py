import streamlit as st
import random
import time
import re
import json
import mysql.connector
from datetime import datetime
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Database connection parameters
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_DATABASE = os.getenv("DB_DATABASE")

class DigitSpanTest:
    FORWARD = 0
    BACKWARD = 1

    def __init__(self, starting_length=3, symbols=None):
        self.length = starting_length - 1  # Subtract 1 to start from the correct length
        self.symbols = symbols if symbols else ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
        self.sequence = []
        self.next()
        self.max_success_length = 0
        self.max_success_time = 0
        self.correct_attempts = 0
        self.total_attempts = 0
        self.user_activity = []

    def get_sequence(self):
        return self.sequence[:]

    def get_target_sequence(self, mode):
        if mode == self.FORWARD:
            return self.get_sequence()
        elif mode == self.BACKWARD:
            return self.get_sequence()[::-1]
        else:
            raise ValueError(f"Invalid mode '{mode}'.")

    def next(self):
        self.length += 1
        self.sequence = self.generate_sequence()

    def generate_sequence(self):
        return [random.choice(self.symbols) for _ in range(self.length)]

    def record_attempt(self, input_sequence, time_taken, is_correct):
        self.total_attempts += 1
        if is_correct:
            self.correct_attempts += 1
            if self.length > self.max_success_length:
                self.max_success_length = self.length
                self.max_success_time = time_taken
        self.user_activity.append({
            "length": self.length,
            "sequence": ''.join(self.sequence),
            "time_taken": time_taken,
            "input_sequence": input_sequence,
            "is_correct": is_correct
        })

    def get_accuracy(self):
        return self.correct_attempts / self.total_attempts if self.total_attempts > 0 else 0

def save_to_database(name, email, mode, test):
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_DATABASE
        )
        cursor = connection.cursor()

        query = """
        INSERT INTO cog_table (date, name, email, mode, max_success_length, max_success_time, accuracy, user_activity)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            datetime.now(),
            name,
            email,
            mode,
            test.max_success_length,
            test.max_success_time,
            test.get_accuracy(),
            json.dumps(test.user_activity)
        )

        cursor.execute(query, values)
        connection.commit()
        st.success("Results saved successfully to the database!")
        st.info(f"Saved data: Mode: {mode}, Max length: {test.max_success_length}, Accuracy: {test.get_accuracy():.2%}")
    except mysql.connector.Error as error:
        st.error(f"Failed to save results to database: {error}")
        st.warning("Please check your database connection and try again.")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# Streamlit app starts here
st.title("Working Memory Test")

if 'state' not in st.session_state:
    st.session_state['state'] = {
        'user_submitted': False,
        'mode_selected': False,
        'test_started': False,
        'digit_span_test': None,
        'show_sequence': False,
        'sequence_complete': False,
        'current_digit': None,
        'user_input': '',
        'start_time': None,
        'mode': None,
        'input_key': 0  # New: unique key for input field
    }

state = st.session_state['state']

if not state['user_submitted']:
    name = st.text_input("Enter your name")
    email = st.text_input("Enter your email")
    if st.button("Start Test"):
        if name and email:
            state['name'] = name
            state['email'] = email
            state['user_submitted'] = True
            st.experimental_rerun()
        else:
            st.warning("Please enter your name and email before starting the test.")

elif not state['mode_selected']:
    mode = st.selectbox("Choose mode:", options=["Forward", "Backward"], index=0)
    if st.button("Confirm Mode"):
        state['mode'] = "Forward" if mode == "Forward" else "Backward"
        state['mode_selected'] = True
        st.experimental_rerun()

elif not state['test_started']:
    if st.button("Start"):
        state['test_started'] = True
        state['digit_span_test'] = DigitSpanTest(starting_length=3)
        state['show_sequence'] = True
        state['sequence_complete'] = False
        state['user_input'] = ''  # Clear input
        st.experimental_rerun()

else:
    digit_span_test = state['digit_span_test']
    current_sequence = digit_span_test.get_sequence()
    
    if state['show_sequence']:
        st.write("Remember the sequence of numbers:")
        progress_bar = st.progress(0)
        placeholder = st.empty()
        for i, digit in enumerate(current_sequence):
            placeholder.write(digit)
            progress_bar.progress((i + 1) / len(current_sequence))
            time.sleep(1)
            placeholder.empty()  # Clear the number display
        state['show_sequence'] = False
        state['sequence_complete'] = True
        state['user_input'] = ''  # Clear the input
        state['input_key'] += 1  # Increment the input key
        state['start_time'] = time.time()  # Set start_time here
        st.experimental_rerun()

    elif state['sequence_complete']:
        mode_mapping = {"Forward": DigitSpanTest.FORWARD, "Backward": DigitSpanTest.BACKWARD}
        selected_mode = mode_mapping[state['mode']]
        
        # Use a unique key for the input field
        user_input = st.text_input("Enter the sequence:", key=f"user_input_{state['input_key']}")

        if st.button("Submit") or user_input != state['user_input']:
            end_time = time.time()
            if state['start_time'] is None:
                st.error("An error occurred. Please try again.")
                state['start_time'] = time.time()
            else:
                time_taken = end_time - state['start_time']
                
                state['user_input'] = user_input  # Update stored user input
                normalized_input = re.sub(r'[^0-9]', '', user_input)  # Remove all non-digit characters
                target_sequence = ''.join(digit_span_test.get_target_sequence(selected_mode))

                is_correct = normalized_input == target_sequence
                digit_span_test.record_attempt(normalized_input, time_taken, is_correct)

                if is_correct:
                    st.success(f"Correct! Time taken: {time_taken:.2f} seconds. Moving to the next sequence...")
                    digit_span_test.next()
                    state['show_sequence'] = True
                    state['sequence_complete'] = False
                    state['user_input'] = ''  # Clear the input
                    state['input_key'] += 1  # Increment the input key
                    time.sleep(2)  # Give user time to see the success message
                    st.experimental_rerun()
                else:
                    st.error(f"Incorrect. Time taken: {time_taken:.2f} seconds. Try again!")
                    state['start_time'] = time.time()  # Reset start_time for next attempt

        st.write(f"Current sequence length: {digit_span_test.length}")

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Restart from the beginning"):
                state['digit_span_test'] = DigitSpanTest(starting_length=3)
                state['show_sequence'] = True
                state['sequence_complete'] = False
                state['user_input'] = ''  # Clear the input
                state['input_key'] += 1  # Increment the input key
                state['start_time'] = None  # Reset start_time
                st.experimental_rerun()
        with col2:
            if st.button("Retry current sequence"):
                state['show_sequence'] = True
                state['sequence_complete'] = False
                state['user_input'] = ''  # Clear the input
                state['input_key'] += 1  # Increment the input key
                state['start_time'] = None  # Reset start_time
                st.experimental_rerun()
        with col3:
            if st.button("Save Results"):
                with st.spinner('Saving results to database...'):
                    save_to_database(state['name'], state['email'], state['mode'], digit_span_test)

        st.write(f"Max successful length: {digit_span_test.max_success_length}")
        st.write(f"Accuracy: {digit_span_test.get_accuracy():.2%}")