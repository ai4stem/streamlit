# streamlit

본 파일은 ChatGPT를 이용한 자동 면접 및 피드백 시스템입니다.  

<h2>실행 방법</h2>
1. 해당 파일을 모두 다운로드 받도록 합니다.
2. 해당 폴더로 이동한 뒤, 터미널에서 다음 명령어를 실행합니다:
- 학생 응답용: <b>streamlit run edu_app.py --server.address 0.0.0.0 --server.port 8503</b>  
- 학생 평가용: <b>streamlit run edu_eval_app.py --server.address 0.0.0.0 --server.port 8504</b>

<h2>본 파일을 이용하기 위해서는 .env 파일을 만들어야 합니다.</h2>
.env 구조

OPEN_API_KEY=your key
PASSWORD=your password
DB_HOST=localhost
DB_USER=username
DB_PASSWORD=password
DB_DATABASE=database

<h2>본 파일의 저장 및 추출 등은 MySQL을 통해 이뤄집니다.</h2>
