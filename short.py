import streamlit as st
import random
import time
import re
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

# 한글 과일 이름 리스트
fruits = [
    "사과", "바나나", "포도", "오렌지", "체리", "복숭아", "레몬", "라임", "멜론", "베리",
    "수박", "딸기", "키위", "자두", "망고", "파인애플", "아보카도", "코코넛", "라즈베리", "블루베리",
    "크랜베리", "구아바", "파파야", "대추", "무화과", "유자", "밤", "감", "귤", "머루",
    "참외", "자몽", "한라봉", "살구", "망고스틴", "두리안", "용과", "호두", "석류", "아몬드"
]

def save_to_database(name, email, correct_count, input_time, correct_words, user_input):
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_DATABASE
        )
        cursor = connection.cursor()

        query = """
        INSERT INTO short_tab (date, name, email, correct_count, input_time, correct_words, user_input)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            datetime.now(),
            name,
            email,
            correct_count,
            input_time,
            ', '.join(correct_words),
            user_input
        )

        cursor.execute(query, values)
        connection.commit()
        return True, "Results submitted and saved successfully to the database!"
    except mysql.connector.Error as error:
        return False, f"Failed to save results to database: {error}"
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

# Streamlit app starts here
st.title("Cognitive Memory Test")

st.markdown("""
<style>
    .stButton>button {
        margin-right: 0px;
    }
    div.row-widget.stRadio > div{
        flex-direction:row;
    }
    .stButton {
        display: flex;
        justify-content: center;
    }
</style>
""", unsafe_allow_html=True)

if 'state' not in st.session_state:
    st.session_state['state'] = {
        'user_submitted': False,
        'name': None,
        'email': None,
        'test_phase': 'start',
        'short_term_words': [],
        'countdown': 30,
        'recall_start_time': None,
        'results': None,
        'submitted': False,
        'submit_message': None
    }

state = st.session_state['state']

if not state['user_submitted']:
    name = st.text_input("Enter your name")
    email = st.text_input("Enter your email")
    if st.button("Proceed"):
        if name and email:
            state['name'] = name
            state['email'] = email
            state['user_submitted'] = True
            st.experimental_rerun()
        else:
            st.warning("Please enter your name and email before proceeding.")
else:
    # Immediate recall test
    if state['test_phase'] == 'start':
        st.write("이 테스트에서는 10개의 과일 이름을 보여드리고, 30초 동안 기억하셔야 합니다.")
        if st.button("테스트 시작"):
            state['short_term_words'] = random.sample(fruits, 10)
            state['test_phase'] = 'show_words'
            st.experimental_rerun()

    elif state['test_phase'] == 'show_words':
        st.write("다음 과일 이름을 기억하세요:")
        st.write(", ".join(state['short_term_words']))

        progress_bar = st.progress(100)
        countdown_placeholder = st.empty()

        for i in range(30, 0, -1):
            countdown_placeholder.write(f"{i}초 남았습니다...")
            progress_bar.progress(i / 30)
            time.sleep(1)
            state['countdown'] = i
            if i == 1:  # Last iteration
                state['test_phase'] = 'recall'
                state['recall_start_time'] = time.time()
        st.experimental_rerun()

    elif state['test_phase'] == 'recall':
        user_input = st.text_area("기억나는 과일 이름을 입력하세요:", value=state['results']['user_input'] if state['results'] else "")

        # 두 개의 컬럼 생성
        col1, col2 = st.columns(2)

        with col1:
            submit_button = st.button("제출")

        with col2:
            restart_button = st.button("테스트 다시 시작")

        if not state['submitted'] and submit_button:
            input_time = time.time() - state['recall_start_time']

            # Process user input
            user_words = set(filter(None, re.split(r'\s|,|\.', user_input)))
            correct_words = set(state['short_term_words'])
            correct_count = len(user_words.intersection(correct_words))

            state['results'] = {
                'correct_count': correct_count,
                'input_time': input_time,
                'correct_words': correct_words,
                'user_input': user_input
            }

            # Save to database
            success, message = save_to_database(
                state['name'], 
                state['email'], 
                correct_count,
                input_time,
                correct_words,
                user_input
            )

            state['submitted'] = True
            state['submit_message'] = message

            st.experimental_rerun()

        if state['results']:
            st.write(f"당신은 {state['results']['correct_count']}개의 과일 이름을 맞췄습니다.")
            st.write(f"정답을 입력하는데 걸린 시간: {state['results']['input_time']:.2f}초")

            if state['submit_message']:
                if state['submitted']:
                    st.success(state['submit_message'])
                else:
                    st.error(state['submit_message'])
                    st.warning("Please check your database connection and try again.")

        if restart_button:
            state['test_phase'] = 'start'
            state['short_term_words'] = []
            state['countdown'] = 30
            state['recall_start_time'] = None
            state['results'] = None
            state['submitted'] = False
            state['submit_message'] = None
            st.experimental_rerun()