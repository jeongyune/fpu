st.divider()
st.header("검색 / 필터")
search = st.text_input("검색어", "")
grades = ["전체"] + sorted([x for x in st.session_state.df["grade"].dropna().unique() if x])
years = ["전체"] + [str(x) for x in sorted([int(x) for x in st.session_state.df["year"].dropna().unique() if str(x).isdigit()])]
topics = ["전체"] + sorted(st.session_state.df["primary_topic"].dropna().unique().tolist())

grade_filter = st.selectbox("학년", grades)
year_filter = st.selectbox("연도", years)
topic_filter = st.selectbox("주제", topics)
