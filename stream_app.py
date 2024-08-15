import streamlit as st
from openai import OpenAI
import os
import json
from dotenv import load_dotenv
import mysql.connector
from datetime import datetime

load_dotenv()  # .env 파일 로드

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
MODEL = 'gpt-4o'
TEMPERATURE = 0.0

# OpenAI API 키 설정
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# 초기 프롬프트 설정
initial_prompt_en = (
    "From now on, you will be conducting an interview to assess your ability to integrate and understand concepts related to artificial intelligence, neuroscience, and education."
    "Start by saying, 'Nice to meet you. We will now begin the interview to evaluate your expertise in artificial intelligence as an AI integration and education specialist. Please start by giving a brief introduction of yourself.'"
    "There are three main tasks you need to focus on during the interview."
    "First, ask questions to assess the candidate’s knowledge of AI theories, principles, and concepts. Based on their responses, you need to continue the discussion or questioning at least four times."
    "Second, to evaluate their problem-solving abilities using AI, present a dilemma or crisis scenario related to an educational setting involving AI, and ask how they would resolve it. Again, you should extend the discussion or questioning at least four times based on their answers."
    "Third, to gauge their understanding of the fundamental changes and perspectives on learning as AI is integrated into education, present a specific situation where AI has been introduced into the educational environment. Ask how they would handle the reactions and attitudes of students. Continue the conversation or questioning at least four times based on their responses."
    "Once all conversations are finished, say, 'Thank you for your time. The interview is now concluded.' If at any point they express a desire to stop the interview, you should do so immediately. Now, let's begin."
)

initial_prompt_kr = (
    "지금부터 너는 인공지능과 신경과학, 교육 등을 융합하고 이해하는 역량을 측정하는 면접을 하게 될 거야."
    "먼저 '반갑습니다. 지금부터 인공지능 융합 교육 전문가로서의 인공지능과 관련된 역량을 평가하는 면담을 시작하도록 하겠습니다. 간단한 자기 소개를 해 주세요. 하고 시작해."
    "네가 이후 해야 할 면접의 주요 과제는 3개야."
    "첫째는 인공지능의 이론이나 원리, 개념 등과 관련해 얼마나 지식이 있는지 질문하고 확인해. 사용자의 답변을 기준으로 질문이나 토론을 4번 이상 이어 나가야 해."
    "둘째는 인공지능을 활용한 문제 해결능력을 평가하기 위해 인공지능과 관련된 교육 현장의 딜레마나 위기 상황을 제시하고 이를 어떻게 해결할 수 있는지 물어 봐. 사용자의 답변을 기준으로 질문이나 토론을 4번 이상 이어 나가야 해."
    "셋째는 인공지능이 도입되면서 나타는 본질적 변화와 학습에 대한 관점이 어떠한지 평가하기 위해 인공지능이 교육환경에 도입되었을 때 학생이 보이게 될 반응과 태도에 대해 어떻게 대처하는지 구체적인 상황을 주고 물어 봐. 사용자의 답변을 기준으로 질문이나 토론을 4번 이상 이어 나가야 해."
    "모든 대화가 끝났으면 '수고하셨습니다. 면접을 마치겠습니다.'라고 하고 종료해. 그리고 도중에라도 면접을 그만하고 싶다고 하면 멈춰. 자 이제부터 시작해 봐."
)

# 언어 선택 (기본값: 한국어)
language = st.selectbox("언어를 선택하세요 / Please select a language", ("한국어", "English"), index=0)

# 언어에 따른 초기 프롬프트 및 텍스트 설정
if language == "English":
    initial_prompt = initial_prompt_en
    title = "Interview Bot"
    description = ("This is a chatbot using the OpenAI ChatGPT API. "
                   "Please enter your name and email, and then click the 'Submit Info' button to start the interview. "
                   "After completing the interview, you will see the message 'Thank you for your time. The interview is now concluded.' "
                   "You must click the 'Submit' button to finalize the interview, and once you see the message 'The conversation has been saved.', you may exit.")
    name_label = "Name"
    email_label = "Email"
    info_button = "Submit Info"
    send_button = "Send"
    submit_button_label = "Submit"
    save_message = "The conversation has been saved."
    error_message = "You must enter your name and email."
else:
    initial_prompt = initial_prompt_kr
    title = "인터뷰 챗봇"
    description = ("OpenAI ChatGPT API를 이용한 챗봇입니다. "
                   "먼저 자신의 이름과 이메일을 입력한 뒤, '정보 입력' 버튼을 누르면 면접이 시작됩니다. "
                   "면접을 모두 마치면 '수고하셨습니다. 면접을 마치겠습니다.'라는 메시지가 나타납니다. "
                   "이후 '제출하기' 버튼을 눌러야 면접이 마무리되며, '대화 내용이 저장되었습니다.'라는 메시지가 뜨면 종료해도 됩니다.")
    name_label = "이름"
    email_label = "이메일"
    info_button = "정보 입력"
    send_button = "전송"
    submit_button_label = "제출하기"
    save_message = "대화 내용이 저장되었습니다."
    error_message = "사용자 이름과 이메일을 입력해야 합니다."

# 대화 기록 초기화
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "system", "content": initial_prompt}]
else:
    # 언어가 변경되었을 때 프롬프트를 업데이트
    st.session_state["messages"][0] = {"role": "system", "content": initial_prompt}

# 챗봇 응답 함수
def get_chatgpt_response(prompt):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state["messages"].append({"role": "user", "content": prompt, "timestamp": timestamp})

    response = client.chat.completions.create(
        model=MODEL,
        messages=st.session_state["messages"],
    )
    
    answer = response.choices[0].message.content
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    st.session_state["messages"].append({"role": "assistant", "content": answer, "timestamp": timestamp})    

    return answer

# MySQL에 대화 내용 저장 함수
def save_to_db():
    name = st.session_state.get('user_name', '').strip()
    email = st.session_state.get('user_email', '').strip()

    if name == '' or email == '':
        st.error(error_message)
        return
    
    db = mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        passwd=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_DATABASE")
    )
    cursor = db.cursor()
    now = datetime.now()

    sql = """
    INSERT INTO interview (name, email, chat, time)
    VALUES (%s, %s, %s, %s)
    """
    chat = json.dumps(st.session_state["messages"])  # 대화 내용을 JSON 문자열로 변환
    val = (name, email, chat, now)
    cursor.execute(sql, val)
    db.commit()
    cursor.close()
    db.close()
    st.success(save_message)

# Streamlit 애플리케이션
st.title(title)
st.write(description)

# 사용자 정보 입력 폼
with st.form(key='user_info_form'):
    user_name = st.text_input(name_label, key="user_name")
    user_email = st.text_input(email_label, key="user_email")
    user_info_submit = st.form_submit_button(label=info_button)

# Submit 버튼을 눌렀을 때 초기 대화를 시작
if user_info_submit:
    get_chatgpt_response("")

# 대화 기록 출력
if "messages" in st.session_state:
    for message in st.session_state["messages"]:
        role = message["role"]
        content = message["content"]
        timestamp = message.get("timestamp", "")

        if role == "user":
            st.write(f"**You** ({timestamp}): {content}")
        elif role == "assistant":
            st.write(f"**AI** ({timestamp}): {content}")

# 폼을 사용하여 입력 필드와 버튼 그룹화
if "user_name" in st.session_state and "user_email" in st.session_state:
    with st.form(key='my_form', clear_on_submit=True):
        user_input = st.text_area("You: ", key="user_input")
        send_button_click = st.form_submit_button(label=send_button)

        if send_button_click and user_input:
            # 사용자 입력 저장 및 챗봇 응답 생성
            get_chatgpt_response(user_input)
            st.experimental_rerun()  # 상태 업데이트 후 즉시 리렌더링

# "제출하기" 버튼
if "user_name" in st.session_state and "user_email" in st.session_state:
    if st.button(submit_button_label):  # 여기서 올바르게 라벨 적용
        save_to_db()

# 새로운 메시지가 추가되면 스크롤을 맨 아래로 이동
st.write('<script>window.scrollTo(0, document.body.scrollHeight);</script>', unsafe_allow_html=True)
