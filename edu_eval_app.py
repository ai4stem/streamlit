import streamlit as st
from openai import OpenAI
import os
import json
from dotenv import load_dotenv
import mysql.connector

load_dotenv()  # .env 파일 로드

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
MODEL = 'gpt-4o'
TEMPERATURE = 0.0

# OpenAI API 설정
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# OpenAI 평가 프롬프트 설정
evaluation_prompt = (
    "다음은 인공지능을 이용해 사람과 면담한 기록이야. "
    "질문에 대한 응답 내용을 토대로 면담자가 과학자로서 자질이 있는지 호기심, 문제 해결 능력, 협업 능력, 비판적 사고, 의사소통 능력 5가지에 대해 평가하고 앞으로 발전할 수 있도록 피드백을 제공해. "
)

# MySQL에서 데이터 불러오기 함수
def fetch_records():
    db = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        passwd=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_DATABASE")
    )
    cursor = db.cursor()
    cursor.execute("SELECT id, name, email, time FROM qna")
    records = cursor.fetchall()
    cursor.close()
    db.close()
    return records

# MySQL에서 특정 레코드 불러오기 함수
def fetch_record_by_id(record_id):
    db = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        passwd=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_DATABASE")
    )
    cursor = db.cursor()
    cursor.execute("SELECT chat FROM qna WHERE id = %s", (record_id,))
    record = cursor.fetchone()
    cursor.close()
    db.close()
    return record

# OpenAI GPT-4로 평가 생성 함수
def get_evaluation(chat):
    messages = [{"role": "system", "content": evaluation_prompt}]
    messages += json.loads(chat)
    
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=TEMPERATURE
    )
    
    evaluation = response.choices[0].message.content
    return evaluation

# Streamlit 애플리케이션
st.title("면담 기록 평가")

# 비밀번호 입력
password = st.text_input("비밀번호를 입력하세요", type="password")

if password == os.getenv('PASSWORD'):  # 환경 변수에 저장된 비밀번호와 비교
    # 저장된 레코드 불러오기
    records = fetch_records()

    # 레코드 선택
    record_options = [f"{record[1]} ({record[2]}) - {record[3]}" for record in records]
    selected_record = st.selectbox("평가할 면담 기록을 선택하세요:", record_options)

    # 선택된 레코드 ID 추출
    selected_record_id = records[record_options.index(selected_record)][0]

    # 선택된 학생의 대화 기록 불러오기
    record = fetch_record_by_id(selected_record_id)
    if record:
        chat = json.loads(record[0])
        st.write("### 학생의 대화 기록")
        for message in chat:
            if message["role"] == "user":
                st.write(f"**You:** {message['content']}")
            elif message["role"] == "assistant":
                st.write(f"**ChatGPT:** {message['content']}")

    # 평가 버튼
    if st.button("평가하기"):
        if record:
            evaluation = get_evaluation(record[0])
            st.write("### 평가 결과")
            st.write(evaluation)
        else:
            st.error("선택된 기록을 찾을 수 없습니다.")
else:
    st.error("비밀번호가 틀렸습니다.")
