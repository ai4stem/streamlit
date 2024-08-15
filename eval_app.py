import streamlit as st
from openai import OpenAI
import os
import json
from dotenv import load_dotenv
import mysql.connector
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import markdown

load_dotenv()  # .env 파일 로드

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
MODEL = 'gpt-4o'
TEMPERATURE = 0.0

# OpenAI API 설정
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# 평가 프롬프트 설정
evaluation_prompt_kr = (
    "다음은 인공지능을 이용해 사람과 면담한 기록이야. "
    "질문에 대한 응답 내용을 토대로 면담자의 인공지능 이해 능력, 문제 해결능력, 인공지능 도입에 따른 학습의 본질에 대한 이해에 대해 평가해 줘."
    "각각의 평가 측면에 대해 총평, 장점, 개선할 점 이렇게 3가지로 나눠서 평가 결과를 제시해 줘."
    "장점이나 개선할 점이 없다면 '없음'으로 표시해."
)

evaluation_prompt_en = (
    "The following is a record of an interview conducted using artificial intelligence."
    "Please evaluate the interviewee's understanding of AI, problem-solving skills, and comprehension of the fundamental changes in learning brought about by the introduction of AI, based on their responses to the questions."
    "Please provide the evaluation results by dividing them into three parts: an overall assessment, strengths, and areas for improvement for each aspect of the evaluation."
    "If there are no strengths or areas for improvement, indicate them as 'None'."
)

# 언어 선택 (기본값: 한국어)
language = st.selectbox("언어를 선택하세요 / Please select a language", ("한국어", "English"), index=0)

# 언어에 따른 텍스트 설정
if language == "English":
    evaluation_prompt = evaluation_prompt_en
    title = "Interview Record Evaluation"
    password_label = "Enter your password"
    select_record_label = "Please select the interview record to evaluate:"
    refresh_button_label = "Refresh"
    evaluation_section_title = "Student's Conversation Record"
    evaluate_button_label = "Evaluate"
    send_button_label = "Send"
    success_message = "The evaluation has been successfully sent to"
    error_message = "The selected record could not be found."
    wrong_password_message = "The password is incorrect."
    evaluation_result_title = "### Evaluation Result"
    evaluation_email_subject = "Interview Evaluation Result"
else:
    evaluation_prompt = evaluation_prompt_kr
    title = "면담 기록 평가"
    password_label = "비밀번호를 입력하세요"
    select_record_label = "평가할 면담 기록을 선택하세요:"
    refresh_button_label = "새로고침"
    evaluation_section_title = "학생의 대화 기록"
    evaluate_button_label = "평가하기"
    send_button_label = "전송하기"
    success_message = "평가 결과가 성공적으로 전송되었습니다."
    error_message = "선택된 기록을 찾을 수 없습니다."
    wrong_password_message = "비밀번호가 틀렸습니다."
    evaluation_result_title = "### 평가 결과"
    evaluation_email_subject = "면담 평가 결과"

# MySQL에서 데이터 불러오기 함수
def fetch_records():
    db = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        passwd=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_DATABASE")
    )
    cursor = db.cursor()
    cursor.execute("SELECT id, name, email, time FROM interview")
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
    cursor.execute("SELECT chat, email, name FROM interview WHERE id = %s", (record_id,))
    record = cursor.fetchone()
    cursor.close()
    db.close()
    
    return record

# OpenAI GPT-4로 평가 생성 함수
def get_evaluation(chat):
    messages = [{"role": "system", "content": "You are an expert to evaluate human abilities relevant to AI and Education."}]

    conversation = json.loads(chat)
    # 텍스트로 변환
    text = f"{evaluation_prompt}\n"
    
    for entry in conversation:
        timestamp = entry.get("timestamp", "")
        if entry['role'] == 'system':
            text += f"[System] ({timestamp}): {entry['content']}\n"
        elif entry['role'] == 'user':
            text += f"[User] ({timestamp}): {entry['content']}\n"
        elif entry['role'] == 'assistant':
            text += f"[Assistant] ({timestamp}): {entry['content']}\n"

    messages.append({"role": "user", "content": text})
        
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=TEMPERATURE
    )
    
    evaluation = response.choices[0].message.content
    
    return evaluation

# 이메일로 평가 결과 전송 함수
def send_email(recipient_email, name, subject, body):
    print(recipient_email, name, subject)
    
    sender_email = os.getenv('EMAIL_ADDRESS')
    sender_password = os.getenv('EMAIL_PASSWORD')  # 앱 비밀번호 사용
    
    print(sender_email, sender_password)
    
    # 마크다운을 HTML로 변환
    html_body = markdown.markdown(body)
    
    message = MIMEMultipart("alternative")
    message['From'] = sender_email
    message['To'] = recipient_email
    message['Subject'] = subject
    
    # HTML 메시지 추가
    message.attach(MIMEText(html_body, 'html'))
    
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)  # 앱 비밀번호로 로그인
            server.send_message(message)
            server.quit()
        return True
    except Exception as e:
        st.error(f"이메일을 보내는 동안 오류가 발생했습니다: {str(e)}")
        print("Error occurred while sending an email.")
        return False

# Streamlit 애플리케이션
st.title(title)

# 비밀번호 입력
password = st.text_input(password_label, type="password")

if password == os.getenv('PASSWORD'):  # 환경 변수에 저장된 비밀번호와 비교
    # 세션 상태 초기화
    if 'records' not in st.session_state:
        st.session_state.records = fetch_records()

    # 콤보박스와 새로고침 버튼을 같은 줄에 배치
    st.write(select_record_label)  # 레이블은 별도로 작성
    col1, col2 = st.columns([5, 1])  # 열 비율 조정

    with col1:
        with st.container():
            # 레코드 선택
            record_options = [f"{record[1]} ({record[2]}) - {record[3]}" for record in st.session_state.records]
            selected_record = st.selectbox("", record_options, label_visibility="collapsed")  # 레이블을 빈 문자열로 설정하여 표시되지 않게 함
    
    with col2:
        with st.container():
            # 새로고침 버튼
            if st.button(refresh_button_label):
                st.session_state.records = fetch_records()
                st.rerun()  # 페이지 리로드

    # 선택된 레코드 ID 추출
    selected_record_id = st.session_state.records[record_options.index(selected_record)][0]

    # 선택된 학생의 대화 기록 불러오기
    record = fetch_record_by_id(selected_record_id)
    if record:
        chat, email, name = record
        chat = json.loads(chat)
        st.write(f"### {evaluation_section_title}")
        for message in chat:
            timestamp = message.get("timestamp", "")
            if message["role"] == "user":
                st.write(f"**You** ({timestamp}): {message['content']}")
            elif message["role"] == "assistant":
                st.write(f"**AI** ({timestamp}): {message['content']}")

    # 평가 버튼
    if st.button(evaluate_button_label):
        if record:
            evaluation = get_evaluation(record[0])
            st.session_state['evaluation'] = evaluation  # 세션 상태에 평가 결과 저장
            st.write(evaluation_result_title)
            st.write(evaluation)
            
            print(name)
            print(email)
            print(evaluation)
        else:
            st.error(error_message)

    # 전송하기 버튼
    if 'evaluation' in st.session_state and st.button(send_button_label):
        evaluation = st.session_state['evaluation']
        if send_email(email, name, evaluation_email_subject, evaluation):
            st.success(f"{success_message} {email}.")
else:
    st.error(wrong_password_message)
