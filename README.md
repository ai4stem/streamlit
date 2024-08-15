# Conversational Agent for interview with streamlit 

This files are an automated interview system based on LLM (ChatGPT).
본 파일은 ChatGPT를 이용한 자동 면접 및 피드백 시스템입니다.  

<h2>How to use</h2>
<h2>실행 방법</h2>
1. Download the whole files  
해당 파일을 모두 다운로드 받도록 합니다.
2. Move to the downloaded folder and run several code as follows  
해당 폴더로 이동한 뒤, 터미널에서 다음 명령어를 실행합니다:<br><br>
- For interviewee (학생 응답용): <b>streamlit run stream_app.py --server.address 0.0.0.0 --server.port 8503</b><br>
- For interviewer (학생 평가용): <b>streamlit run eval_app.py --server.address 0.0.0.0 --server.port 8504</b><br>

<h2> You should create .env file in order to use the app</h2>
<h2>본 파일을 이용하기 위해서는 .env 파일을 만들어야 합니다.</h2>

The structure of .env (.env 구조)

OPEN_API_KEY=your key  
PASSWORD=your password  
DB_HOST=localhost  
DB_USER=username  
DB_PASSWORD=password  
DB_DATABASE=database
GOOGLE_API_KEY=your key
EMAIL_ADDRESS=your email
EMAIL_PASSWORD=16 letters for gmail api

<h2>The app relies on MySQL for storing and retrieval of information</h2>
<h2>본 파일의 저장 및 추출 등은 MySQL을 통해 이뤄집니다.</h2>
