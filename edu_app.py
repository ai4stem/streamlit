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

# OpenAI API 키 설정
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# 초기 프롬프트 설정
initial_prompt = (
    "지금부터 고등학생들의 과학자로서의 자질이 있는지 파악하는 질문을 할 거야."
    "먼저 '반갑습니다. 자기 소개를 간단히 해 주세요.' 하고 시작해. "
    "네가 이후 해야 할 면접 주요 과제는 2개야. "
    "첫째 과제는 고등학생 수준에서 경험할 수 있는 실험이나 탐구를 사례로 제시하고 이론과 실험 결과가 불일치할 때 어떻게 대처하는지를 중심으로 질문해. "
    "둘째 과제는 실제 과학자가 되었을 때 경험할 수 있는 상황이나 맥락을 사례로 제시하고 어떻게 행동하거나 대처하는지 질문해. "
    "학생이 과학자로서 자질이 있는지는 호기심, 문제 해결 능력, 협업 능력, 비판적 사고, 의사소통 능력 5가지인데 이 5가지가 잘 표현될 수 있도록 해. "
    "각각의 과제에 대해 사용자와의 대화는 최소한 3회 이상 주고 받을 수 있도록 해 줘."
    "모든 대화가 끝났으면 '수고하셨습니다. 자문을 마치겠습니다.'라고 하고 종료해. 자 이제부터 시작해 봐."
)

# 챗봇 응답 함수
def get_chatgpt_response(prompt):
    st.session_state["messages"].append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        model=MODEL,
        messages=st.session_state["messages"],
    )
    
    answer = response.choices[0].message.content
    print(answer)
    
    st.session_state["messages"].append({"role": "assistant", "content": answer})    

    return answer

# MySQL에 대화 내용 저장 함수
def save_to_db():
    name = st.session_state.get('user_name', '').strip()
    email = st.session_state.get('user_email', '').strip()

    if name == '' or email == '':
        st.error("사용자 이름과 이메일을 입력해야 합니다.")
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
    INSERT INTO qna (name, email, chat, time)
    VALUES (%s, %s, %s, %s)
    """
    chat = json.dumps(st.session_state["messages"])  # 대화 내용을 JSON 문자열로 변환
    val = (name, email, chat, now)
    cursor.execute(sql, val)
    db.commit()
    cursor.close()
    db.close()
    st.success("대화 내용이 저장되었습니다.")


# Streamlit 애플리케이션
st.title("AI 기반 과학자의 자질 평가 사이트")
st.write("LLM을 이용한 피드백 챗봇입니다. 먼저 자신의 이름과 이메일을 입력한 뒤, 정보입력 버튼을 누르면 면접이 시작됩니다. 인공지능이 대화를 모두 마치면 '수고하셨습니다. 면접을 마치겠습니다.'라는 메시지가 나타납니다. 이후 제출하기 버튼을 눌러야 대화가 마무리되며, '대화 내용이 저장되었습니다.'라는 메시지가 뜨면 종료해도 됩니다.")

# 사용자 정보 입력 폼
with st.form(key='user_info_form'):
    user_name = st.text_input("Name", key="user_name")
    user_email = st.text_input("Email", key="user_email")
    user_info_submit = st.form_submit_button(label='정보 입력')

# 대화 기록 초기화
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "system", "content": initial_prompt}]

# Submit 버튼을 눌렀을 때 초기 대화를 시작
if user_info_submit:
    get_chatgpt_response("")

# 대화 기록 출력
if "messages" in st.session_state:
    for message in st.session_state["messages"]:
        if message["role"] == "user":
            st.write(f"You: {message['content']}")
        elif message["role"] == "assistant":
            st.write(f"ChatGPT: {message['content']}")

# 폼을 사용하여 입력 필드와 버튼 그룹화
if "user_name" in st.session_state and "user_email" in st.session_state:
    with st.form(key='my_form', clear_on_submit=True):
        user_input = st.text_area("You: ", key="user_input")
        submit_button = st.form_submit_button(label='Send')

        if submit_button and user_input:
            # 사용자 입력 저장 및 챗봇 응답 생성
            get_chatgpt_response(user_input)
            st.experimental_rerun()  # 상태 업데이트 후 즉시 리렌더링

# "제출하기" 버튼
if "user_name" in st.session_state and "user_email" in st.session_state:
    if st.button("제출하기"):
        save_to_db()

# 새로운 메시지가 추가되면 스크롤을 맨 아래로 이동
st.write('<script>window.scrollTo(0, document.body.scrollHeight);</script>', unsafe_allow_html=True)