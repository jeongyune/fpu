import re
import fitz
import pandas as pd
import streamlit as st


# =========================================================
# 1. 기본 설정
# =========================================================

st.set_page_config(
    page_title="Korean High School English Reading Corpus",
    layout="wide"
)

# 포함 문항: 20~24, 29~42
ALLOWED_QUESTIONS = set(range(20, 24)) | set(range(29, 42))


# =========================================================
# 2. 분류 체계
# =========================================================

TAXONOMY = {
    "Humanities": {
        "Psychology": {
            "Cognitive Psychology": [
                "Memory", "Attention", "Perception", "Reasoning",
                "Cognitive Bias", "Decision Making", "Framing",
                "Confirmation Bias"
            ],
            "Social Psychology": [
                "Conformity", "Group Behavior", "Social Influence",
                "Bystander Effect", "Groupthink", "Social Norms",
                "Interpersonal Relations"
            ],
            "Developmental Psychology": [
                "Child Development", "Attachment", "Language Acquisition",
                "Cognitive Development", "Personality Development", "Aging"
            ],
            "Behavioral Psychology": [
                "Habit", "Conditioning", "Motivation",
                "Reward", "Behavioral Patterns"
            ],
            "Emotion & Well-being": [
                "Emotion", "Stress", "Happiness", "Fear"
            ],
        },
        "Philosophy & Ethics": {
            "Epistemology & Logic": [],
            "Philosophy of Science": [],
            "Ethics": [],
            "Applied Ethics": [],
            "Philosophy of Mind & Human Nature": [],
        },
    },

    "Social Sciences": {
        "Economics": {
            "Behavioral Economics": [],
            "Microeconomics": [],
            "Macroeconomics": [],
            "Market Dynamics": [],
            "International Economics": [],
        },
        "Sociology": {
            "Social Structure": [],
            "Society & Community": [],
            "Social Change": [],
            "Family & Relationships": [],
        },
        "Anthropology": {
            "Cultural Anthropology": [],
            "Linguistic Anthropology": [],
            "Human Evolution Anthropology": [],
        },
        "Political Science & Government": {
            "Political Systems": [],
            "Public Policy": [],
            "Political Behavior": [],
            "International Relations": [],
        },
        "Education": {
            "Learning & Teaching": [],
            "Educational Psychology": [],
            "Education & Society": [],
        },
        "Demography": {
            "Population": [],
        },
    },

    "Business & Management": {
        "Management": {
            "Organizational Behavior": [],
            "HRM": [],
            "Strategy": [],
            "Operations Management": [],
        },
        "Marketing": {
            "Consumer Behavior": [],
            "Advertising": [],
            "Branding": [],
            "Market Research": [],
            "Pricing": [],
            "Social Media Marketing": [],
        },
        "Entrepreneurship": {
            "Startups": [],
            "Entrepreneurs": [],
            "Innovation": [],
            "Risk": [],
            "Business Models": [],
        },
        "Finance & Accounting": {
            "Investment": [],
            "Stocks": [],
            "Banking": [],
            "Corporate Finance": [],
            "Accounting": [],
            "Risk Management": [],
        },
    },

    "Natural Sciences": {
        "Biology & Life Sciences": {
            "Evolutionary Biology": [],
            "Ecology & Biodiversity": [],
            "Genetics": [],
            "Cell Biology": [],
            "Botany": [],
            "Microbiology": [],
            "Animal Behavior": [],
        },
        "Neuroscience": {
            "Neuroplasticity & Brain Function": [],
        },
        "Physics": {
            "Mechanics": [],
            "Thermodynamics": [],
            "Electromagnetism": [],
            "Optics": [],
            "Modern Physics": [],
            "Applied Physics": [],
        },
        "Chemistry": {
            "General Chemistry": [],
            "Physical Chemistry": [],
            "Organic Chemistry": [],
            "Inorganic Chemistry": [],
            "Analytical Chemistry": [],
            "Materials Chemistry": [],
            "Environmental Chemistry": [],
        },
        "Earth Science": {
            "Geology": [],
            "Meteorology": [],
            "Climatology": [],
            "Oceanography": [],
            "Environmental Earth Science": [],
            "Earth History": [],
        },
        "Astronomy & Space Science": {
            "Astronomy": [],
            "Astrophysics": [],
            "Cosmology": [],
            "Space Exploration": [],
        },
    },

    "Medicine & Health": {
        "Human Biology": {},
        "Medicine": {},
        "Public Health": {},
        "Nutrition": {},
        "Medical Technology": {},
    },

    "Technology & Engineering": {
        "Computer Science": {},
        "Engineering": {},
        "Biotechnology": {},
        "Transportation": {},
        "Internet & Digital Technology": {},
        "Technology & Society": {},
    },

    "Environmental Science": {
        "Climate & Climate Change": {},
        "Conservation": {},
        "Pollution": {},
        "Natural Resources": {},
        "Sustainability": {},
    },

    "Linguistics": {
        "Language & Cognition": {},
        "Language Acquisition": {},
        "Sociolinguistics": {},
        "Historical Linguistics": {},
        "Communication": {},
    },

    "Arts & Culture": {
        "Visual Arts": {},
        "Art History": {},
        "Music": {},
        "Film & Media": {},
        "Architecture": {},
        "Aesthetics": {},
    },

    "Literature": {
        "Literary Works": {},
        "Literary Theory": {},
        "Literature & Society": {},
        "Authors & Literary History": {},
    },
}


CONTEXT_KEYWORDS = [
    "Everyday Life",
    "Work",
    "Education",
    "Environment",
    "Technology",
    "Culture",
    "Society",
    "Consumer",
    "Nature",
]


# =========================================================
# 3. PDF 텍스트 추출
# =========================================================

def extract_pdf_text(uploaded_file):
    """PDF 전체에서 텍스트를 추출한다."""
    data = uploaded_file.read()

    doc = fitz.open(stream=data, filetype="pdf")

    pages = []
    for page in doc:
        pages.append(page.get_text("text"))

    return "\n".join(pages)


# =========================================================
# 4. 텍스트 정리
# =========================================================

def clean_text(text):
    """PDF 추출 과정에서 생긴 불필요한 줄을 제거한다."""

    text = text.replace("\r", "\n")

    # 페이지 번호 / 헤더 / 푸터류 제거
    text = re.sub(
        r"^\s*고\d+\s+영어영역.*$",
        "",
        text,
        flags=re.MULTILINE
    )

    text = re.sub(
        r"^\s*영어영역.*$",
        "",
        text,
        flags=re.MULTILINE
    )

    text = re.sub(
        r"^\s*-\s*-+\s*$",
        "",
        text,
        flags=re.MULTILINE
    )

    # 과도한 빈 줄 정리
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


# =========================================================
# 5. 문항 분리
# =========================================================

def split_questions(text):
    """
    1번, 2번 ... 45번 형태의 문항을 분리한다.
    이후 ALLOWED_QUESTIONS에 해당하는 문항만 사용한다.
    """

    pattern = r"(?m)^\s*(\d{1,2})\s*(?=\n|\.)"

    matches = list(re.finditer(pattern, text))

    questions = {}

    for i, match in enumerate(matches):
        number = int(match.group(1))

        if number not in ALLOWED_QUESTIONS:
            continue

        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)

        content = text[start:end].strip()

        if content:
            questions[number] = content

    return questions


# =========================================================
# 6. 선지 분리
# =========================================================

def split_options(text):
    """
    ①~⑤ 선지를 각각 분리한다.
    """

    pattern = r"([①②③④⑤])\s*"

    matches = list(re.finditer(pattern, text))

    options = {
        "①": "",
        "②": "",
        "③": "",
        "④": "",
        "⑤": "",
    }

    if not matches:
        return options, text

    passage_end = matches[0].start()
    main_text = text[:passage_end].strip()

    for i, match in enumerate(matches):
        symbol = match.group(1)
        start = match.end()

        end = (
            matches[i + 1].start()
            if i + 1 < len(matches)
            else len(text)
        )

        options[symbol] = text[start:end].strip()

    return options, main_text


# =========================================================
# 7. 문제 / 지문 분리
# =========================================================

def split_prompt_and_passage(text):
    """
    문제 지시문과 본문을 분리한다.

    일반적인 형태:
    문제...? [몇 점]
    지문...
    """

    # [3점], [2점] 등의 점수 표시
    match = re.search(r"\[\s*\d+\s*점\s*\]", text)

    if match:
        prompt = text[:match.end()].strip()
        passage = text[match.end():].strip()

        return prompt, passage

    # 점수 표시가 없을 경우 첫 번째 물음표 기준
    qmark = text.find("?")

    if qmark != -1:
        prompt = text[:qmark + 1].strip()
        passage = text[qmark + 1:].strip()

        return prompt, passage

    return "", text.strip()


# =========================================================
# 8. 주어진 단어 추출
# =========================================================

def extract_vocab(text):
    """
    지문 뒤쪽의 • / * / · 형태 어휘 목록을 추출한다.
    """

    lines = text.splitlines()

    vocab = []
    passage = []

    for line in lines:
        stripped = line.strip()

        if re.match(r"^[•*·]\s*", stripped):
            vocab.append(
                re.sub(r"^[•*·]\s*", "", stripped)
            )
        else:
            passage.append(line)

    return "\n".join(vocab).strip(), "\n".join(passage).strip()


# =========================================================
# 9. 문항 하나 파싱
# =========================================================

def parse_question(number, raw_text):
    """문항 하나를 구조화한다."""

    options, body = split_options(raw_text)

    prompt, passage = split_prompt_and_passage(body)

    vocab, passage = extract_vocab(passage)

    return {
        "question": number,
        "prompt": prompt,
        "passage": passage,
        "vocab": vocab,
        "option_1": options["①"],
        "option_2": options["②"],
        "option_3": options["③"],
        "option_4": options["④"],
        "option_5": options["⑤"],
    }


# =========================================================
# 10. 자동 분류
# =========================================================

def flatten_taxonomy():
    """분류 체계를 검색하기 쉽게 평탄화한다."""

    result = []

    for domain, fields in TAXONOMY.items():
        for field, subtopics in fields.items():

            if isinstance(subtopics, dict):
                for subtopic in subtopics.keys():
                    result.append((domain, field, subtopic))

            elif isinstance(subtopics, list):
                for subtopic in subtopics:
                    result.append((domain, field, subtopic))

    return result


def classify(text):
    """
    키워드 기반의 1차 자동 분류.
    최종 분류는 사용자가 직접 수정할 수 있다.
    """

    lower = text.lower()

    keyword_map = {
        "psychology": "Psychology",
        "memory": "Cognitive Psychology",
        "attention": "Cognitive Psychology",
        "decision": "Cognitive Psychology",
        "bias": "Cognitive Psychology",
        "conformity": "Social Psychology",
        "group": "Social Psychology",
        "emotion": "Emotion & Well-being",
        "stress": "Emotion & Well-being",
        "happiness": "Emotion & Well-being",
        "motivation": "Behavioral Psychology",

        "economy": "Economics",
        "economic": "Economics",
        "market": "Economics",
        "price": "Economics",
        "consumer": "Marketing",

        "society": "Sociology",
        "social": "Sociology",
        "family": "Sociology",

        "education": "Education",
        "school": "Education",
        "learning": "Education",
        "teacher": "Education",

        "business": "Management",
        "company": "Management",
        "employee": "Management",
        "startup": "Entrepreneurship",
        "investment": "Finance & Accounting",
        "stock": "Finance & Accounting",

        "evolution": "Biology & Life Sciences",
        "gene": "Biology & Life Sciences",
        "cell": "Biology & Life Sciences",
        "species": "Biology & Life Sciences",

        "brain": "Neuroscience",
        "neuron": "Neuroscience",

        "physics": "Physics",
        "energy": "Physics",
        "force": "Physics",
        "light": "Physics",

        "chemical": "Chemistry",
        "molecule": "Chemistry",
        "reaction": "Chemistry",

        "climate": "Climate & Climate Change",
        "pollution": "Pollution",
        "sustainability": "Sustainability",

        "language": "Linguistics",
        "linguistic": "Linguistics",
        "communication": "Communication",

        "art": "Visual Arts",
        "music": "Music",
        "film": "Film & Media",
        "architecture": "Architecture",

        "literature": "Literature",
        "novel": "Literary Works",
        "poem": "Literary Works",
        "author": "Authors & Literary History",
    }

    scores = {}

    for keyword, field in keyword_map.items():
        if keyword in lower:
            scores[field] = scores.get(field, 0) + 1

    if not scores:
        return "", "", "", ""

    best_field = max(scores, key=scores.get)

    for domain, fields in TAXONOMY.items():
        for field, subtopics in fields.items():

            if field == best_field:
                subtopic = ""

                if isinstance(subtopics, dict) and subtopics:
                    subtopic = next(iter(subtopics.keys()))

                elif isinstance(subtopics, list) and subtopics:
                    subtopic = subtopics[0]

                return domain, field, subtopic, ""

    return "", "", "", ""


def infer_context(text):
    """본문에서 Context 후보를 추정한다."""

    lower = text.lower()

    context_keywords = {
        "Everyday Life": ["daily", "everyday", "ordinary"],
        "Work": ["work", "worker", "employee", "workplace"],
        "Education": ["school", "student", "teacher", "education"],
        "Environment": ["environment", "climate", "pollution"],
        "Technology": ["technology", "digital", "computer", "internet"],
        "Culture": ["culture", "cultural", "tradition"],
        "Society": ["society", "social", "community"],
        "Consumer": ["consumer", "shopping", "product", "brand"],
        "Nature": ["nature", "animal", "plant", "ecosystem"],
    }

    found = []

    for context, keywords in context_keywords.items():
        if any(k in lower for k in keywords):
            found.append(context)

    return ", ".join(found)


def infer_question_type(prompt):
    """문제 지시문에서 문항 유형을 추정한다."""

    types = [
        ("요지", "요지"),
        ("주장", "주장"),
        ("제목", "제목"),
        ("주제", "주제"),
        ("목적", "목적"),
        ("빈칸", "빈칸"),
        ("순서", "순서"),
        ("삽입", "삽입"),
        ("무관", "무관한 문장"),
        ("어법", "어법"),
        ("어휘", "어휘"),
    ]

    for keyword, result in types:
        if keyword in prompt:
            return result

    return "미분류"


# =========================================================
# 11. PDF → 데이터베이스
# =========================================================

COLUMNS = [
    "year",
    "grade",
    "exam",
    "question",
    "prompt",
    "passage",
    "vocab",
    "option_1",
    "option_2",
    "option_3",
    "option_4",
    "option_5",
    "question_type",
    "primary_topic",
    "field",
    "subtopic",
    "context",
    "keywords",
]


def analyze_pdf(uploaded_file, year="", grade="", exam=""):
    """PDF를 분석하여 corpus용 DataFrame을 만든다."""

    text = clean_text(extract_pdf_text(uploaded_file))
    questions = split_questions(text)

    rows = []

    for number in sorted(questions):

        parsed = parse_question(
            number,
            questions[number]
        )

        combined_text = (
            parsed["prompt"]
            + "\n"
            + parsed["passage"]
            + "\n"
            + parsed["vocab"]
        )

        domain, field, subtopic, keywords = classify(
            combined_text
        )

        row = {
            "year": year,
            "grade": grade,
            "exam": exam,
            **parsed,
            "question_type": infer_question_type(
                parsed["prompt"]
            ),
            "primary_topic": domain,
            "field": field,
            "subtopic": subtopic,
            "context": infer_context(combined_text),
            "keywords": keywords,
        }

        rows.append(row)

    return pd.DataFrame(rows, columns=COLUMNS)


# =========================================================
# 12. 중복 제거 / 누적
# =========================================================

def make_key(row):
    return (
        str(row["year"]),
        str(row["grade"]),
        str(row["exam"]),
        str(row["question"]),
    )


def merge_corpus(old_df, new_df):
    """새 분석 결과를 기존 결과에 누적한다."""

    if old_df.empty:
        return new_df.copy()

    combined = pd.concat(
        [old_df, new_df],
        ignore_index=True
    )

    combined["_key"] = combined.apply(
        make_key,
        axis=1
    )

    combined = combined.drop_duplicates(
        subset="_key",
        keep="last"
    )

    combined = combined.drop(columns="_key")

    return combined[COLUMNS]


# =========================================================
# 13. Session State
# =========================================================

if "corpus" not in st.session_state:
    st.session_state.corpus = pd.DataFrame(
        columns=COLUMNS
    )


# =========================================================
# 14. 제목
# =========================================================

st.title("Korean High School English Reading Corpus")

st.caption(
    "2006–2026 한국 고등학교 영어 독해 문항 데이터베이스"
)

st.info(
    "수집 문항: 18~24번 + 29~42번 "
    "(1~17, 25~28, 43~45번 제외)"
)


# =========================================================
# 15. 사이드바 — PDF 분석
# =========================================================

st.sidebar.header("PDF 분석")

uploaded_pdf = st.sidebar.file_uploader(
    "시험 PDF 업로드",
    type=["pdf"]
)

year = st.sidebar.text_input(
    "연도",
    placeholder="예: 2026"
)

grade = st.sidebar.text_input(
    "학년",
    placeholder="예: 고2"
)

exam = st.sidebar.text_input(
    "시험",
    placeholder="예: 6월 모의고사"
)


if uploaded_pdf:

    if st.sidebar.button(
        "PDF 분석하기",
        use_container_width=True
    ):

        with st.spinner("PDF 분석 중..."):

            new_df = analyze_pdf(
                uploaded_pdf,
                year,
                grade,
                exam
            )

            st.session_state.corpus = merge_corpus(
                st.session_state.corpus,
                new_df
            )

        st.success(
            f"{len(new_df)}개 문항을 분석했습니다."
        )


# =========================================================
# 16. CSV 불러오기
# =========================================================

st.sidebar.header("데이터 관리")

csv_file = st.sidebar.file_uploader(
    "기존 CSV 불러오기",
    type=["csv"]
)

if csv_file:

    loaded = pd.read_csv(csv_file).fillna("")

    for col in COLUMNS:
        if col not in loaded.columns:
            loaded[col] = ""

    loaded = loaded[COLUMNS]

    st.session_state.corpus = merge_corpus(
        st.session_state.corpus,
        loaded
    )


# =========================================================
# 17. CSV 다운로드
# =========================================================

if not st.session_state.corpus.empty:

    csv_data = st.session_state.corpus.to_csv(
        index=False,
        encoding="utf-8-sig"
    )

    st.sidebar.download_button(
        "현재 데이터 CSV 저장",
        csv_data,
        file_name="korean_english_reading_corpus.csv",
        mime="text/csv",
        use_container_width=True
    )


# =========================================================
# 18. 검색 / 필터
# =========================================================

df = st.session_state.corpus.copy()

if df.empty:

    st.warning(
        "아직 데이터가 없습니다. 왼쪽에서 PDF를 업로드하세요."
    )

    st.stop()


st.header("문항 검색")

search = st.text_input(
    "검색",
    placeholder="지문, 문제, 키워드 등을 검색"
)

col1, col2, col3, col4 = st.columns(4)

with col1:
    year_filter = st.multiselect(
        "연도",
        sorted(
            df["year"].astype(str).unique()
        )
    )

with col2:
    grade_filter = st.multiselect(
        "학년",
        sorted(
            df["grade"].astype(str).unique()
        )
    )

with col3:
    topic_filter = st.multiselect(
        "대분류",
        sorted(
            df["primary_topic"].astype(str).unique()
        )
    )

with col4:
    field_filter = st.multiselect(
        "분야",
        sorted(
            df["field"].astype(str).unique()
        )
    )


if search:

    mask = (
        df.astype(str)
        .apply(
            lambda row: row.str.contains(
                search,
                case=False,
                na=False
            ).any(),
            axis=1
        )
    )

    df = df[mask]


if year_filter:
    df = df[
        df["year"].astype(str).isin(year_filter)
    ]

if grade_filter:
    df = df[
        df["grade"].astype(str).isin(grade_filter)
    ]

if topic_filter:
    df = df[
        df["primary_topic"].astype(str).isin(topic_filter)
    ]

if field_filter:
    df = df[
        df["field"].astype(str).isin(field_filter)
    ]


# =========================================================
# 19. 결과 개수
# =========================================================

st.write(
    f"**{len(df)}개 문항**"
)


# =========================================================
# 20. 문항 표시 + 편집
# =========================================================

for index, row in df.iterrows():

    question_number = int(row["question"])

    title = (
        f"{row['year']} {row['grade']} "
        f"{row['exam']} — {question_number}번"
    )

    with st.expander(title):

        # -------------------------------------------------
        # A. 저장된 결과 미리보기
        # -------------------------------------------------

        st.markdown("### 저장된 문항")

        if row["prompt"]:
            st.markdown(
                f"**문제**  \n{row['prompt']}"
            )

        if row["passage"]:
            st.markdown(
                f"**지문**  \n{row['passage']}"
            )

        if row["vocab"]:
            st.markdown(
                f"**주어진 단어**  \n{row['vocab']}"
            )

        st.markdown("**선지**")

        for i in range(1, 6):
            value = row[f"option_{i}"]

            if value:
                st.markdown(
                    f"**{i}번** {value}"
                )

        st.markdown("**분류**")

        st.write(
            f"- 문제 유형: {row['question_type'] or '미분류'}"
        )

        st.write(
            f"- 대분류: {row['primary_topic'] or '미분류'}"
        )

        st.write(
            f"- 분야: {row['field'] or '미분류'}"
        )

        st.write(
            f"- 세부 주제: {row['subtopic'] or '미분류'}"
        )

        st.write(
            f"- Context: {row['context'] or '없음'}"
        )

        st.write(
            f"- Keywords: {row['keywords'] or '없음'}"
        )


        # -------------------------------------------------
        # B. 편집 영역
        # -------------------------------------------------

        st.divider()

        st.markdown("### 문항 수정")

        new_prompt = st.text_area(
            "문제",
            value=str(row["prompt"]),
            key=f"prompt_{index}",
            height=100
        )

        new_passage = st.text_area(
            "지문",
            value=str(row["passage"]),
            key=f"passage_{index}",
            height=300
        )

        new_vocab = st.text_area(
            "주어진 단어",
            value=str(row["vocab"]),
            key=f"vocab_{index}",
            height=100
        )


        st.markdown("#### 선지")

        option_cols = st.columns(2)

        with option_cols[0]:

            new_option_1 = st.text_input(
                "①",
                value=str(row["option_1"]),
                key=f"option1_{index}"
            )

            new_option_2 = st.text_input(
                "②",
                value=str(row["option_2"]),
                key=f"option2_{index}"
            )

            new_option_3 = st.text_input(
                "③",
                value=str(row["option_3"]),
                key=f"option3_{index}"
            )

        with option_cols[1]:

            new_option_4 = st.text_input(
                "④",
                value=str(row["option_4"]),
                key=f"option4_{index}"
            )

            new_option_5 = st.text_input(
                "⑤",
                value=str(row["option_5"]),
                key=f"option5_{index}"
            )


        # -------------------------------------------------
        # C. 분류 편집
        # -------------------------------------------------

        st.markdown("#### 분류")

        domain_list = list(TAXONOMY.keys())

        current_domain = (
            row["primary_topic"]
            if row["primary_topic"] in domain_list
            else domain_list[0]
        )

        new_domain = st.selectbox(
            "대분류",
            domain_list,
            index=domain_list.index(current_domain),
            key=f"domain_{index}"
        )


        field_list = list(
            TAXONOMY[new_domain].keys()
        )

        current_field = (
            row["field"]
            if row["field"] in field_list
            else field_list[0]
        )

        new_field = st.selectbox(
            "분야",
            field_list,
            index=field_list.index(current_field),
            key=f"field_{index}"
        )


        subtopic_data = TAXONOMY[
            new_domain
        ][new_field]

        if isinstance(subtopic_data, dict):
            subtopic_list = list(
                subtopic_data.keys()
            )
        elif isinstance(subtopic_data, list):
            subtopic_list = subtopic_data
        else:
            subtopic_list = []


        if subtopic_list:

            current_subtopic = (
                row["subtopic"]
                if row["subtopic"] in subtopic_list
                else subtopic_list[0]
            )

            new_subtopic = st.selectbox(
                "세부 주제",
                subtopic_list,
                index=subtopic_list.index(
                    current_subtopic
                ),
                key=f"subtopic_{index}"
            )

        else:

            new_subtopic = st.text_input(
                "세부 주제",
                value=str(row["subtopic"]),
                key=f"subtopic_{index}"
            )


        new_question_type = st.text_input(
            "문제 유형",
            value=str(row["question_type"]),
            key=f"type_{index}"
        )

        new_context = st.text_input(
            "Context",
            value=str(row["context"]),
            key=f"context_{index}",
            placeholder="예: Education, Technology, Society"
        )

        new_keywords = st.text_input(
            "Keywords",
            value=str(row["keywords"]),
            key=f"keywords_{index}",
            placeholder="예: memory, attention, decision making"
        )


        # -------------------------------------------------
        # D. 저장
        # -------------------------------------------------

        if st.button(
            "이 문항 저장",
            key=f"save_{index}",
            type="primary"
        ):

            original_index = st.session_state.corpus.index[
                (
                    st.session_state.corpus["year"].astype(str)
                    == str(row["year"])
                )
                &
                (
                    st.session_state.corpus["grade"].astype(str)
                    == str(row["grade"])
                )
                &
                (
                    st.session_state.corpus["exam"].astype(str)
                    == str(row["exam"])
                )
                &
                (
                    st.session_state.corpus["question"].astype(str)
                    == str(row["question"])
                )
            ]

            if len(original_index) > 0:

                idx = original_index[0]

                st.session_state.corpus.loc[
                    idx, "prompt"
                ] = new_prompt

                st.session_state.corpus.loc[
                    idx, "passage"
                ] = new_passage

                st.session_state.corpus.loc[
                    idx, "vocab"
                ] = new_vocab

                st.session_state.corpus.loc[
                    idx, "option_1"
                ] = new_option_1

                st.session_state.corpus.loc[
                    idx, "option_2"
                ] = new_option_2

                st.session_state.corpus.loc[
                    idx, "option_3"
                ] = new_option_3

                st.session_state.corpus.loc[
                    idx, "option_4"
                ] = new_option_4

                st.session_state.corpus.loc[
                    idx, "option_5"
                ] = new_option_5

                st.session_state.corpus.loc[
                    idx, "question_type"
                ] = new_question_type

                st.session_state.corpus.loc[
                    idx, "primary_topic"
                ] = new_domain

                st.session_state.corpus.loc[
                    idx, "field"
                ] = new_field

                st.session_state.corpus.loc[
                    idx, "subtopic"
                ] = new_subtopic

                st.session_state.corpus.loc[
                    idx, "context"
                ] = new_context

                st.session_state.corpus.loc[
                    idx, "keywords"
                ] = new_keywords

                st.success(
                    f"{question_number}번 문항을 저장했습니다."
                )

                st.rerun()


# =========================================================
# 21. 전체 데이터 요약
# =========================================================

st.divider()

st.header("Corpus Summary")

summary_col1, summary_col2, summary_col3 = st.columns(3)

with summary_col1:
    st.metric(
        "전체 문항",
        len(st.session_state.corpus)
    )

with summary_col2:
    st.metric(
        "대분류",
        st.session_state.corpus[
            "primary_topic"
        ].replace("", pd.NA).nunique()
    )

with summary_col3:
    st.metric(
        "연도",
        st.session_state.corpus[
            "year"
        ].replace("", pd.NA).nunique()
    )
