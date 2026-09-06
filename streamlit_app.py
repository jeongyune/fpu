import re
from pathlib import Path

import pandas as pd
import streamlit as st

try:
    import fitz
except ImportError:
    fitz = None


# ============================================================
# 기본 설정
# ============================================================

st.set_page_config(
    page_title="KSAT English Reading Corpus",
    page_icon="📚",
    layout="wide",
)


# ============================================================
# 주제 분류 체계
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
# 키워드
# ============================================================

KEYWORDS = {
    "Psychology": {
        "Memory": [
            "memory", "remember", "recall", "forget"
        ],
        "Cognition": [
            "cognitive", "cognition", "attention",
            "reasoning", "perception"
        ],
        "Decision Making": [
            "decision", "choice", "choose", "judgment"
        ],
        "Emotion": [
            "emotion", "fear", "happiness",
            "sadness", "stress"
        ],
        "Social Psychology": [
            "social influence", "conformity",
            "peer pressure", "group"
        ],
        "Behavior": [
            "behavior", "behaviour", "habit"
        ],
        "Learning": [
            "learn", "learning", "education", "student"
        ],
        "Perception": [
            "perception", "visual perception", "sensory"
        ],
    },

    "Biology": {
        "Evolution": [
            "evolution", "natural selection",
            "adaptation", "species"
        ],
        "Ecology": [
            "ecosystem", "ecology", "predator",
            "food web", "habitat"
        ],
        "Animal Behavior": [
            "animal behavior", "migration",
            "mating", "territory"
        ],
        "Human Biology": [
            "human body", "brain", "cell",
            "organ", "hormone"
        ],
        "Genetics": [
            "gene", "genetic", "dna", "heredity"
        ],
        "Plants": [
            "plant", "flower", "root",
            "seed", "photosynthesis"
        ],
        "Microbiology": [
            "bacteria", "virus", "microbe",
            "microorganism"
        ],
    },

    "Medicine": {
        "Health": [
            "health", "healthy", "disease prevention"
        ],
        "Disease": [
            "disease", "illness", "infection", "symptom"
        ],
        "Nutrition": [
            "nutrition", "nutrient", "diet",
            "calorie", "food"
        ],
        "Medical Technology": [
            "medical technology", "diagnosis",
            "surgery", "medical device"
        ],
    },

    "Economics": {
        "Markets": [
            "market", "price", "supply", "demand"
        ],
        "Behavioral Economics": [
            "behavioral economics", "bias",
            "rational", "irrational"
        ],
        "Trade": [
            "trade", "import", "export", "tariff"
        ],
        "Money": [
            "money", "currency", "bank", "inflation"
        ],
        "Incentives": [
            "incentive", "reward", "cost", "benefit"
        ],
        "Business": [
            "business", "company", "firm", "consumer"
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
            "engineering", "engineer",
            "design", "machine"
        ],
        "Transportation": [
            "transportation", "vehicle",
            "car", "train", "aviation"
        ],
        "Internet/Media": [
            "internet", "social media",
            "media", "online"
        ],
        "Technology & Society": [
            "technology", "technological", "digital"
        ],
    },

    "Environment": {
        "Climate": [
            "climate", "global warming",
            "greenhouse gas"
        ],
        "Conservation": [
            "conservation", "endangered",
            "biodiversity"
        ],
        "Pollution": [
            "pollution", "waste",
            "plastic", "contamination"
        ],
        "Natural Resources": [
            "natural resource",
            "water", "forest", "energy"
        ],
    },

    "Social Science": {
        "Sociology": [
            "society", "social class",
            "community", "institution"
        ],
        "Education": [
            "education", "school",
            "teacher", "student", "curriculum"
        ],
        "Politics/Government": [
            "government", "political",
            "president", "policy", "election"
        ],
        "Anthropology": [
            "anthropology", "custom",
            "ritual", "culture"
        ],
        "Communication": [
            "communication",
            "conversation", "language"
        ],
        "Demography": [
            "population", "birth rate",
            "demographic", "aging"
        ],
    },

    "History": {
        "World History": [
            "ancient", "medieval",
            "empire", "war", "historical"
        ],
        "Political History": [
            "president", "revolution",
            "government", "political"
        ],
        "Social History": [
            "workers", "class", "social history"
        ],
        "Cultural History": [
            "tradition", "cultural", "culture"
        ],
        "Biography": [
            "born", "died",
            "biography", "life of"
        ],
    },

    "Humanities": {
        "Philosophy": [
            "philosophy", "philosopher"
        ],
        "Ethics": [
            "ethical", "ethics",
            "moral", "right and wrong"
        ],
        "Religion": [
            "religion", "religious",
            "church", "god"
        ],
        "Language": [
            "linguistic", "grammar",
            "word", "language"
        ],
    },

    "Arts & Literature": {
        "Visual Art": [
            "painting", "artist",
            "sculpture", "artwork"
        ],
        "Music": [
            "music", "musician",
            "song", "composer"
        ],
        "Literature": [
            "novel", "poem",
            "poetry", "literature", "fiction"
        ],
        "Architecture": [
            "architecture",
            "building", "architect"
        ],
    },

    "Geography": {
        "Places & Regions": [
            "region", "continent",
            "country", "geography"
        ],
        "Cities": [
            "city", "urban", "town"
        ],
        "Population & Geography": [
            "population", "rural",
            "urban", "migration"
        ],
    },

    "Everyday Life": {
        "Habits": [
            "habit", "routine", "daily"
        ],
        "Relationships": [
            "friend", "family", "relationship"
        ],
        "Work": [
            "work", "job",
            "employee", "workplace"
        ],
        "Consumer Behavior": [
            "consumer", "shopping", "purchase"
        ],
        "Travel": [
            "travel", "tourist",
            "trip", "journey"
        ],
        "Lifestyle": [
            "lifestyle", "leisure", "hobby"
        ],
    },
}


# ============================================================
# 데이터 구조
# ============================================================

COLUMNS = [
    "year",
    "grade",
    "exam",
    "question",
    "question_type",
    "primary_topic",
    "secondary_topic",
    "keywords",
    "body",
    "reference_words",
    "choices",
]


# ============================================================
# 메타데이터 추출
# ============================================================

def infer_metadata(filename):

    name = Path(filename).stem

    year_match = re.search(
        r"(20\d{2})",
        name
    )

    month_match = re.search(
        r"(\d{1,2})월",
        name
    )

    grade_match = re.search(
        r"고\s*([123])",
        name
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
# 자동 분류
# ============================================================

def classify(text):

    text_lower = text.lower()

    hits = []

    for primary, secondary_topics in KEYWORDS.items():

        for secondary, words in secondary_topics.items():

            score = sum(
                text_lower.count(
                    word.lower()
                )
                for word in words
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
        reverse=True
    )

    if not hits:

        return "Other", "", ""

    best = hits[0]

    related = []

    for item in hits[1:]:

        if item[1] == best[1]:

            related.append(
                item[2]
            )

        if len(related) >= 2:
            break

    return (
        best[1],
        best[2],
        ", ".join(
            dict.fromkeys(related)
        ),
    )


# ============================================================
# PDF 텍스트 추출
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

    if len(
        re.sub(
            r"\s+",
            "",
            text
        )
    ) < 200:

        return None

    return text


# ============================================================
# 페이지 머리말 / 꼬리말 제거
# ============================================================

def remove_page_headers_footers(text):

    lines = text.splitlines()

    cleaned = []

    for line in lines:

        stripped = line.strip()

        if not stripped:
            cleaned.append("")
            continue

        # 예:
        # 고2 영어영역 3
        # 고2 영어영역
        if re.search(
            r"고\s*[123]\s*영어영역",
            stripped
        ):
            continue

        # 페이지 번호처럼 보이는 단독 숫자
        if re.fullmatch(
            r"\d{1,3}",
            stripped
        ):
            continue

        # 긴 선
        if re.fullmatch(
            r"[-_=—–]{5,}",
            stripped
        ):
            continue

        cleaned.append(
            line
        )

    return "\n".join(
        cleaned
    )


# ============================================================
# 문항 분리
#
# 포함:
#   20~42
#   46~50
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

    matches = list(
        re.finditer(
            r"(?m)^\s*(1[89]|[2-4]\d|50)\s*[\.\)]?\s+",
            text,
        )
    )

    allowed = set(
        list(range(20, 43))
        + list(range(46, 51))
    )

    matches = [
        match
        for match in matches
        if int(match.group(1))
        in allowed
    ]

    rows = []

    for i, match in enumerate(matches):

        question = int(
            match.group(1)
        )

        if i + 1 < len(matches):

            end = matches[
                i + 1
            ].start()

        else:

            end = len(text)

        block = text[
            match.end():end
        ].strip()

        if len(block) >= 80:

            rows.append(
                (
                    question,
                    block,
                )
            )

    return rows


# ============================================================
# 문항 블록 정리
#
# 본문
# 참고 영어단어
# 선지
# 로 분리
# ============================================================

def parse_question_block(block):

    block = remove_page_headers_footers(
        block
    )

    # 여러 공백 정리
    block = re.sub(
        r"[ \t]+",
        " ",
        block
    )

    # 앞뒤 빈 줄 정리
    block = block.strip()

    # --------------------------------------------------------
    # 선지 찾기
    # --------------------------------------------------------

    choice_match = re.search(
        r"(?:^|\n|\s)([①②③④⑤])\s*",
        block
    )

    choices = ""

    if choice_match:

        before_choices = block[
            :choice_match.start()
        ]

        choices_part = block[
            choice_match.start():
        ]

        # ① ② ③ ④ ⑤ 앞에 줄바꿈
        choices_part = re.sub(
            r"\s*([①②③④⑤])\s*",
            r"\n\1 ",
            choices_part
        )

        choices = choices_part.strip()

        block = before_choices.strip()

    # --------------------------------------------------------
    # 참고 영어단어 찾기
    # --------------------------------------------------------

    reference_match = re.search(
        r"(?:^|\n|\s)[•●▪]\s*",
        block
    )

    reference_words = ""

    if reference_match:

        body_part = block[
            :reference_match.start()
        ]

        reference_part = block[
            reference_match.start():
        ]

        reference_words = reference_part.strip()

        block = body_part.strip()

    # 일부 PDF에서는 참고 단어가
    # '참고 영어단어'라는 제목으로 추출될 수 있음
    else:

        reference_match = re.search(
            r"참고\s*영어\s*단어",
            block
        )

        if reference_match:

            body_part = block[
                :reference_match.start()
            ]

            reference_part = block[
                reference_match.end():
            ]

            reference_words = (
                reference_part
                .strip()
            )

            block = body_part.strip()

    # --------------------------------------------------------
    # 본문 정리
    # --------------------------------------------------------

    body = re.sub(
        r"\n{3,}",
        "\n\n",
        block
    ).strip()

    # --------------------------------------------------------
    # 참고 단어 정리
    # --------------------------------------------------------

    if reference_words:

        reference_words = re.sub(
            r"\s*([①②③④⑤])\s*",
            r"\n\1 ",
            reference_words
        )

        reference_words = re.sub(
            r"\n{3,}",
            "\n\n",
            reference_words
        ).strip()

    # --------------------------------------------------------
    # 선지 정리
    # --------------------------------------------------------

    if choices:

        choices = re.sub(
            r"\n{3,}",
            "\n\n",
            choices
        ).strip()

    return (
        body,
        reference_words,
        choices,
    )


# ============================================================
# PDF 분석
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

    for question, block in questions:

        body, reference_words, choices = (
            parse_question_block(
                block
            )
        )

        primary, secondary, keywords = (
            classify(body)
        )

        rows.append(
            {
                "year": metadata["year"],
                "grade": metadata["grade"],
                "exam": metadata["exam"],
                "question": question,
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
# CSV 호환 / 기존 데이터 처리
# ============================================================

def normalize_dataframe(df):

    df = df.copy()

    # 기존 CSV가 passage만 가지고 있는 경우
    if "body" not in df.columns:

        if "passage" in df.columns:

            parsed = df[
                "passage"
            ].fillna("").apply(
                parse_question_block
            )

            df["body"] = [
                item[0]
                for item in parsed
            ]

            df["reference_words"] = [
                item[1]
                for item in parsed
            ]

            df["choices"] = [
                item[2]
                for item in parsed
            ]

        else:

            df["body"] = ""

            df["reference_words"] = ""

            df["choices"] = ""

    for column in COLUMNS:

        if column not in df.columns:

            df[column] = ""

    return df[
        COLUMNS
    ].copy()


# ============================================================
# Corpus 병합
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
# Session State
# ============================================================

if "corpus_df" not in st.session_state:

    st.session_state[
        "corpus_df"
    ] = pd.DataFrame(
        columns=COLUMNS
    )


# ============================================================
# 제목
# ============================================================

st.title(
    "📚 Korean High School English Reading Corpus"
)

st.caption(
    "2006–2026 고1·고2·고3 영어 독해 지문 개인용 데이터베이스"
)


# ============================================================
# 사이드바
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
                "PDF를 분석하고 기존 corpus에 추가하는 중..."
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

                        before = len(
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

                        after = len(
                            st.session_state[
                                "corpus_df"
                            ]
                        )

                        st.success(
                            f"완료! "
                            f"{after - before}개 새 지문 추가 / "
                            f"현재 총 {after}개"
                        )

                except Exception as error:

                    st.error(
                        f"분석 오류: {error}"
                    )


    st.divider()

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

                loaded = (
                    normalize_dataframe(
                        loaded
                    )
                )

                before = len(
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
                    loaded,
                )

                after = len(
                    st.session_state[
                        "corpus_df"
                    ]
                )

                st.success(
                    f"CSV 병합 완료: "
                    f"{after - before}개 새 항목 / "
                    f"총 {after}개"
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
# 현재 데이터
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
# 데이터 없음
# ============================================================

if df.empty:

    st.info(
        "왼쪽에서 PDF를 추가하세요."
    )

    st.markdown(
        """
### 저장되는 문항

**20~42번 + 46~50번**

### 제외되는 문항

**1~17번 Listening + 18, 19, 43, 44, 45번**

PDF를 여러 개 추가하면 하나의 corpus에 계속 누적됩니다.
"""
    )


# ============================================================
# 데이터 표시
# ============================================================

else:

    st.success(
        f"현재 corpus: **{len(df)}개 지문**"
    )


    # --------------------------------------------------------
    # 검색 / 필터
    # --------------------------------------------------------

    st.subheader(
        "🔎 검색 / 필터"
    )

    col1, col2, col3 = st.columns(
        3
    )

    with col1:

        years = sorted(
            {
                str(int(v))
                for v in df["year"]
                if str(v)
                .replace(".0", "")
                .isdigit()
            }
        )

        selected_year = st.selectbox(
            "연도",
            ["전체"] + years,
        )

    with col2:

        grades = sorted(
            {
                str(int(v))
                for v in df["grade"]
                if str(v)
                .replace(".0", "")
                .isdigit()
            }
        )

        selected_grade = st.selectbox(
            "학년",
            ["전체"] + grades,
        )

    with col3:

        topics = sorted(
            df[
                "primary_topic"
            ]
            .astype(str)
            .unique()
        )

        selected_topic = st.selectbox(
            "주제",
            ["전체"] + topics,
        )


    search = st.text_input(
        "본문 / 참고 단어 / 선지 검색",
        placeholder=(
            "예: memory, evolution, market..."
        ),
    )


    # --------------------------------------------------------
    # 필터 적용
    # --------------------------------------------------------

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
            filtered["body"].astype(str)
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
    # 지문 카드
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

            st.caption(
                f"연도: {row['year']}  |  "
                f"학년: 고{row['grade']}  |  "
                f"시험: {row['exam']}  |  "
                f"문항: Q{row['question']}"
            )

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


            # ------------------------------------------------
            # 본문
            # ------------------------------------------------

            st.markdown(
                "### 본문"
            )

            st.write(
                row["body"]
            )


            # ------------------------------------------------
            # 참고 영어단어
            # ------------------------------------------------

            if str(
                row["reference_words"]
            ).strip():

                st.markdown(
                    "### 참고 영어단어"
                )

                st.markdown(
                    row[
                        "reference_words"
                    ]
                )


            # ------------------------------------------------
            # 선지
            # ------------------------------------------------

            if str(
                row["choices"]
            ).strip():

                st.markdown(
                    "### 선지"
                )

                st.markdown(
                    row["choices"]
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
            # 직접 수정
            # =================================================

            st.divider()

            st.markdown(
                "### ✏️ 이 지문 수정"
            )

            edited_body = st.text_area(
                "본문",
                value=str(
                    row["body"]
                ),
                height=250,
                key=f"body_{index}",
            )

            edited_reference = st.text_area(
                "참고 영어단어",
                value=str(
                    row[
                        "reference_words"
                    ]
                ),
                height=120,
                key=f"reference_{index}",
            )

            edited_choices = st.text_area(
                "선지",
                value=str(
                    row["choices"]
                ),
                height=180,
                key=f"choices_{index}",
            )

            edit_col1, edit_col2 = st.columns(
                2
            )

            with edit_col1:

                primary_options = list(
                    TAXONOMY.keys()
                )

                current_primary = (
                    row[
                        "primary_topic"
                    ]
                )

                edited_primary = st.selectbox(
                    "Primary Topic",
                    primary_options,
                    index=(
                        primary_options.index(
                            current_primary
                        )
                        if current_primary
                        in primary_options
                        else 0
                    ),
                    key=f"primary_{index}",
                )

            with edit_col2:

                secondary_options = [
                    ""
                ] + TAXONOMY.get(
                    edited_primary,
                    []
                )

                current_secondary = (
                    row[
                        "secondary_topic"
                    ]
                )

                edited_secondary = st.selectbox(
                    "Secondary Topic",
                    secondary_options,
                    index=(
                        secondary_options.index(
                            current_secondary
                        )
                        if current_secondary
                        in secondary_options
                        else 0
                    ),
                    key=f"secondary_{index}",
                )


            if st.button(
                "💾 이 지문 수정 저장",
                key=f"save_{index}",
                type="primary",
            ):

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
