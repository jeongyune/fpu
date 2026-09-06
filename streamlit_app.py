import re
from pathlib import Path

import pandas as pd
import streamlit as st

try:
    import fitz
except ImportError:
    fitz = None


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="KSAT English Reading Corpus",
    page_icon="📚",
    layout="wide",
)


# ============================================================
# TAXONOMY
# ============================================================

TAXONOMY = {
    "Psychology": [
        "Memory",
        "Cognition",
        "Decision Making",
        "Emotion",
        "Social Psychology",
        "Behavior",
        "Learning",
        "Perception",
    ],

    "Biology": [
        "Evolution",
        "Ecology",
        "Animal Behavior",
        "Human Biology",
        "Genetics",
        "Plants",
        "Microbiology",
    ],

    "Medicine": [
        "Health",
        "Disease",
        "Nutrition",
        "Medical Technology",
    ],

    "Economics": [
        "Markets",
        "Behavioral Economics",
        "Trade",
        "Money",
        "Incentives",
        "Business",
    ],

    "Technology": [
        "AI/Computing",
        "Engineering",
        "Transportation",
        "Internet/Media",
        "Technology & Society",
    ],

    "Environment": [
        "Climate",
        "Conservation",
        "Pollution",
        "Natural Resources",
    ],

    "Social Science": [
        "Sociology",
        "Education",
        "Politics/Government",
        "Anthropology",
        "Communication",
        "Demography",
    ],

    "History": [
        "World History",
        "Political History",
        "Social History",
        "Cultural History",
        "Biography",
    ],

    "Humanities": [
        "Philosophy",
        "Ethics",
        "Religion",
        "Language",
    ],

    "Arts & Literature": [
        "Visual Art",
        "Music",
        "Literature",
        "Architecture",
    ],

    "Geography": [
        "Places & Regions",
        "Cities",
        "Population & Geography",
    ],

    "Everyday Life": [
        "Habits",
        "Relationships",
        "Work",
        "Consumer Behavior",
        "Travel",
        "Lifestyle",
    ],

    "Other": [],
}


# ============================================================
# KEYWORDS
# ============================================================

KEYWORDS = {
    "Psychology": {
        "Memory": [
            "memory",
            "remember",
            "recall",
            "forget",
        ],

        "Cognition": [
            "cognitive",
            "cognition",
            "attention",
            "reasoning",
            "perception",
        ],

        "Decision Making": [
            "decision",
            "choice",
            "choose",
            "judgment",
        ],

        "Emotion": [
            "emotion",
            "fear",
            "happiness",
            "sadness",
            "stress",
        ],

        "Social Psychology": [
            "social influence",
            "conformity",
            "peer pressure",
            "group",
        ],

        "Behavior": [
            "behavior",
            "behaviour",
            "habit",
        ],

        "Learning": [
            "learn",
            "learning",
            "education",
            "student",
        ],

        "Perception": [
            "perception",
            "visual perception",
            "sensory",
        ],
    },

    "Biology": {
        "Evolution": [
            "evolution",
            "natural selection",
            "adaptation",
            "species",
        ],

        "Ecology": [
            "ecosystem",
            "ecology",
            "predator",
            "food web",
            "habitat",
        ],

        "Animal Behavior": [
            "animal behavior",
            "migration",
            "mating",
            "territory",
        ],

        "Human Biology": [
            "human body",
            "brain",
            "cell",
            "organ",
            "hormone",
        ],

        "Genetics": [
            "gene",
            "genetic",
            "dna",
            "heredity",
        ],

        "Plants": [
            "plant",
            "flower",
            "root",
            "seed",
            "photosynthesis",
        ],

        "Microbiology": [
            "bacteria",
            "virus",
            "microbe",
            "microorganism",
        ],
    },

    "Medicine": {
        "Health": [
            "health",
            "healthy",
            "disease prevention",
        ],

        "Disease": [
            "disease",
            "illness",
            "infection",
            "symptom",
        ],

        "Nutrition": [
            "nutrition",
            "nutrient",
            "diet",
            "calorie",
            "food",
        ],

        "Medical Technology": [
            "medical technology",
            "diagnosis",
            "surgery",
            "medical device",
        ],
    },

    "Economics": {
        "Markets": [
            "market",
            "price",
            "supply",
            "demand",
        ],

        "Behavioral Economics": [
            "behavioral economics",
            "bias",
            "rational",
            "irrational",
        ],

        "Trade": [
            "trade",
            "import",
            "export",
            "tariff",
        ],

        "Money": [
            "money",
            "currency",
            "bank",
            "inflation",
        ],

        "Incentives": [
            "incentive",
            "reward",
            "cost",
            "benefit",
        ],

        "Business": [
            "business",
            "company",
            "firm",
            "consumer",
        ],
    },

    "Technology": {
        "AI/Computing": [
            "artificial intelligence",
            "machine learning",
            "algorithm",
            "computer",
            "computing",
        ],

        "Engineering": [
            "engineering",
            "engineer",
            "design",
            "machine",
        ],

        "Transportation": [
            "transportation",
            "vehicle",
            "car",
            "train",
            "aviation",
        ],

        "Internet/Media": [
            "internet",
            "social media",
            "media",
            "online",
        ],

        "Technology & Society": [
            "technology",
            "technological",
            "digital",
        ],
    },

    "Environment": {
        "Climate": [
            "climate",
            "global warming",
            "greenhouse gas",
        ],

        "Conservation": [
            "conservation",
            "endangered",
            "biodiversity",
        ],

        "Pollution": [
            "pollution",
            "waste",
            "plastic",
            "contamination",
        ],

        "Natural Resources": [
            "natural resource",
            "water",
            "forest",
            "energy",
        ],
    },

    "Social Science": {
        "Sociology": [
            "society",
            "social class",
            "community",
            "institution",
        ],

        "Education": [
            "education",
            "school",
            "teacher",
            "student",
            "curriculum",
        ],

        "Politics/Government": [
            "government",
            "political",
            "president",
            "policy",
            "election",
        ],

        "Anthropology": [
            "anthropology",
            "custom",
            "ritual",
            "culture",
        ],

        "Communication": [
            "communication",
            "conversation",
            "language",
        ],

        "Demography": [
            "population",
            "birth rate",
            "demographic",
            "aging",
        ],
    },

    "History": {
        "World History": [
            "ancient",
            "medieval",
            "empire",
            "war",
            "historical",
        ],

        "Political History": [
            "president",
            "revolution",
            "government",
            "political",
        ],

        "Social History": [
            "workers",
            "class",
            "social history",
        ],

        "Cultural History": [
            "tradition",
            "cultural",
            "culture",
        ],

        "Biography": [
            "born",
            "died",
            "biography",
            "life of",
        ],
    },

    "Humanities": {
        "Philosophy": [
            "philosophy",
            "philosopher",
        ],

        "Ethics": [
            "ethical",
            "ethics",
            "moral",
            "right and wrong",
        ],

        "Religion": [
            "religion",
            "religious",
            "church",
            "god",
        ],

        "Language": [
            "linguistic",
            "grammar",
            "word",
            "language",
        ],
    },

    "Arts & Literature": {
        "Visual Art": [
            "painting",
            "artist",
            "sculpture",
            "artwork",
        ],

        "Music": [
            "music",
            "musician",
            "song",
            "composer",
        ],

        "Literature": [
            "novel",
            "poem",
            "poetry",
            "literature",
            "fiction",
        ],

        "Architecture": [
            "architecture",
            "building",
            "architect",
        ],
    },

    "Geography": {
        "Places & Regions": [
            "region",
            "continent",
            "country",
            "geography",
        ],

        "Cities": [
            "city",
            "urban",
            "town",
        ],

        "Population & Geography": [
            "population",
            "rural",
            "urban",
            "migration",
        ],
    },

    "Everyday Life": {
        "Habits": [
            "habit",
            "routine",
            "daily",
        ],

        "Relationships": [
            "friend",
            "family",
            "relationship",
        ],

        "Work": [
            "work",
            "job",
            "employee",
            "workplace",
        ],

        "Consumer Behavior": [
            "consumer",
            "shopping",
            "purchase",
        ],

        "Travel": [
            "travel",
            "tourist",
            "trip",
            "journey",
        ],

        "Lifestyle": [
            "lifestyle",
            "leisure",
            "hobby",
        ],
    },
}


# ============================================================
# DATA COLUMNS
# ============================================================

COLUMNS = [
    "year",
    "grade",
    "exam",
    "question",
    "question_text",
    "question_type",
    "primary_topic",
    "secondary_topic",
    "keywords",
    "body",
    "reference_words",
    "choices",
]


# ============================================================
# METADATA
# ============================================================

def infer_metadata(filename):

    name = Path(filename).stem

    year_match = re.search(
        r"(20\d{2})",
        name,
    )

    month_match = re.search(
        r"(\d{1,2})월",
        name,
    )

    grade_match = re.search(
        r"고\s*([123])",
        name,
    )

    return {
        "year": (
            int(year_match.group(1))
            if year_match
            else ""
        ),

        "grade": (
            int(grade_match.group(1))
            if grade_match
            else ""
        ),

        "exam": (
            f"{month_match.group(1)}월"
            if month_match
            else ""
        ),
    }


# ============================================================
# CLASSIFICATION
# ============================================================

def classify(text):

    text_lower = str(text).lower()

    hits = []

    for primary, secondary_topics in KEYWORDS.items():

        for secondary, words in secondary_topics.items():

            score = 0

            for word in words:

                score += text_lower.count(
                    word.lower()
                )

            if score > 0:

                hits.append(
                    (
                        score,
                        primary,
                        secondary,
                    )
                )

    hits.sort(
        key=lambda x: x[0],
        reverse=True,
    )

    if not hits:

        return "Other", "", ""

    best_score, best_primary, best_secondary = hits[0]

    related = []

    for score, primary, secondary in hits[1:]:

        if primary == best_primary:

            related.append(
                secondary
            )

        if len(related) >= 2:

            break

    return (
        best_primary,
        best_secondary,
        ", ".join(
            dict.fromkeys(
                related
            )
        ),
    )


# ============================================================
# PDF TEXT EXTRACTION
# ============================================================

def extract_text(uploaded_file):

    if fitz is None:

        raise RuntimeError(
            "PyMuPDF가 설치되지 않았습니다."
        )

    document = fitz.open(
        stream=uploaded_file.getvalue(),
        filetype="pdf",
    )

    pages = []

    for page in document:

        pages.append(
            page.get_text("text")
        )

    text = "\n".join(
        pages
    )

    compact = re.sub(
        r"\s+",
        "",
        text,
    )

    if len(compact) < 200:

        return None

    return text


# ============================================================
# REMOVE PDF PAGE HEADERS / FOOTERS
# ============================================================

def remove_page_headers_footers(text):

    lines = text.splitlines()

    cleaned = []

    for line in lines:

        stripped = line.strip()

        if not stripped:

            cleaned.append("")

            continue

        # 고1/고2/고3 영어영역
        if re.search(
            r"고\s*[123]\s*영어영역",
            stripped,
        ):

            continue

        # 단독 페이지 번호
        if re.fullmatch(
            r"\d{1,3}",
            stripped,
        ):

            continue

        # 긴 선
        if re.fullmatch(
            r"[-_=—–]{5,}",
            stripped,
        ):

            continue

        cleaned.append(
            line
        )

    return "\n".join(
        cleaned
    )


# ============================================================
# QUESTION SPLITTING
#
# Reading:
#   20~42
#
# 제외:
#   1~17
#   18
#   19
#   43
#   44
#   45
# ============================================================

def split_questions(text):

    text = remove_page_headers_footers(
        text
    )

    # 문항 번호가 새로운 줄에 있는 경우
    pattern = (
        r"(?m)^\s*"
        r"(1[89]|[2-4]\d|50)"
        r"\s*[\.\)]?\s+"
    )

    matches = list(
        re.finditer(
            pattern,
            text,
        )
    )

    allowed = set(
        list(range(20, 43))
        + list(range(46, 51))
    )

    valid_matches = []

    for match in matches:

        number = int(
            match.group(1)
        )

        if number in allowed:

            valid_matches.append(
                match
            )

    rows = []

    for i, match in enumerate(
        valid_matches
    ):

        question_number = int(
            match.group(1)
        )

        if i + 1 < len(
            valid_matches
        ):

            end = valid_matches[
                i + 1
            ].start()

        else:

            end = len(text)

        block = text[
            match.end():end
        ].strip()

        if len(block) >= 50:

            rows.append(
                (
                    question_number,
                    block,
                )
            )

    return rows


# ============================================================
# QUESTION TEXT / BODY SPLIT
# ============================================================

def split_question_text_and_body(block):

    block = block.strip()

    # PDF에서 줄바꿈이 사라져도
    # 문제 발문은 대체로 ? 로 끝남.
    #
    # 예:
    # 다음 글에서 필자가 주장하는 바로 가장 적절한 것은? [3점] We can sometimes...
    #
    # -> question_text:
    # 다음 글에서 필자가 주장하는 바로 가장 적절한 것은? [3점]
    #
    # -> body:
    # We can sometimes...

    match = re.search(
        r"(.+?\?)"
        r"\s*"
        r"(\[\s*\d+\s*점\s*\])?"
        r"\s*"
        r"([A-Z][A-Za-z])",
        block,
        flags=re.DOTALL,
    )

    if match:

        question_text = match.group(1).strip()

        score_text = match.group(2)

        body_start = match.start(3)

        body = block[
            body_start:
        ].strip()

        if score_text:

            question_text += (
                " "
                + re.sub(
                    r"\s+",
                    "",
                    score_text,
                )
            )

        return (
            question_text,
            body,
        )

    # --------------------------------------------------------
    # 대체 방법:
    # 첫 번째 ? 를 기준으로 분리
    # --------------------------------------------------------

    question_mark = block.find("?")

    if question_mark != -1:

        question_text = block[
            :question_mark + 1
        ].strip()

        remaining = block[
            question_mark + 1:
        ].strip()

        score_match = re.match(
            r"(\[\s*\d+\s*점\s*\])\s*",
            remaining,
        )

        if score_match:

            question_text += (
                " "
                + re.sub(
                    r"\s+",
                    "",
                    score_match.group(1),
                )
            )

            remaining = remaining[
                score_match.end():
            ].strip()

        return (
            question_text,
            remaining,
        )

    return (
        "",
        block,
    )


# ============================================================
# CHOICE PARSING
# ============================================================

def parse_choices(text):

    # ① ~~~ ② ~~~ ③ ~~~ 형태를
    #
    # ① ~~~
    # ② ~~~
    # ③ ~~~
    #
    # 으로 변경

    text = re.sub(
        r"\s*([①②③④⑤])\s*",
        r"\n\1 ",
        text,
    )

    text = re.sub(
        r"\n{2,}",
        "\n",
        text,
    )

    return text.strip()


# ============================================================
# REFERENCE WORD PARSING
# ============================================================

def parse_reference_words(text):

    text = text.strip()

    # 불필요한 bullet 제거
    text = re.sub(
        r"^[•●▪]\s*",
        "",
        text,
    )

    # 여러 bullet이 붙어 있는 경우
    text = re.sub(
        r"\s*[•●▪]\s*",
        "\n",
        text,
    )

    text = re.sub(
        r"\n{2,}",
        "\n",
        text,
    )

    return text.strip()


# ============================================================
# QUESTION BLOCK PARSER
# ============================================================

def parse_question_block(block):

    block = remove_page_headers_footers(
        block
    )

    block = block.strip()

    # --------------------------------------------------------
    # 문제 발문 / 본문
    # --------------------------------------------------------

    question_text, remaining = (
        split_question_text_and_body(
            block
        )
    )

    # --------------------------------------------------------
    # 선지 찾기
    # --------------------------------------------------------

    choice_match = re.search(
        r"(?<!\S)[①]",
        remaining,
    )

    choices = ""

    if choice_match:

        before_choices = remaining[
            :choice_match.start()
        ]

        choices_part = remaining[
            choice_match.start():
        ]

        choices = parse_choices(
            choices_part
        )

        remaining = (
            before_choices
            .strip()
        )

    # --------------------------------------------------------
    # 참고 영어단어 찾기
    # --------------------------------------------------------

    reference_words = ""

    bullet_match = re.search(
        r"(?m)^\s*[•●▪]\s*",
        remaining,
    )

    if bullet_match:

        body_part = remaining[
            :bullet_match.start()
        ]

        reference_part = remaining[
            bullet_match.start():
        ]

        reference_words = (
            parse_reference_words(
                reference_part
            )
        )

        remaining = body_part.strip()

    else:

        # '참고 영어단어'라는 문구가 있는 경우
        reference_match = re.search(
            r"참고\s*영어\s*단어",
            remaining,
        )

        if reference_match:

            body_part = remaining[
                :reference_match.start()
            ]

            reference_part = remaining[
                reference_match.end():
            ]

            reference_words = (
                parse_reference_words(
                    reference_part
                )
            )

            remaining = body_part.strip()

    # --------------------------------------------------------
    # 본문 정리
    # --------------------------------------------------------

    body = re.sub(
        r"\n{3,}",
        "\n\n",
        remaining,
    ).strip()

    return (
        question_text,
        body,
        reference_words,
        choices,
    )


# ============================================================
# ANALYZE PDF
# ============================================================

def analyze_pdf(uploaded_file):

    metadata = infer_metadata(
        uploaded_file.name
    )

    text = extract_text(
        uploaded_file
    )

    if text is None:

        return (
            None,
            "이 PDF에서는 텍스트를 추출하지 못했습니다. OCR이 필요한 PDF일 수 있습니다.",
        )

    questions = split_questions(
        text
    )

    rows = []

    for question_number, block in questions:

        (
            question_text,
            body,
            reference_words,
            choices,
        ) = parse_question_block(
            block
        )

        primary, secondary, keywords = (
            classify(body)
        )

        rows.append(
            {
                "year": metadata["year"],

                "grade": metadata["grade"],

                "exam": metadata["exam"],

                "question": question_number,

                "question_text": question_text,

                "question_type": "",

                "primary_topic": primary,

                "secondary_topic": secondary,

                "keywords": keywords,

                "body": body,

                "reference_words": reference_words,

                "choices": choices,
            }
        )

    return (
        pd.DataFrame(
            rows,
            columns=COLUMNS,
        ),
        None,
    )


# ============================================================
# NORMALIZE OLD CSV
# ============================================================

def normalize_dataframe(df):

    df = df.copy()

    # 기존 데이터에 question_text가 없으면 생성
    if "question_text" not in df.columns:

        df["question_text"] = ""

        if "passage" in df.columns:

            for idx in df.index:

                old_text = str(
                    df.loc[
                        idx,
                        "passage"
                    ]
                )

                qtext, body = (
                    split_question_text_and_body(
                        old_text
                    )
                )

                df.loc[
                    idx,
                    "question_text"
                ] = qtext

                df.loc[
                    idx,
                    "body"
                ] = body

        else:

            df["question_text"] = ""

    # body가 없는 기존 CSV
    if "body" not in df.columns:

        if "passage" in df.columns:

            df["body"] = (
                df["passage"]
                .fillna("")
            )

        else:

            df["body"] = ""

    # 필요한 컬럼 생성
    for column in COLUMNS:

        if column not in df.columns:

            df[column] = ""

    return df[
        COLUMNS
    ].copy()


# ============================================================
# MERGE CORPUS
# ============================================================

def merge_corpus(
    old_df,
    new_df,
):

    old_df = normalize_dataframe(
        old_df
    )

    new_df = normalize_dataframe(
        new_df
    )

    if old_df.empty:

        return new_df.copy()

    if new_df.empty:

        return old_df.copy()

    combined = pd.concat(
        [
            old_df,
            new_df,
        ],
        ignore_index=True,
    )

    key_columns = [
        "year",
        "grade",
        "exam",
        "question",
    ]

    combined["_unique_key"] = (
        combined[key_columns]
        .astype(str)
        .agg(
            "|".join,
            axis=1,
        )
    )

    combined = (
        combined
        .drop_duplicates(
            "_unique_key",
            keep="last",
        )
        .drop(
            columns="_unique_key"
        )
    )

    return combined[
        COLUMNS
    ].reset_index(
        drop=True
    )


# ============================================================
# SESSION STATE
# ============================================================

if "corpus_df" not in st.session_state:

    st.session_state[
        "corpus_df"
    ] = pd.DataFrame(
        columns=COLUMNS
    )


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.header(
        "📄 PDF 추가"
    )

    uploaded = st.file_uploader(
        "모의고사 PDF",
        type=["pdf"],
    )

    if uploaded:

        if st.button(
            "이 PDF 분석해서 추가",
            type="primary",
            use_container_width=True,
        ):

            with st.spinner(
                "PDF를 분석하고 corpus에 추가하는 중..."
            ):

                try:

                    new_df, error = (
                        analyze_pdf(
                            uploaded
                        )
                    )

                    if error:

                        st.error(
                            error
                        )

                    elif new_df.empty:

                        st.warning(
                            "20~42 또는 46~50번 Reading 지문을 찾지 못했습니다."
                        )

                    else:

                        old_count = len(
                            st.session_state[
                                "corpus_df"
                            ]
                        )

                        st.session_state[
                            "corpus_df"
                        ] = merge_corpus(
                            st.session_state[
                                "corpus_df"
                            ],
                            new_df,
                        )

                        new_count = len(
                            st.session_state[
                                "corpus_df"
                            ]
                        )

                        st.success(
                            f"완료! "
                            f"{new_count - old_count}개 새 지문 추가 / "
                            f"현재 총 {new_count}개"
                        )

                except Exception as error:

                    st.error(
                        f"분석 오류: {error}"
                    )


    st.divider()


    # ========================================================
    # CSV
    # ========================================================

    st.header(
        "💾 저장 / 불러오기"
    )

    csv_file = st.file_uploader(
        "기존 corpus CSV 불러오기",
        type=["csv"],
    )

    if csv_file:

        if st.button(
            "CSV 불러와서 corpus에 합치기",
            use_container_width=True,
        ):

            try:

                loaded = pd.read_csv(
                    csv_file
                )

                loaded = normalize_dataframe(
                    loaded
                )

                st.session_state[
                    "corpus_df"
                ] = merge_corpus(
                    st.session_state[
                        "corpus_df"
                    ],
                    loaded,
                )

                st.success(
                    f"CSV 병합 완료 / "
                    f"현재 총 "
                    f"{len(st.session_state['corpus_df'])}개"
                )

            except Exception as error:

                st.error(
                    f"CSV 오류: {error}"
                )


    if not st.session_state[
        "corpus_df"
    ].empty:

        csv_data = (
            st.session_state[
                "corpus_df"
            ]
            .to_csv(
                index=False
            )
            .encode(
                "utf-8-sig"
            )
        )

        st.download_button(
            "⬇️ 현재 corpus 저장",
            csv_data,
            "ksat_english_corpus.csv",
            "text/csv",
            use_container_width=True,
        )


        st.divider()


        if st.button(
            "⚠️ 현재 corpus 전체 삭제",
            use_container_width=True,
        ):

            st.session_state[
                "corpus_df"
            ] = pd.DataFrame(
                columns=COLUMNS
            )

            st.rerun()


# ============================================================
# MAIN DATA
# ============================================================

df = normalize_dataframe(
    st.session_state[
        "corpus_df"
    ]
)

st.session_state[
    "corpus_df"
] = df


# ============================================================
# HEADER
# ============================================================

st.title(
    "📚 Korean High School English Reading Corpus"
)

st.caption(
    "2006–2026 고1·고2·고3 영어 독해 지문 개인용 데이터베이스"
)


# ============================================================
# EMPTY STATE
# ============================================================

if df.empty:

    st.info(
        "왼쪽에서 모의고사 PDF를 추가하세요."
    )

    st.markdown(
        """
### 자동으로 수집하는 문항

**20~42번 + 46~50번**

### 자동으로 제외하는 문항

**1~17번 Listening**

**18, 19, 43, 44, 45번**

PDF를 여러 번 추가하면 기존 corpus에 계속 누적됩니다.
"""
    )


# ============================================================
# DATA DISPLAY
# ============================================================

else:

    st.success(
        f"현재 corpus: **{len(df)}개 지문**"
    )


    # ========================================================
    # SEARCH / FILTER
    # ========================================================

    st.subheader(
        "🔎 검색 / 필터"
    )

    col1, col2, col3 = st.columns(
        3
    )


    with col1:

        years = sorted(
            {
                str(int(float(v)))
                for v in df["year"]
                if str(v).strip()
                and str(v).replace(
                    ".",
                    "",
                    1,
                ).isdigit()
            }
        )

        selected_year = st.selectbox(
            "연도",
            ["전체"] + years,
        )


    with col2:

        grades = sorted(
            {
                str(int(float(v)))
                for v in df["grade"]
                if str(v).strip()
                and str(v).replace(
                    ".",
                    "",
                    1,
                ).isdigit()
            }
        )

        selected_grade = st.selectbox(
            "학년",
            ["전체"] + grades,
        )


    with col3:

        topics = sorted(
            {
                str(v)
                for v in df[
                    "primary_topic"
                ]
                .fillna("")
                if str(v).strip()
            }
        )

        selected_topic = st.selectbox(
            "주제",
            ["전체"] + topics,
        )


    search = st.text_input(
        "본문 / 문제 / 참고 영어단어 / 선지 검색",
        placeholder=(
            "예: memory, evolution, market..."
        ),
    )


    # ========================================================
    # APPLY FILTER
    # ========================================================

    filtered = df.copy()


    if selected_year != "전체":

        filtered = filtered[
            filtered["year"]
            .astype(str)
            .str.startswith(
                selected_year
            )
        ]


    if selected_grade != "전체":

        filtered = filtered[
            filtered["grade"]
            .astype(str)
            .str.startswith(
                selected_grade
            )
        ]


    if selected_topic != "전체":

        filtered = filtered[
            filtered[
                "primary_topic"
            ]
            == selected_topic
        ]


    if search:

        combined_search = (
            filtered[
                "question_text"
            ].astype(str)
            + " "
            + filtered[
                "body"
            ].astype(str)
            + " "
            + filtered[
                "reference_words"
            ].astype(str)
            + " "
            + filtered[
                "choices"
            ].astype(str)
        )

        mask = combined_search.str.contains(
            search,
            case=False,
            na=False,
        )

        filtered = filtered[
            mask
        ]


    st.write(
        f"**검색 결과 {len(filtered)}개**"
    )

    st.divider()


    # ========================================================
    # QUESTION CARDS
    # ========================================================

    for index, row in filtered.iterrows():

        label = (
            f"Q{row['question']}  ·  "
            f"{row['year']}  ·  "
            f"고{row['grade']}  ·  "
            f"{row['exam']}  ·  "
            f"{row['primary_topic']}"
        )


        with st.expander(
            label,
            expanded=False,
        ):

            # ------------------------------------------------
            # METADATA
            # ------------------------------------------------

            st.caption(
                f"연도: {row['year']}  |  "
                f"학년: 고{row['grade']}  |  "
                f"시험: {row['exam']}  |  "
                f"문항: Q{row['question']}"
            )


            # ------------------------------------------------
            # QUESTION
            # ------------------------------------------------

            if str(
                row["question_text"]
            ).strip():

                st.markdown(
                    "### 문제"
                )

                st.markdown(
                    row[
                        "question_text"
                    ]
                )


            # ------------------------------------------------
            # BODY
            # ------------------------------------------------

            st.markdown(
                "### 본문"
            )

            st.markdown(
                row["body"]
            )


            # ------------------------------------------------
            # REFERENCE WORDS
            # ------------------------------------------------

            if str(
                row[
                    "reference_words"
                ]
            ).strip():

                st.markdown(
                    "### 참고 영어단어"
                )

                reference_lines = (
                    str(
                        row[
                            "reference_words"
                        ]
                    )
                    .splitlines()
                )

                for line in reference_lines:

                    line = line.strip()

                    if line:

                        st.markdown(
                            f"- {line}"
                        )


            # ------------------------------------------------
            # CHOICES
            # ------------------------------------------------

            if str(
                row["choices"]
            ).strip():

                st.markdown(
                    "### 선지"
                )

                choice_lines = (
                    str(
                        row["choices"]
                    )
                    .splitlines()
                )

                for line in choice_lines:

                    line = line.strip()

                    if line:

                        st.markdown(
                            line
                        )


            # ------------------------------------------------
            # TOPIC
            # ------------------------------------------------

            st.markdown(
                f"**Primary Topic:** "
                f"{row['primary_topic']}"
            )

            if str(
                row["secondary_topic"]
            ).strip():

                st.markdown(
                    f"**Secondary Topic:** "
                    f"{row['secondary_topic']}"
                )


            if str(
                row["keywords"]
            ).strip():

                st.caption(
                    f"Keywords: "
                    f"{row['keywords']}"
                )


            st.caption(
                "문항 유형: "
                + (
                    str(
                        row[
                            "question_type"
                        ]
                    )
                    if str(
                        row[
                            "question_type"
                        ]
                    ).strip()
                    else "미분류"
                )
            )


            # =================================================
            # EDIT
            # =================================================

            st.divider()

            st.markdown(
                "## ✏️ 이 지문 수정"
            )


            edited_question = st.text_area(
                "문제",
                value=str(
                    row[
                        "question_text"
                    ]
                ),
                height=100,
                key=f"question_{index}",
            )


            edited_body = st.text_area(
                "본문",
                value=str(
                    row["body"]
                ),
                height=300,
                key=f"body_{index}",
            )


            edited_reference = st.text_area(
                "참고 영어단어",
                value=str(
                    row[
                        "reference_words"
                    ]
                ),
                height=150,
                key=f"reference_{index}",
            )


            edited_choices = st.text_area(
                "선지",
                value=str(
                    row["choices"]
                ),
                height=220,
                key=f"choices_{index}",
                help=(
                    "①, ②, ③, ④, ⑤를 각각 한 줄에 입력하세요."
                ),
            )


            # ------------------------------------------------
            # TOPIC EDIT
            # ------------------------------------------------

            edit_col1, edit_col2 = st.columns(
                2
            )


            with edit_col1:

                primary_options = list(
                    TAXONOMY.keys()
                )

                current_primary = str(
                    row[
                        "primary_topic"
                    ]
                )

                if current_primary not in primary_options:

                    current_primary = (
                        "Other"
                    )

                edited_primary = st.selectbox(
                    "Primary Topic",
                    primary_options,
                    index=primary_options.index(
                        current_primary
                    ),
                    key=f"primary_{index}",
                )


            with edit_col2:

                secondary_options = [
                    ""
                ] + TAXONOMY.get(
                    edited_primary,
                    [],
                )

                current_secondary = str(
                    row[
                        "secondary_topic"
                    ]
                )

                if (
                    current_secondary
                    not in secondary_options
                ):

                    current_secondary = ""

                edited_secondary = st.selectbox(
                    "Secondary Topic",
                    secondary_options,
                    index=secondary_options.index(
                        current_secondary
                    ),
                    key=f"secondary_{index}",
                )


            # ------------------------------------------------
            # SAVE
            # ------------------------------------------------

            if st.button(
                "💾 이 지문 수정 저장",
                key=f"save_{index}",
                type="primary",
            ):

                df.loc[
                    index,
                    "question_text"
                ] = edited_question

                df.loc[
                    index,
                    "body"
                ] = edited_body

                df.loc[
                    index,
                    "reference_words"
                ] = edited_reference

                df.loc[
                    index,
                    "choices"
                ] = edited_choices

                df.loc[
                    index,
                    "primary_topic"
                ] = edited_primary

                df.loc[
                    index,
                    "secondary_topic"
                ] = edited_secondary

                st.session_state[
                    "corpus_df"
                ] = df

                st.success(
                    "수정 사항을 저장했습니다."
                )

                st.rerun()
