# 📚 KSAT English Reading Corpus

한국 고등학교 영어 모의고사 Reading 지문을 수집하고 주제별로 검색·분류하는 개인용 Streamlit 앱입니다.

## 주요 기능

- PDF에서 Reading 지문 추출
- Listening 문항 제외
- 연도 / 학년 / 시험월 / 문항 자동 인식
- 주제 1차 자동 분류
- 여러 PDF를 분석하면 하나의 corpus에 누적
- 동일한 연도·학년·시험·문항의 중복 자동 제거
- 주제별 검색 및 필터링
- 지문 본문 검색
- 분류 결과 수동 수정
- CSV 저장 및 불러오기

## 데이터 구조

각 지문은 다음 정보를 저장합니다.

- year
- grade
- exam
- question
- question_type
- primary_topic
- secondary_topic
- keywords
- passage

## 실행

```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
