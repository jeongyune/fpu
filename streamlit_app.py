import re
from pathlib import Path
import pandas as pd
import streamlit as st

try:
    import fitz
except ImportError:
    fitz = None

st.set_page_config(
    page_title="KSAT English Reading Corpus",
    page_icon="📚",
    layout="wide"
)

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
        "AI/Computing", "Engineering", "Transportation",
        "Internet/Media", "Technology & Society"
    ],
    "Environment": [
        "Climate", "Conservation", "Pollution", "Natural Resources"
    ],
    "Social Science": [
        "Sociology", "Education", "Politics/Government",
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
        "Habits", "Relationships", "Work",
        "Consumer Behavior", "Travel", "Lifestyle"
    ],
    "Other": []
}

KEYWORDS = {
    "Psychology": {
        "Memory": ["memory", "remember", "recall", "forget"],
        "Cognition": ["cognitive", "cognition", "attention", "reasoning", "perception"],
        "Decision Making": ["decision", "choice", "choose", "judgment"],
        "Emotion": ["emotion", "fear", "happiness", "sadness", "stress"],
        "Social Psychology": [
            "social influence", "conformity", "peer pressure", "group"
        ],
        "Behavior": ["behavior", "behaviour", "habit"],
        "Learning": ["learn", "learning", "education", "student"],
        "Perception": ["perception", "visual perception", "sensory"]
    },

    "Biology": {
        "Evolution": [
            "evolution", "natural selection", "adaptation", "species"
        ],
        "Ecology": [
            "ecosystem", "ecology", "predator", "food web", "habitat"
        ],
        "Animal Behavior": [
            "animal behavior", "migration", "mating", "territory"
        ],
        "Genetics": ["gene", "genetic", "dna", "heredity"],
        "Plants": [
            "plant", "flower", "root", "seed", "photosynthesis"
        ],
        "Microbiology": [
            "bacteria", "virus", "microbe", "microorganism"
        ]
    },

    "Medicine": {
        "Health": ["health", "healthy", "disease prevention"],
        "Disease": ["disease", "illness", "infection", "symptom"],
        "Nutrition": [
            "nutrition", "nutrient", "diet", "calorie", "food"
        ],
        "Medical Technology": [
            "medical technology", "diagnosis", "surgery", "medical device"
        ]
    },

    "Economics": {
        "Markets": ["market", "price", "supply", "demand"],
        "Behavioral Economics": [
            "behavioral economics", "bias", "rational", "irrational"
        ],
        "Trade": ["trade", "import", "export", "tariff"],
        "Money": ["money", "currency", "bank", "inflation"],
        "Incentives": ["incentive", "reward", "cost", "benefit"],
        "Business": [
            "business", "company", "firm", "consumer"
        ]
    },

    "Technology": {
        "AI/Computing": [
            "artificial intelligence", "machine learning",
            "algorithm", "computer", "computing"
        ],
        "Engineering": [
            "engineering", "engineer", "design", "machine"
        ],
        "Transportation": [
            "transportation", "vehicle", "car", "train", "aviation"
        ],
        "Internet/Media": [
            "internet", "social media", "media", "online"
        ],
        "Technology & Society": [
            "technology", "technological", "digital"
        ]
    },

    "Environment": {
        "Climate": [
            "climate", "global warming", "greenhouse gas"
        ],
        "Conservation": [
            "conservation", "endangered", "biodiversity"
        ],
        "Pollution": [
            "pollution", "waste", "plastic", "contamination"
        ],
        "Natural Resources": [
            "natural resource", "water", "forest", "energy"
        ]
    },

    "Social Science": {
        "Sociology": [
            "society", "social class", "community", "institution"
        ],
        "Education": [
            "education", "school", "teacher", "student", "curriculum"
        ],
        "Politics/Government": [
            "government", "political", "president",
            "policy", "election"
        ],
        "Anthropology": [
            "anthropology", "custom", "ritual", "culture"
        ],
        "Communication": [
            "communication", "conversation", "language"
        ],
        "Demography": [
            "population", "birth rate", "demographic", "aging"
        ]
    },

    "History": {
        "World History": [
            "ancient", "medieval", "empire", "war", "historical"
        ],
        "Political History": [
            "president", "revolution", "government", "political"
        ],
        "Social History": [
            "workers", "class", "social history"
        ],
        "Cultural History": [
            "tradition", "cultural", "culture"
        ],
        "Biography": [
            "born", "died", "biography", "life of"
        ]
    },

    "Humanities": {
        "Philosophy": [
            "philosophy", "philosopher"
        ],
        "Ethics": [
            "ethical", "ethics", "moral", "right and wrong"
        ],
        "Religion": [
            "religion", "religious", "church", "god"
        ],
        "Language": [
            "linguistic", "grammar", "word", "language"
        ]
    },

    "Arts & Literature": {
        "Visual Art": [
            "painting", "artist", "sculpture", "artwork"
        ],
        "Music": [
            "music", "musician", "song", "composer"
        ],
        "Literature": [
            "novel", "poem", "poetry", "literature", "fiction"
        ],
        "Architecture": [
            "architecture", "building", "architect"
        ]
    },

    "Geography": {
        "Places & Regions": [
            "region", "continent", "country", "geography"
        ],
        "Cities": [
            "city", "urban", "town"
        ],
        "Population & Geography": [
            "population", "rural", "urban", "migration"
        ]
    },

    "Everyday Life": {
        "Habits": ["habit", "routine", "daily"],
        "Relationships": [
            "friend", "family", "relationship"
        ],
        "Work": [
            "work", "job", "employee", "workplace"
        ],
        "Consumer Behavior": [
            "consumer", "shopping", "purchase"
        ],
        "Travel": [
            "travel", "tourist", "trip", "journey"
        ],
        "Lifestyle": [
            "lifestyle", "leisure", "hobby"
        ]
    }
}

COLUMNS = [
    "year",
    "grade",
    "exam",
    "question",
    "question_type",
    "primary_topic",
    "secondary_topic",
    "keywords",
    "passage"
]


def infer_metadata(filename):
    name = Path(filename).stem

    year_match = re.search(r"(20\d{2})", name)
    month_match = re.search(r"(\d{1,2})월", name)
    grade_match = re.search(r"고\s*([123])", name)

    return {
        "year": int(year_match.group(1)) if year_match else "",
        "grade": int(grade_match.group(1)) if grade_match else "",
        "exam": f"{month_match.group(1)}월" if month_match else ""
    }


def classify(text):
    text_lower = text.lower()
    hits = []

    for primary, secondary_topics in KEYWORDS.items():
        for secondary, words in secondary_topics.items():
            score = sum(
                text_lower.count(word.lower())
                for word in words
            )

            if score:
                hits.append(
                    (score, primary, secondary)
                )

    hits.sort(reverse=True)

    if not hits:
        return "Other", "", ""

    top = hits[0]

    related = [
        item[2]
        for item in hits[1:]
        if item[1] == top[1]
    ][:2]

    return (
        top[1],
        top[2],
        ", ".join(dict.fromkeys(related))
    )


def extract_text(uploaded_file):
    if fitz is None:
        raise RuntimeError(
            "PyMuPDF가 설치되지 않았습니다."
        )

    document = fitz.open(
        stream=uploaded_file.getvalue(),
        filetype="pdf"
    )

    pages = [
        page.get_text("text")
        for page in document
    ]

    text = "\n".join(pages)

    if len(re.sub(r"\s+", "", text)) < 200:
        return None

    return text


def split_questions(text):
    matches = list(
        re.finditer(
            r"(?m)^\s*(1[89]|[2-4]\d|50)\s*[\.\)]?\s+",
            text
        )
    )

    matches = [
        match
        for match in matches
        if 18 <= int(match.group(1)) <= 50
    ]

    rows = []

    for i, match in enumerate(matches):
        question = int(match.group(1))

        end = (
            matches[i + 1].start()
            if i + 1 < len(matches)
            else len(text)
        )

        passage = text[
            match.start():end
        ].strip()

        if len(passage) >= 80:
            rows.append(
                (question, passage)
            )

    return rows


def analyze_pdf(uploaded_file):
    metadata = infer_metadata(
        uploaded_file.name
    )

    text = extract_text(uploaded_file)

    if text is None:
        return (
            None,
            "텍스트 레이어를 찾지 못했습니다. "
            "이 PDF는 OCR 처리가 필요합니다."
        )

    questions = split_questions(text)

    rows = []

    for question, passage in questions:
        primary, secondary, keywords = classify(
            passage
        )

        rows.append({
            "year": metadata["year"],
            "grade": metadata["grade"],
            "exam": metadata["exam"],
            "question": question,
            "question_type": "",
            "primary_topic": primary,
            "secondary_topic": secondary,
            "keywords": keywords,
            "passage": passage
        })

    return (
        pd.DataFrame(rows, columns=COLUMNS),
        None
    )


def merge_corpus(old_df, new_df):
    if old_df is None or old_df.empty:
        return new_df.copy()

    if new_df is None or new_df.empty:
        return old_df.copy()

    combined = pd.concat(
        [old_df, new_df],
        ignore_index=True
    )

    key_columns = [
        "year",
        "grade",
        "exam",
        "question"
    ]

    combined["_unique_key"] = (
        combined[key_columns]
        .astype(str)
        .agg("|".join, axis=1)
    )

    combined = (
        combined
        .drop_duplicates(
            "_unique_key",
            keep="last"
        )
        .drop(columns="_unique_key")
    )

    return combined[
        COLUMNS
    ].reset_index(drop=True)


if "corpus_df" not in st.session_state:
    st.session_state["corpus_df"] = (
        pd.DataFrame(columns=COLUMNS)
    )


st.title(
    "📚 Korean High School English Reading Corpus"
)

st.caption(
    "2006–2026 고1·고2·고3 영어 독해 지문 "
    "개인용 데이터베이스"
)


with st.sidebar:

    st.header("📄 PDF 추가")

    uploaded = st.file_uploader(
        "모의고사 PDF",
        type=["pdf"]
    )

    if uploaded and st.button(
        "이 PDF 분석해서 추가",
        type="primary",
        use_container_width=True
    ):

        with st.spinner(
            "PDF를 분석하고 기존 corpus에 추가하는 중..."
        ):

            try:

                new_df, error = analyze_pdf(
                    uploaded
                )

                if error:
                    st.error(error)

                elif new_df.empty:
                    st.warning(
                        "Reading 지문을 찾지 못했습니다."
                    )

                else:

                    before = len(
                        st.session_state["corpus_df"]
                    )

                    st.session_state["corpus_df"] = (
                        merge_corpus(
                            st.session_state["corpus_df"],
                            new_df
                        )
                    )

                    after = len(
                        st.session_state["corpus_df"]
                    )

                    added = after - before

                    st.success(
                        f"완료! {added}개 새 지문 추가 / "
                        f"현재 총 {after}개"
                    )

            except Exception as error:
                st.error(
                    f"분석 오류: {error}"
                )


    st.divider()

    st.header("💾 저장 / 불러오기")

    csv_file = st.file_uploader(
        "기존 corpus CSV 불러오기",
        type=["csv"]
    )

    if csv_file and st.button(
        "CSV 불러와서 corpus에 합치기",
        use_container_width=True
    ):

        try:

            loaded = pd.read_csv(
                csv_file
            )

            for column in COLUMNS:
                if column not in loaded.columns:
                    loaded[column] = ""

            loaded = loaded[COLUMNS]

            before = len(
                st.session_state["corpus_df"]
            )

            st.session_state["corpus_df"] = (
                merge_corpus(
                    st.session_state["corpus_df"],
                    loaded
                )
            )

            after = len(
                st.session_state["corpus_df"]
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
            st.session_state["corpus_df"]
            .to_csv(index=False)
            .encode("utf-8-sig")
        )

        st.download_button(
            "⬇️ 현재 corpus 저장",
            csv_data,
            "ksat_english_corpus.csv",
            "text/csv",
            use_container_width=True
        )

        if st.button(
            "⚠️ 현재 corpus 전체 삭제",
            use_container_width=True
        ):

            st.session_state["corpus_df"] = (
                pd.DataFrame(columns=COLUMNS)
            )

            st.rerun()


df = st.session_state["corpus_df"]


if df.empty:

    st.info(
        "왼쪽에서 PDF를 추가하세요. "
        "PDF를 여러 개 분석하면 결과가 하나의 "
        "corpus에 계속 누적됩니다."
    )

    st.markdown(
        """
### 사용 순서

1. PDF 업로드
2. **이 PDF 분석해서 추가**
3. 다음 PDF 업로드
4. 다시 **이 PDF 분석해서 추가**
5. 모든 지문이 하나의 corpus에 누적됩니다.

같은 연도·학년·시험·문항을 다시 업로드하면
중복으로 쌓이지 않습니다.

작업이 끝나면 **현재 corpus 저장**으로 CSV를
백업할 수 있습니다.
"""
    )

else:

    st.success(
        f"현재 corpus: **{len(df)}개 지문**"
    )

    st.subheader("🔎 검색 / 필터")

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        years = sorted([
            str(int(value))
            for value in df["year"].dropna().unique()
            if str(value)
            .replace(".0", "")
            .isdigit()
        ])

        year = st.selectbox(
            "연도",
            ["전체"] + years
        )

    with c2:

        grades = sorted([
            str(int(value))
            for value in df["grade"].dropna().unique()
            if str(value)
            .replace(".0", "")
            .isdigit()
        ])

        grade = st.selectbox(
            "학년",
            ["전체"] + grades
        )

    with c3:

        topics = sorted(
            df["primary_topic"]
            .astype(str)
            .unique()
        )

        topic = st.selectbox(
            "주제",
            ["전체"] + topics
        )

    with c4:

        search = st.text_input(
            "본문 / 키워드 검색"
        )


    filtered = df.copy()


    if year != "전체":
        filtered = filtered[
            filtered["year"]
            .astype(str)
            .str.startswith(year)
        ]


    if grade != "전체":
        filtered = filtered[
            filtered["grade"]
            .astype(str)
            .str.startswith(grade)
        ]


    if topic != "전체":
        filtered = filtered[
            filtered["primary_topic"] == topic
        ]


    if search:

        mask = (
            filtered["passage"]
            .astype(str)
            .str.contains(
                search,
                case=False,
                na=False
            )
            |
            filtered["keywords"]
            .astype(str)
            .str.contains(
                search,
                case=False,
                na=False
            )
            |
            filtered["secondary_topic"]
            .astype(str)
            .str.contains(
                search,
                case=False,
                na=False
            )
        )

        filtered = filtered[mask]


    st.write(
        f"**검색 결과 {len(filtered)}개**"
    )

    st.dataframe(
        filtered,
        use_container_width=True,
        hide_index=True
    )


    st.subheader("✏️ 분류 수정")

    if not filtered.empty:

        selected_index = st.selectbox(
            "수정할 지문",
            filtered.index.tolist(),
            format_func=lambda index:
                f"{df.loc[index, 'year']} / "
                f"고{df.loc[index, 'grade']} / "
                f"{df.loc[index, 'exam']} / "
                f"Q{df.loc[index, 'question']}"
        )

        col_a, col_b = st.columns(2)

        with col_a:

            current_primary = df.loc[
                selected_index,
                "primary_topic"
            ]

            new_primary = st.selectbox(
                "Primary topic",
                list(TAXONOMY.keys()),
                index=(
                    list(TAXONOMY.keys())
                    .index(current_primary)
                    if current_primary in TAXONOMY
                    else 0
                )
            )

        with col_b:

            secondary_options = (
                [""]
                + TAXONOMY.get(
                    new_primary,
                    []
                )
            )

            current_secondary = df.loc[
                selected_index,
                "secondary_topic"
            ]

            new_secondary = st.selectbox(
                "Secondary topic",
                secondary_options,
                index=(
                    secondary_options.index(
                        current_secondary
                    )
                    if current_secondary
                    in secondary_options
                    else 0
                )
            )

        if st.button("분류 저장"):

            df.loc[
                selected_index,
                "primary_topic"
            ] = new_primary

            df.loc[
                selected_index,
                "secondary_topic"
            ] = new_secondary

            st.session_state[
                "corpus_df"
            ] = df

            st.success(
                "수정했습니다."
            )

            st.rerun()
