import re
import io
import pandas as pd
import streamlit as st
import fitz

st.set_page_config(page_title="English Reading Corpus", layout="wide")

# -----------------------------
# Taxonomy
# -----------------------------
TAXONOMY = {
    "Psychology": [
        "Memory", "Cognition", "Decision Making", "Emotion",
        "Social Psychology", "Behavior", "Learning", "Perception"
    ],
    "Biology": [
        "Evolution", "Ecology", "Animal Behavior", "Human Biology",
        "Genetics", "Plants", "Microbiology"
    ],
    "Medicine": [
        "Health", "Disease", "Nutrition", "Medical Technology"
    ],
    "Economics": [
        "Markets", "Behavioral Economics", "Trade", "Money",
        "Incentives", "Business"
    ],
    "Technology": [
        "AI / Computing", "Engineering", "Transportation",
        "Internet / Media", "Technology & Society"
    ],
    "Environment": [
        "Climate", "Conservation", "Pollution", "Natural Resources"
    ],
    "Social Science": [
        "Sociology", "Education", "Politics / Government",
        "Anthropology", "Communication", "Demography"
    ],
    "History": [
        "World History", "Political History", "Social History",
        "Cultural History", "Biography"
    ],
    "Humanities": [
        "Philosophy", "Ethics", "Religion", "Language"
    ],
    "Arts & Literature": [
        "Visual Art", "Music", "Literature", "Architecture"
    ],
    "Geography": [
        "Places & Regions", "Cities", "Population & Geography"
    ],
    "Everyday Life": [
        "Habits", "Relationships", "Work", "Consumer Behavior",
        "Travel", "Lifestyle"
    ],
    "Other": ["Other"]
}

PRIMARY_TOPICS = list(TAXONOMY.keys())

# Keyword-based first-pass classifier.
# This is deliberately editable: it is not presented as a definitive academic classification.
KEYWORDS = {
    "Psychology": ["memory", "cognitive", "decision", "emotion", "behavior", "brain", "perception", "probability", "bias"],
    "Biology": ["evolution", "gene", "genome", "species", "plant", "animal", "organism", "growth", "ecology"],
    "Medicine": ["disease", "patient", "medical", "health", "nutrition", "treatment", "drug", "doctor"],
    "Economics": ["economy", "economic", "market", "price", "cost", "trade", "currency", "consumer", "profit", "demand"],
    "Technology": ["technology", "computer", "internet", "software", "digital", "engineer", "machine", "artificial intelligence"],
    "Environment": ["climate", "environment", "pollution", "conservation", "forest", "ocean", "carbon", "renewable"],
    "Social Science": ["society", "social", "education", "school", "government", "politics", "media", "population", "communication"],
    "History": ["history", "historical", "war", "century", "ancient", "president", "empire", "colonial"],
    "Humanities": ["philosophy", "ethical", "ethics", "moral", "religion", "language", "meaning"],
    "Arts & Literature": ["painting", "artist", "music", "musician", "novel", "poem", "literature", "art", "architecture"],
    "Geography": ["region", "city", "country", "geography", "population", "continent", "urban"],
    "Everyday Life": ["habit", "relationship", "travel", "work", "shopping", "consumer", "family", "restaurant"]
}

def clean_text(text: str) -> str:
    text = text.replace("\u00ad", "")
    text = text.replace("\u2010", "-").replace("\u2011", "-").replace("\u2013", "-")
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"(\w)-\s+(\w)", r"\1\2", text)
    return text.strip()

def extract_pdf_text(uploaded_file):
    data = uploaded_file.getvalue()
    doc = fitz.open(stream=data, filetype="pdf")
    pages = []
    for i, page in enumerate(doc, start=1):
        pages.append((i, page.get_text("text")))
    return pages

def infer_type(block):
    first = block[:500].lower()
    patterns = [
        ("목적", ["목적으로", "purpose"]),
        ("심경/분위기", ["심경", "분위기", "feeling", "mood"]),
        ("주장", ["주장하는", "주장", "claim", "argue"]),
        ("요지", ["요지", "main point"]),
        ("주제", ["주제", "main topic", "theme"]),
        ("제목", ["제목", "title"]),
        ("내용일치", ["내용과 일치", "내용과 일치하지", "consistent", "according to"]),
        ("어법", ["어법상", "grammar"]),
        ("어휘", ["문맥상 낱말", "vocabulary"]),
        ("빈칸", ["빈칸", "blank"]),
        ("순서", ["순서", "order"]),
        ("삽입", ["들어가기에", "insert"]),
        ("무관한 문장", ["관계 없는 문장", "irrelevant"]),
    ]
    for label, keys in patterns:
        if any(k in first for k in keys):
            return label
    return "기타"

def split_questions(full_text):
    # We intentionally start at question 18 for this project.
    # Handles both "18." and line-start variants reasonably well.
    text = full_text
    matches = list(re.finditer(r"(?m)(?:^|\n)\s*(1[89]|[2-9]\d|[1-4]\d|50)\.\s", text))
    matches = [m for m in matches if 18 <= int(m.group(1)) <= 50]
    out = []
    for i, m in enumerate(matches):
        q = int(m.group(1))
        start = m.end()
        end = matches[i+1].start() if i+1 < len(matches) else len(text)
        block = text[start:end].strip()
        if len(block) < 20:
            continue
        out.append((q, clean_text(block)))
    # De-duplicate accidental repeated page/header fragments by question number only
    # while keeping the longest block.
    best = {}
    for q, block in out:
        if q not in best or len(block) > len(best[q]):
            best[q] = block
    return [(q, best[q]) for q in sorted(best)]

def classify(text):
    low = text.lower()
    scores = {}
    for topic, words in KEYWORDS.items():
        scores[topic] = sum(low.count(w.lower()) for w in words)
    topic = max(scores, key=scores.get)
    if scores[topic] == 0:
        topic = "Other"
    confidence = round(min(0.95, 0.35 + scores[topic] * 0.08), 2) if topic != "Other" else 0.20
    return topic, confidence

def make_rows(filename, questions):
    # Try to infer metadata from common Korean filename patterns.
    year = re.search(r"(20\d{2})", filename)
    year = int(year.group(1)) if year else ""
    grade = "고2" if "고2" in filename else ("고1" if "고1" in filename else ("고3" if "고3" in filename else ""))
    month = ""
    for n in [3, 4, 6, 7, 9, 10, 11]:
        if f"{n}월" in filename:
            month = n
            break

    rows = []
    for q, passage in questions:
        topic, conf = classify(passage)
        rows.append({
            "id": f"{year or 'unknown'}_{grade or 'unknown'}_{month or 'unknown'}_{q}",
            "year": year,
            "grade": grade,
            "month": month,
            "question": q,
            "type": infer_type(passage),
            "primary_topic": topic,
            "secondary_topic": "",
            "keywords": "",
            "confidence": conf,
            "passage": passage,
            "source_file": filename
        })
    return rows

# -----------------------------
# UI
# -----------------------------
st.title("📚 Korean High School English Reading Corpus")
st.caption("2006–2026 고1·고2·고3 영어 독해 지문 개인용 데이터베이스")

if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame(columns=[
        "id","year","grade","month","question","type",
        "primary_topic","secondary_topic","keywords",
        "confidence","passage","source_file"
    ])

with st.sidebar:
    st.header("PDF 추가")
    uploaded = st.file_uploader("모의고사 PDF", type=["pdf"])
    if uploaded is not None:
        if st.button("PDF 분석하기", use_container_width=True):
            with st.spinner("PDF에서 텍스트를 추출하고 문항을 나누는 중..."):
                pages = extract_pdf_text(uploaded)
                raw = "\n".join(t for _, t in pages)
                if len(raw.strip()) < 100:
                    st.error("텍스트 레이어가 거의 없습니다. 이 PDF는 OCR이 필요한 스캔형 PDF일 가능성이 있습니다.")
                else:
                    questions = split_questions(raw)
                    rows = make_rows(uploaded.name, questions)
                    if rows:
                        new = pd.DataFrame(rows)
                        st.session_state.df = pd.concat([st.session_state.df, new], ignore_index=True)
                        st.success(f"{len(rows)}개 문항을 추가했습니다.")
                    else:
                        st.error("문항을 찾지 못했습니다. PDF 구조를 확인해야 합니다.")

    st.divider()
    st.header("검색 / 필터")
    search = st.text_input("검색어", "")
    grades = ["전체"] + sorted([x for x in st.session_state.df["grade"].dropna().unique() if x])
    years = ["전체"] + [str(x) for x in sorted([int(x) for x in st.session_state.df["year"].dropna().unique() if str(x).isdigit()])]
    topics = ["전체"] + sorted(st.session_state.df["primary_topic"].dropna().unique().tolist())

    grade_filter = st.selectbox("학년", grades)
    year_filter = st.selectbox("연도", years)
    topic_filter = st.selectbox("주제", topics)

df = st.session_state.df.copy()

if not df.empty:
    if grade_filter != "전체":
        df = df[df.grade == grade_filter]
    if year_filter != "전체":
        df = df[df.year.astype(str) == year_filter]
    if topic_filter != "전체":
        df = df[df.primary_topic == topic_filter]
    if search:
        mask = (
            df["passage"].fillna("").str.contains(search, case=False, regex=False) |
            df["primary_topic"].fillna("").str.contains(search, case=False, regex=False) |
            df["secondary_topic"].fillna("").str.contains(search, case=False, regex=False) |
            df["keywords"].fillna("").str.contains(search, case=False, regex=False)
        )
        df = df[mask]

    st.subheader(f"검색 결과: {len(df)}개")

    for idx, row in df.iterrows():
        title = f"{row['year']} {row['grade']} {row['month']}월 {row['question']}번 · {row['primary_topic']}"
        with st.expander(title):
            c1, c2, c3 = st.columns(3)
            with c1:
                st.write(f"**문항 유형:** {row['type']}")
            with c2:
                st.write(f"**세부 주제:** {row['secondary_topic'] or '미지정'}")
            with c3:
                st.write(f"**분류 신뢰도:** {row['confidence']}")

            st.text_area("지문", row["passage"], height=220, key=f"passage_{idx}")

            new_primary = st.selectbox(
                "대분류",
                PRIMARY_TOPICS,
                index=PRIMARY_TOPICS.index(row["primary_topic"]) if row["primary_topic"] in PRIMARY_TOPICS else len(PRIMARY_TOPICS)-1,
                key=f"primary_{idx}"
            )
            secondary_options = [""] + TAXONOMY[new_primary]
            current_secondary = row["secondary_topic"] if row["secondary_topic"] in secondary_options else ""
            new_secondary = st.selectbox(
                "세부 주제",
                secondary_options,
                index=secondary_options.index(current_secondary),
                key=f"secondary_{idx}"
            )
            new_keywords = st.text_input("키워드 (쉼표로 구분)", row["keywords"], key=f"keywords_{idx}")

            if st.button("태그 저장", key=f"save_{idx}"):
                st.session_state.df.at[idx, "primary_topic"] = new_primary
                st.session_state.df.at[idx, "secondary_topic"] = new_secondary
                st.session_state.df.at[idx, "keywords"] = new_keywords
                st.success("저장했습니다. 화면을 새로고침해도 현재 세션에서는 유지됩니다.")
else:
    st.info("왼쪽에서 PDF를 업로드해 보세요. 먼저 2006 또는 2026 PDF 하나로 테스트하는 것을 추천합니다.")

st.divider()
st.subheader("데이터 관리")

if not st.session_state.df.empty:
    csv = st.session_state.df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "⬇️ 현재 데이터 CSV 다운로드",
        data=csv,
        file_name="english_reading_corpus.csv",
        mime="text/csv"
    )

restore = st.file_uploader("기존 CSV 불러오기", type=["csv"], key="restore")
if restore is not None and st.button("CSV 불러오기"):
    st.session_state.df = pd.read_csv(restore)
    st.success("CSV를 불러왔습니다.")

st.caption("현재 버전은 개인 연구용 프로토타입입니다. 원문 분류 결과는 반드시 직접 검수하세요.")
