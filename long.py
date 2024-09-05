from dotenv import load_dotenv
from datetime import datetime
from openai import OpenAI
import streamlit as st
import mysql.connector
import time
import os
import json

load_dotenv()  # .env 파일 로드

# Database connection parameters
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_DATABASE = os.getenv("DB_DATABASE")

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Initialize session state variables
if 'user_info_submitted' not in st.session_state:
    st.session_state.user_info_submitted = False
if 'user_name' not in st.session_state:
    st.session_state.user_name = ""
if 'user_email' not in st.session_state:
    st.session_state.user_email = ""
if 'learning_phase' not in st.session_state:
    st.session_state.learning_phase = False
if 'recall_phase' not in st.session_state:
    st.session_state.recall_phase = False
if 'test_phase' not in st.session_state:
    st.session_state.test_phase = False
if 'quiz_phase' not in st.session_state:
    st.session_state.quiz_phase = False
if 'quiz_started' not in st.session_state:
    st.session_state.quiz_started = False
if 'quiz_end_time' not in st.session_state:
    st.session_state.quiz_end_time = None
if 'quiz_results' not in st.session_state:
    st.session_state.quiz_results = []
if 'learning_start_time' not in st.session_state:
    st.session_state.learning_start_time = None
if 'recall_start_time' not in st.session_state:
    st.session_state.recall_start_time = None
if 'quiz_start_time' not in st.session_state:
    st.session_state.quiz_start_time = None

# ChatGPT API tools setup
tools = [
    {
        "type": "function",
        "function": {
            "name": "evaluate_answers",
            "description": "Evaluate student's answers about the questions",
            "parameters": {
                "type": "object",
                "properties": {
                    "a1": {"type": "number", "enum": [0, 0.5, 1], "description": "Score for question 1"},
                    "a2": {"type": "number", "enum": [0, 0.5, 1], "description": "Score for question 2"},
                    "a3": {"type": "number", "enum": [0, 0.5, 1], "description": "Score for question 3"},
                    "a4": {"type": "number", "enum": [0, 0.5, 1], "description": "Score for question 4"},
                    "a5": {"type": "number", "enum": [0, 0.5, 1], "description": "Score for question 5"},
                    "a6": {"type": "number", "enum": [0, 0.5, 1], "description": "Score for question 6"},
                    "a7": {"type": "number", "enum": [0, 0.5, 1], "description": "Score for question 7"},
                },
                "required": ["a1", "a2", "a3", "a4", "a5", "a6", "a7"],
            },
        }
    }
]

# 문제 구성
questions = [
    "강화 학습이란 무엇인가요?",
    "강화 학습과 지도 학습의 차이점은 무엇인가요?",
    "강화 학습에서 탐색과 이용의 균형이 중요한 이유는 무엇인가요?",
    "탐색과 이용은 각각 무엇을 의미하나요?",
    "강화 학습은 어떤 분야에서 응용될 수 있나요?",
    "강화 학습의 목적은 무엇인가요?",
    "강화 학습의 예시로 무엇을 들 수 있나요?"
]

# Function to evaluate answers using ChatGPT API
def evaluate_answers_with_chatgpt(text_to_remember, questions, user_answers):
    query = f"다음은 지연 회상 검사를 위한 텍스트야: {text_to_remember}\n"
    query += "위의 텍스트에 대한 질문과 응답은 다음과 같아.\n"

    for i, (question, answer) in enumerate(zip(questions, user_answers), 1):
        query += f"질문 {i}: {question}\n"
        query += f"응답 {i}: {answer}\n"

    query += "각 응답에 대해 맞으면 1, 부분적으로 맞으면 0.5, 틀리면 0으로 평가해 줘."

    messages = [
        {"role": "system", "content": "You are the expert of cognitive science. Don't make assumptions about what values to plug into functions."},
        {"role": "user", "content": query}
    ]

    try:
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=tools,
        )
        
        result = json.loads(resp.choices[0].message.tool_calls[0].function.arguments)
        scores = [result[f'a{i}'] for i in range(1, 8)]
        
        # Print for debugging
        print("API Response:", result)
        print("Extracted Scores:", scores)
        
        return scores
    except Exception as e:
        print(f"Error in API call: {e}")
        return [0] * 7  # Return all zeros in case of error

# None 값을 처리하여 SQL에 저장할 수 있도록 하는 함수
def convert_none_to_null(data):
    return [None if x is None else x for x in data]

# MySQL에 데이터 저장 함수
def save_results_to_db(data):
    # None 값을 NULL로 변환
    data = convert_none_to_null(data)
    print("Data to save in DB:", data)  # 디버깅용 출력

    connection = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_DATABASE
    )
    cursor = connection.cursor()

    try:
        sql = """
        INSERT INTO long_tab (date, name, email, correct_answers, time_taken, answer1, answer2, answer3, answer4, answer5, answer6, answer7,
        correct1, correct2, correct3, correct4, correct5, correct6, correct7)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """
        cursor.execute(sql, data)
        connection.commit()
    finally:
        cursor.close()
        connection.close()

# Streamlit 페이지 기본 설정
st.title("Long-Term Memory Test with Timer")

# 강화 학습 텍스트
text_to_remember = """
강화 학습(reinforcement learning)은 인공지능과 기계 학습의 한 분야로, 컴퓨터 프로그램(에이전트)이 주어진 환경에서 최상의 결정을 내리는 방법을 배우는 과정입니다. 예를 들어, 비디오 게임을 플레이하는 프로그램이 있다고 가정해봅시다. 이 프로그램은 각 게임 상황에서 어떤 행동을 취할지를 결정하고, 그 행동이 얼마나 좋은지에 따라 보상을 받습니다. 강화 학습은 이러한 보상을 최대화하는 행동을 찾는 방법을 학습하는 것입니다.

강화 학습은 일반적인 지도 학습과는 다릅니다. 지도 학습에서는 컴퓨터에게 입력 데이터와 그에 대한 정답을 알려주지만, 강화 학습에서는 에이전트가 스스로 환경과 상호작용하며 정답을 찾아내야 합니다. 예를 들어, 바둑을 두는 인공지능 프로그램은 수많은 게임을 반복하면서 각 수의 결과에 따른 승패를 보상으로 간주하여 가장 승률이 높은 전략을 학습하게 됩니다.

강화 학습의 핵심 개념은 탐색(exploration)과 이용(exploitation)의 균형을 맞추는 것입니다. 탐색은 새로운 행동을 시도해 보는 것이고, 이용은 이미 알고 있는 행동 중 가장 좋은 것을 선택하는 것입니다. 예를 들어, 한 레스토랑을 방문해 만족스러운 식사를 한 경험이 있다면, 계속해서 그 레스토랑을 방문하는 것이 이용에 해당합니다. 하지만 새로운 레스토랑을 시도하는 것은 탐색에 해당합니다. 강화 학습에서는 이러한 탐색과 이용의 균형을 잘 맞추는 것이 중요합니다. 왜냐하면, 새로운 행동을 시도하지 않으면 더 나은 보상을 놓칠 수 있기 때문입니다.

강화 학습은 다양한 분야에서 응용될 수 있습니다. 예를 들어, 로봇 공학에서는 로봇이 복잡한 환경에서 스스로 움직이며 장애물을 피하고 목표 지점에 도달하는 방법을 학습하는 데 사용됩니다. 또한, 자율 주행 자동차도 강화 학습을 통해 도로 상황에 맞게 안전하게 운전하는 방법을 배울 수 있습니다.
"""

# 사용자 정보 입력
if not st.session_state.user_info_submitted:
    st.header("사용자 정보 입력")
    name = st.text_input("이름을 입력하세요:")
    email = st.text_input("이메일을 입력하세요:")

    if st.button("제출") and name and email:
        st.session_state.user_info_submitted = True
        st.session_state.user_name = name
        st.session_state.user_email = email
        st.experimental_rerun()
else:
    st.header(f"환영합니다, {st.session_state.user_name}님!")
    st.write("이 테스트는 장기 기억을 평가하기 위한 지연 회상 과제입니다.")
    st.write("학습한 내용을 기억하고, 일정 시간이 지난 후에 회상해 보세요.")

    # 테스트 시작 버튼
    if st.button("테스트 시작") and not st.session_state.learning_phase:
        st.session_state.learning_phase = True
        st.session_state.learning_start_time = time.time()
        st.experimental_rerun()

    # 학습 단계
    if st.session_state.learning_phase:
        st.write("다음 텍스트를 기억하세요:")
        st.write(text_to_remember)

        learning_duration = 3 * 60 # 총 3분
        start_time = time.time()

        progress_bar = st.progress(0)
        progress_placeholder = st.empty()

        while True:
            elapsed_time = time.time() - start_time
            remaining_time = learning_duration - elapsed_time
            
            if remaining_time <= 0:
                break

            progress = min(elapsed_time / learning_duration, 1.0)
            progress_bar.progress(progress)
            progress_placeholder.text(f"남은 학습 시간: {int(remaining_time) + 1} 초")
            time.sleep(0.1)

        st.session_state.learning_phase = False
        st.session_state.recall_phase = True
        st.session_state.recall_start_time = time.time()
        st.experimental_rerun()

    # 지연 회상 단계
    if st.session_state.recall_phase:
        delay_duration = 20 * 60 # 총 20분
        start_time = time.time()

        progress_bar = st.progress(0)
        progress_placeholder = st.empty()

        while True:
            elapsed_time = time.time() - start_time
            remaining_time = delay_duration - elapsed_time
            
            if remaining_time <= 0:
                break

            progress = min(elapsed_time / delay_duration, 1.0)
            progress_bar.progress(progress)
            progress_placeholder.text(f"지연 남은 시간: {int(remaining_time) + 1} 초")
            time.sleep(0.1)

        st.session_state.recall_phase = False
        st.session_state.quiz_phase = True
        st.experimental_rerun()

    # 문제 풀기 단계
    if st.session_state.quiz_phase and not st.session_state.quiz_started:
        if st.button("문제 풀기"):
            st.session_state.quiz_started = True
            st.session_state.quiz_start_time = time.time()
            st.session_state.quiz_results = []  # 테스트 시작 시 초기화
            st.experimental_rerun()

if st.session_state.quiz_started and st.session_state.quiz_phase:
    st.write("아래 질문에 답하세요:")
    user_inputs = []

    for i, question in enumerate(questions):
        user_answer = st.text_input(question, key=f"question_{i}")
        user_inputs.append(user_answer)

    if st.button("평가하기"):
        st.session_state.quiz_end_time = time.time()

        # Show a loading message
        with st.spinner('답변을 평가하는 중입니다...'):
            # ChatGPT API를 사용하여 답변 평가
            answer_results = evaluate_answers_with_chatgpt(text_to_remember, questions, user_inputs)

        correct_answers = sum(1 for score in answer_results if score == 1)
        partial_answers = sum(1 for score in answer_results if score == 0.5)

        st.write(f"총 {len(questions)}문제 중 맞춘 문항 수: {correct_answers}, 부분 정답 문항 수: {partial_answers}")
        
        # Display individual scores for debugging
        for i, (question, answer, score) in enumerate(zip(questions, user_inputs, answer_results), 1):
            st.write(f"질문 {i}: {question} / 점수: {score}")
        
        total_time = st.session_state.quiz_end_time - st.session_state.quiz_start_time
        st.write(f"문제를 푸는 데 걸린 시간: {total_time:.2f}초")

        data_to_save = (
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            st.session_state.user_name,
            st.session_state.user_email,
            correct_answers,
            round(total_time, 2),
            *user_inputs,
            *answer_results
        )

        save_results_to_db(data_to_save)
        st.success("결과가 성공적으로 저장되었습니다!")

        # 결과 저장 및 초기화
        st.session_state.learning_phase = False
        st.session_state.recall_phase = False
        st.session_state.test_phase = False
        st.session_state.quiz_phase = False
        st.session_state.quiz_started = False

