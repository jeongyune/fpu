import io
import re

import fitz
import pandas as pd
import streamlit as st


# ============================================================
# 1. 기본 설정
# ============================================================

st.set_page_config(
    page_title="KSAT English Reading Corpus",
    page_icon="📚",
    layout="wide",
)

EXCLUDED_QUESTIONS = set(range(1, 20)) | {43, 44, 45}


# ============================================================
# 2. 분류 체계
#    Primary Topic → Field → Subtopic → Keywords
# ============================================================

TAXONOMY = {
    "Psychology": {
        "Cognitive Psychology": {
            "Memory": ["memory", "remember", "recall", "forget", "retention"],
            "Attention": ["attention", "attentional", "focus"],
            "Perception": ["perception", "perceive", "illusion", "visual imagery"],
            "Reasoning": ["reasoning", "reason", "judgment", "judgement"],
            "Cognitive Bias": [
                "bias", "confirmation bias", "framing effect",
                "anchoring", "cognitive error"
            ],
            "Decision Making": [
                "decision", "decision making", "choice", "choices"
            ],
        },
        "Social Psychology": {
            "Conformity": ["conformity", "conform", "peer pressure"],
            "Group Behavior": ["group behavior", "group behaviour", "group dynamics"],
            "Social Influence": ["social influence", "influence of others"],
            "Bystander Effect": ["bystander", "bystander effect"],
            "Groupthink": ["groupthink", "group thinking"],
            "Social Norms": ["social norm", "norms", "social expectation"],
            "Interpersonal Relations": [
                "relationship", "interpersonal", "friendship", "cooperation"
            ],
        },
        "Developmental Psychology": {
            "Child Development": [
                "child development", "childhood", "infancy", "infant"
            ],
            "Attachment": ["attachment", "caregiver"],
            "Language Acquisition": ["language acquisition", "first language"],
            "Cognitive Development": ["cognitive development", "developmental"],
            "Personality Development": ["personality development", "personality"],
            "Aging": ["aging", "ageing", "elderly", "older adults"],
        },
        "Behavioral Psychology": {
            "Habit": ["habit", "habitual", "routine"],
            "Conditioning": ["conditioning", "reinforcement", "punishment"],
            "Motivation": ["motivation", "motivated", "reward"],
            "Behavioral Patterns": ["behavior", "behaviour", "behavioral pattern"],
        },
        "Emotion & Well-being": {
            "Emotion": ["emotion", "emotional", "feeling"],
            "Stress": ["stress", "stressful"],
            "Happiness": ["happiness", "happy", "well-being", "wellbeing"],
            "Fear": ["fear", "anxiety"],
        },
    },

    "Philosophy & Ethics": {
        "Epistemology & Logic": {
            "Knowledge": ["knowledge", "know"],
            "Truth": ["truth", "true"],
            "Skepticism": ["skepticism", "scepticism", "skeptical", "sceptical"],
            "Induction & Deduction": ["induction", "deduction"],
            "Reasoning": ["logic", "logical", "argument"],
        },
        "Philosophy of Science": {
            "Scientific Method": ["scientific method", "methodology"],
            "Objectivity": ["objectivity", "objective"],
            "Falsification": ["falsification", "falsify"],
            "Paradigm Shift": ["paradigm", "paradigm shift"],
        },
        "Ethics": {
            "Moral Judgment": ["moral judgment", "moral judgement", "morality"],
            "Justice": ["justice", "fairness", "fair"],
            "Duty": ["duty", "obligation"],
            "Consequentialism": ["consequentialism", "consequence"],
            "Utilitarianism": ["utilitarianism", "utility"],
            "Virtue Ethics": ["virtue", "virtue ethics"],
        },
        "Applied Ethics": {
            "AI Ethics": ["ai ethics", "artificial intelligence ethics"],
            "Medical Ethics": ["medical ethics", "bioethics"],
            "Environmental Ethics": ["environmental ethics"],
            "Animal Ethics": ["animal ethics", "animal rights"],
            "Technology Ethics": ["technology ethics", "digital ethics"],
        },
        "Philosophy of Mind & Human Nature": {
            "Consciousness": ["consciousness", "conscious"],
            "Free Will": ["free will"],
            "Mind-Body": ["mind-body", "mind body"],
            "Human Nature": ["human nature"],
            "Self": ["self", "identity"],
        },
    },

    "History": {
        "World History": {
            "Ancient Civilization": ["ancient", "civilization", "empire"],
            "Medieval History": ["medieval", "middle ages"],
            "Modern History": ["modern history", "industrial revolution"],
            "Wars": ["war", "battle", "military"],
        },
        "Political History": {
            "Revolutions": ["revolution", "revolutionary"],
            "Political Movements": ["political movement", "movement"],
            "Leaders": ["president", "leader", "ruler"],
        },
        "Social History": {
            "Class": ["social class", "class system"],
            "Labor": ["labor", "labour", "worker", "workers"],
            "Social Change": ["social change"],
            "Everyday Life": ["everyday life", "daily life"],
        },
        "Cultural History": {
            "Customs": ["custom", "customs"],
            "Traditions": ["tradition", "traditional"],
            "Religion": ["religion", "religious"],
            "Cultural Change": ["cultural change"],
        },
        "History of Science & Technology": {
            "Scientific Discoveries": ["discovery", "scientific discovery"],
            "Inventions": ["invention", "invented", "inventor"],
            "Technological Change": ["technological change"],
        },
        "Biography": {
            "Scientists": ["scientist", "scientists"],
            "Artists": ["artist", "painter"],
            "Philosophers": ["philosopher"],
            "Inventors": ["inventor"],
        },
    },

    "Religion & Religious Studies": {
        "Religion": {
            "Beliefs": ["belief", "beliefs", "faith"],
            "Rituals": ["ritual", "rituals", "ceremony"],
            "Religious Institutions": ["church", "temple", "religious institution"],
            "Mythology": ["myth", "mythology", "legend"],
            "Secularization": ["secular", "secularization"],
        }
    },

    "Economics": {
        "Behavioral Economics": {
            "Loss Aversion": ["loss aversion"],
            "Anchoring": ["anchoring", "anchor"],
            "Present Bias": ["present bias"],
            "Irrational Choice": ["irrational", "irrational choice"],
            "Prospect Theory": ["prospect theory"],
        },
        "Microeconomics": {
            "Supply & Demand": ["supply", "demand"],
            "Opportunity Cost": ["opportunity cost"],
            "Incentives": ["incentive", "incentives"],
            "Consumer Choice": ["consumer choice", "consumer"],
            "Competition": ["competition", "competitive"],
        },
        "Macroeconomics": {
            "Inflation": ["inflation"],
            "Unemployment": ["unemployment"],
            "Economic Growth": ["economic growth", "growth"],
            "Recession": ["recession", "economic crisis"],
            "Fiscal Policy": ["fiscal policy"],
            "Monetary Policy": ["monetary policy"],
        },
        "Market Dynamics": {
            "Markets": ["market", "markets"],
            "Price": ["price", "pricing"],
            "Market Failure": ["market failure"],
            "Externalities": ["externality", "externalities"],
        },
        "International Economics": {
            "Trade": ["trade", "import", "imports", "export", "exports"],
            "Tariffs": ["tariff", "tariffs"],
            "Globalization": ["globalization", "globalisation"],
            "Exchange Rates": ["exchange rate", "currency"],
        },
    },

    "Sociology": {
        "Social Structure": {
            "Social Class": ["social class", "class"],
            "Institutions": ["social institution", "institution"],
            "Inequality": ["inequality", "inequality"],
            "Social Mobility": ["social mobility"],
        },
        "Society & Community": {
            "Community": ["community"],
            "Social Networks": ["social network", "network"],
            "Collective Behavior": ["collective behavior", "collective behaviour"],
            "Cooperation": ["cooperation", "cooperate"],
        },
        "Social Change": {
            "Modernization": ["modernization", "modernisation"],
            "Urbanization": ["urbanization", "urbanisation", "urban"],
            "Industrialization": ["industrialization", "industrialisation"],
            "Social Movements": ["social movement"],
        },
        "Family & Relationships": {
            "Family": ["family", "families"],
            "Marriage": ["marriage"],
            "Parenting": ["parenting", "parent"],
            "Generations": ["generation", "generations"],
        },
    },

    "Anthropology": {
        "Cultural Anthropology": {
            "Culture": ["culture", "cultural"],
            "Customs": ["custom", "customs"],
            "Cultural Relativism": ["cultural relativism"],
            "Ethnocentrism": ["ethnocentrism"],
        },
        "Linguistic Anthropology": {
            "Language & Culture": ["language and culture", "language & culture"],
            "Cultural Meaning": ["cultural meaning"],
        },
        "Human Evolution Anthropology": {
            "Human Origins": ["human origins", "early humans"],
            "Human Adaptation": ["human adaptation", "adaptation"],
        },
    },

    "Political Science & Government": {
        "Political Systems": {
            "Democracy": ["democracy", "democratic"],
            "Government": ["government", "governments"],
            "Institutions": ["political institution"],
            "Constitution": ["constitution"],
        },
        "Public Policy": {
            "Regulation": ["regulation", "regulate"],
            "Welfare": ["welfare"],
            "Education Policy": ["education policy"],
            "Environmental Policy": ["environmental policy"],
        },
        "Political Behavior": {
            "Elections": ["election", "elections"],
            "Voting": ["voting", "vote", "voter"],
            "Public Opinion": ["public opinion"],
            "Political Participation": ["political participation"],
        },
        "International Relations": {
            "Diplomacy": ["diplomacy", "diplomatic"],
            "International Organizations": [
                "international organization", "united nations", "un"
            ],
            "Conflict": ["international conflict"],
            "Cooperation": ["international cooperation"],
        },
    },

    "Education": {
        "Learning & Teaching": {
            "Learning Methods": ["learning method", "learning methods"],
            "Teaching": ["teaching", "teacher"],
            "Curriculum": ["curriculum"],
            "Assessment": ["assessment", "test", "testing"],
        },
        "Educational Psychology": {
            "Motivation": ["student motivation", "learning motivation"],
            "Memory": ["learning and memory"],
            "Learning Strategies": ["learning strategy", "study strategy"],
        },
        "Education & Society": {
            "Educational Inequality": ["educational inequality"],
            "School Systems": ["school system", "education system"],
            "Access to Education": ["access to education"],
        },
    },

    "Demography": {
        "Population": {
            "Population Growth": ["population growth"],
            "Birth Rate": ["birth rate", "fertility rate"],
            "Death Rate": ["death rate", "mortality"],
            "Aging": ["aging population", "ageing population"],
            "Migration": ["migration", "migrant"],
            "Population Distribution": ["population distribution"],
        }
    },

    "Business & Management": {
        "Management": {
            "Organizational Behavior": [
                "organizational behavior", "organizational behaviour",
                "teamwork", "team", "leadership"
            ],
            "Human Resource Management": [
                "human resource", "recruitment", "employee",
                "training", "compensation"
            ],
            "Strategy": [
                "business strategy", "competitive advantage",
                "strategy", "strategic"
            ],
            "Operations Management": [
                "productivity", "efficiency", "supply chain",
                "quality control", "process management"
            ],
        },
        "Marketing": {
            "Consumer Behavior": [
                "consumer behavior", "consumer behaviour", "consumer psychology"
            ],
            "Advertising": ["advertising", "advertisement", "ad"],
            "Branding": ["brand", "branding"],
            "Market Research": ["market research"],
            "Pricing": ["pricing"],
            "Social Media Marketing": ["social media marketing"],
        },
        "Entrepreneurship": {
            "Startups": ["startup", "start-up", "startups"],
            "Entrepreneurs": ["entrepreneur", "entrepreneurs"],
            "Innovation": ["innovation", "innovative"],
            "Risk": ["business risk", "entrepreneurial risk"],
            "Business Models": ["business model"],
        },
        "Finance & Accounting": {
            "Investment": ["investment", "invest", "investor"],
            "Stocks": ["stock", "stocks", "share", "shares"],
            "Banking": ["bank", "banking"],
            "Corporate Finance": ["corporate finance"],
            "Accounting": ["accounting", "accountant"],
            "Risk Management": ["risk management"],
        },
    },

    "Biology & Life Sciences": {
        "Evolutionary Biology": {
            "Natural Selection": ["natural selection", "selection"],
            "Adaptation": ["adaptation", "adaptive"],
            "Evolution": ["evolution", "evolutionary"],
            "Sexual Selection": ["sexual selection"],
            "Altruism": ["altruism", "altruistic"],
            "Genetic Variation": ["genetic variation"],
        },
        "Ecology & Biodiversity": {
            "Ecosystems": ["ecosystem", "ecosystems"],
            "Food Webs": ["food web", "food chain"],
            "Predators": ["predator", "predators", "predation"],
            "Competition": ["ecological competition"],
            "Symbiosis": ["symbiosis", "mutualism", "parasitism"],
            "Invasive Species": ["invasive species"],
            "Extinction": ["extinction", "extinct"],
        },
        "Genetics": {
            "Genes": ["gene", "genes"],
            "DNA": ["dna"],
            "Mutation": ["mutation", "mutations"],
            "Heredity": ["heredity", "hereditary"],
            "Genetic Variation": ["genetic variation"],
        },
        "Cell Biology": {
            "Cells": ["cell", "cells"],
            "Cell Division": ["cell division", "mitosis", "meiosis"],
            "Cellular Processes": ["cellular", "cell membrane"],
        },
        "Botany": {
            "Plants": ["plant", "plants"],
            "Photosynthesis": ["photosynthesis"],
            "Seeds": ["seed", "seeds"],
            "Plant Adaptation": ["plant adaptation"],
        },
        "Microbiology": {
            "Bacteria": ["bacteria", "bacterium"],
            "Viruses": ["virus", "viruses"],
            "Microorganisms": ["microorganism", "microorganisms", "microbe"],
        },
        "Animal Behavior": {
            "Migration": ["animal migration", "migration"],
            "Mating": ["mating", "mate selection"],
            "Communication": ["animal communication"],
            "Territoriality": ["territorial", "territory"],
            "Cooperation": ["animal cooperation"],
        },
    },

    "Neuroscience": {
        "Neuroplasticity & Brain Function": {
            "Neuroplasticity": ["neuroplasticity", "plasticity"],
            "Brain Function": ["brain function", "brain activity"],
            "Sleep & Memory": ["sleep and memory", "memory consolidation"],
            "Emotion & Brain": ["brain region", "brain regions", "emotion and brain"],
            "Brain Imaging": ["fmri", "brain imaging", "neuroimaging"],
        }
    },

    "Physics": {
        "Mechanics": {
            "Motion": ["motion", "velocity", "acceleration"],
            "Force": ["force", "friction"],
            "Gravity": ["gravity", "gravitational"],
            "Energy": ["energy", "kinetic", "potential energy"],
            "Momentum": ["momentum"],
            "Equilibrium": ["equilibrium"],
        },
        "Thermodynamics": {
            "Heat": ["heat"],
            "Temperature": ["temperature"],
            "Entropy": ["entropy"],
            "Energy Transfer": ["energy transfer", "heat transfer"],
        },
        "Electromagnetism": {
            "Electricity": ["electricity", "electric"],
            "Magnetism": ["magnet", "magnetic"],
            "Electromagnetic Waves": ["electromagnetic wave"],
            "Circuits": ["circuit", "circuits"],
        },
        "Optics": {
            "Light": ["light", "light wave"],
            "Reflection": ["reflection"],
            "Refraction": ["refraction"],
            "Lenses": ["lens", "lenses"],
            "Vision": ["vision", "visual"],
        },
        "Modern Physics": {
            "Relativity": ["relativity", "relativistic"],
            "Quantum Mechanics": ["quantum", "quantum mechanics"],
            "Atomic Physics": ["atomic physics", "atom"],
            "Particle Physics": ["particle physics", "particle"],
        },
        "Applied Physics": {
            "Materials": ["material", "materials"],
            "Energy Technology": ["energy technology"],
            "Medical Physics": ["medical physics"],
            "Engineering Applications": ["engineering application"],
        },
    },

    "Chemistry": {
        "General Chemistry": {
            "Matter": ["matter", "substance"],
            "Atoms": ["atom", "atoms"],
            "Molecules": ["molecule", "molecules"],
            "Chemical Reactions": ["chemical reaction", "reaction"],
            "Stoichiometry": ["stoichiometry", "mole"],
        },
        "Physical Chemistry": {
            "Thermodynamics": ["chemical thermodynamics", "enthalpy"],
            "Equilibrium": ["chemical equilibrium", "equilibrium"],
            "Kinetics": ["chemical kinetics", "reaction rate"],
            "Energy": ["chemical energy"],
        },
        "Organic Chemistry": {
            "Carbon Compounds": ["carbon compound", "organic compound"],
            "Polymers": ["polymer", "polymers"],
            "Organic Reactions": ["organic reaction"],
            "Biomolecules": ["biomolecule", "protein", "carbohydrate", "lipid"],
        },
        "Inorganic Chemistry": {
            "Metals": ["metal", "metals"],
            "Minerals": ["mineral", "minerals"],
            "Coordination Compounds": ["coordination compound"],
        },
        "Analytical Chemistry": {
            "Measurement": ["chemical measurement"],
            "Chemical Analysis": ["chemical analysis"],
            "Spectroscopy": ["spectroscopy", "spectroscopic"],
            "Detection": ["detection method"],
        },
        "Materials Chemistry": {
            "Polymers": ["advanced polymer"],
            "Nanomaterials": ["nanomaterial", "nanotechnology"],
            "Semiconductors": ["semiconductor"],
            "Advanced Materials": ["advanced material"],
        },
        "Environmental Chemistry": {
            "Pollution": ["chemical pollution", "pollutant"],
            "Atmospheric Chemistry": ["atmospheric chemistry"],
            "Water Chemistry": ["water chemistry"],
            "Toxic Substances": ["toxic substance", "toxin"],
        },
    },

    "Earth Science": {
        "Geology": {
            "Rocks": ["rock", "rocks"],
            "Minerals": ["mineral", "minerals"],
            "Plate Tectonics": ["plate tectonics", "tectonic plate"],
            "Earth Structure": ["earth structure", "crust", "mantle", "core"],
            "Geological Processes": ["geological process"],
        },
        "Meteorology": {
            "Weather": ["weather"],
            "Atmosphere": ["atmosphere", "atmospheric"],
            "Storms": ["storm", "hurricane", "typhoon"],
            "Clouds": ["cloud", "clouds"],
            "Atmospheric Circulation": ["atmospheric circulation"],
        },
        "Climatology": {
            "Climate": ["climate"],
            "Climate Change": ["climate change", "global warming"],
            "Greenhouse Effect": ["greenhouse effect", "greenhouse gas"],
            "Paleoclimate": ["paleoclimate"],
        },
        "Oceanography": {
            "Oceans": ["ocean", "oceans"],
            "Currents": ["ocean current", "currents"],
            "Marine Systems": ["marine ecosystem", "marine system"],
            "Ocean-Climate Interaction": ["ocean climate"],
        },
        "Environmental Earth Science": {
            "Natural Resources": ["natural resource", "natural resources"],
            "Water": ["water resource", "freshwater"],
            "Soil": ["soil"],
            "Environmental Change": ["environmental change"],
        },
        "Earth History": {
            "Geological Time": ["geological time", "geologic time"],
            "Fossils": ["fossil", "fossils"],
            "Mass Extinction": ["mass extinction"],
            "Evolution of Earth": ["history of earth", "earth history"],
        },
    },

    "Astronomy & Space Science": {
        "Astronomy": {
            "Stars": ["star", "stars", "stellar"],
            "Galaxies": ["galaxy", "galaxies"],
            "Planets": ["planet", "planets"],
            "Solar System": ["solar system"],
        },
        "Astrophysics": {
            "Stellar Evolution": ["stellar evolution"],
            "Black Holes": ["black hole", "black holes"],
            "Gravity": ["astrophysical gravity"],
            "Radiation": ["cosmic radiation", "radiation"],
        },
        "Cosmology": {
            "Universe": ["universe"],
            "Big Bang": ["big bang"],
            "Dark Matter": ["dark matter"],
            "Dark Energy": ["dark energy"],
        },
        "Space Exploration": {
            "Spacecraft": ["spacecraft", "spacecrafts"],
            "Satellites": ["satellite", "satellites"],
            "Space Missions": ["space mission"],
            "Human Spaceflight": ["human spaceflight", "astronaut"],
        },
    },

    "Medicine & Health": {
        "Human Biology": {
            "Anatomy": ["anatomy", "organ"],
            "Physiology": ["physiology"],
            "Brain": ["human brain"],
            "Hormones": ["hormone", "hormones"],
        },
        "Medicine": {
            "Disease": ["disease", "illness", "disorder"],
            "Diagnosis": ["diagnosis", "diagnostic"],
            "Treatment": ["treatment", "therapy"],
            "Medical Research": ["medical research", "clinical study"],
        },
        "Public Health": {
            "Epidemiology": ["epidemiology", "epidemic"],
            "Disease Prevention": ["disease prevention", "prevention"],
            "Health Policy": ["health policy", "public health policy"],
        },
        "Nutrition": {
            "Diet": ["diet", "dietary"],
            "Nutrients": ["nutrient", "nutrients"],
            "Metabolism": ["metabolism", "metabolic"],
            "Food & Health": ["food and health"],
        },
        "Medical Technology": {
            "Medical Imaging": ["medical imaging", "mri", "ct scan"],
            "Prosthetics": ["prosthetic", "prosthetics"],
            "Medical Devices": ["medical device"],
            "Biotechnology": ["medical biotechnology"],
        },
    },

    "Technology & Engineering": {
        "Computer Science": {
            "Algorithms": ["algorithm", "algorithms"],
            "Computing": ["computing", "computer science"],
            "Software": ["software"],
            "Data": ["data", "database"],
            "AI": ["artificial intelligence", "ai", "machine learning"],
        },
        "Engineering": {
            "Mechanical Engineering": ["mechanical engineering"],
            "Civil Engineering": ["civil engineering"],
            "Electrical Engineering": ["electrical engineering"],
            "Materials Engineering": ["materials engineering"],
        },
        "Biotechnology": {
            "Genetic Engineering": ["genetic engineering"],
            "Biotech": ["biotechnology", "biotech"],
            "Bioengineering": ["bioengineering"],
        },
        "Transportation": {
            "Cars": ["car", "cars", "automobile"],
            "Aviation": ["aviation", "aircraft", "airplane"],
            "Railways": ["railway", "railways", "train"],
            "Autonomous Vehicles": ["autonomous vehicle", "self-driving"],
        },
        "Internet & Digital Technology": {
            "Internet": ["internet", "web"],
            "Social Media": ["social media"],
            "Digital Platforms": ["digital platform"],
            "Information": ["information technology", "information system"],
        },
        "Technology & Society": {
            "Automation": ["automation", "automated"],
            "Digital Divide": ["digital divide"],
            "Privacy": ["privacy", "personal data"],
            "Technological Change": ["technological change"],
            "Human-Technology Interaction": [
                "human technology", "human-computer interaction"
            ],
        },
    },

    "Environmental Science": {
        "Climate & Climate Change": {
            "Global Warming": ["global warming"],
            "Greenhouse Gases": ["greenhouse gas", "carbon dioxide"],
            "Climate Policy": ["climate policy"],
        },
        "Conservation": {
            "Biodiversity": ["biodiversity"],
            "Endangered Species": ["endangered species"],
            "Protected Areas": ["protected area", "national park"],
        },
        "Pollution": {
            "Air Pollution": ["air pollution"],
            "Water Pollution": ["water pollution"],
            "Plastic": ["plastic pollution", "plastic waste"],
            "Waste": ["waste", "waste management"],
        },
        "Natural Resources": {
            "Water": ["water resources"],
            "Forests": ["forest", "forests"],
            "Minerals": ["mineral resources"],
            "Energy": ["renewable energy", "fossil fuel"],
        },
        "Sustainability": {
            "Sustainable Development": ["sustainable development"],
            "Renewable Energy": ["renewable energy"],
            "Circular Economy": ["circular economy"],
            "Resource Efficiency": ["resource efficiency"],
        },
    },

    "Linguistics": {
        "Language & Cognition": {
            "Language and Thought": ["language and thought"],
            "Linguistic Relativity": [
                "linguistic relativity", "saphir-whorf", "sapir-whorf"
            ],
            "Metaphor": ["metaphor", "metaphorical"],
            "Categorization": ["categorization", "categorisation"],
        },
        "Language Acquisition": {
            "Child Language": ["child language"],
            "Second Language": ["second language", "foreign language"],
            "Language Learning": ["language learning"],
        },
        "Sociolinguistics": {
            "Language & Society": ["language and society"],
            "Dialects": ["dialect", "dialects"],
            "Language Attitudes": ["language attitude"],
            "Language & Identity": ["language identity"],
        },
        "Historical Linguistics": {
            "Language Change": ["language change"],
            "Language Evolution": ["language evolution"],
            "Language Death": ["language death"],
            "Language Preservation": ["language preservation"],
        },
        "Communication": {
            "Verbal Communication": ["verbal communication"],
            "Nonverbal Communication": [
                "nonverbal communication", "non-verbal communication"
            ],
            "Conversation": ["conversation"],
            "Meaning": ["meaning", "semantics"],
        },
    },

    "Arts & Culture": {
        "Visual Arts": {
            "Painting": ["painting", "painter"],
            "Sculpture": ["sculpture"],
            "Photography": ["photography", "photograph"],
            "Art Techniques": ["art technique"],
        },
        "Art History": {
            "Art Movements": ["art movement"],
            "Artists": ["artist", "artists"],
            "Historical Context": ["art history", "historical context"],
            "Cultural Change": ["artistic change"],
        },
        "Music": {
            "Music": ["music", "musical"],
            "Musical Psychology": ["music and emotion", "music psychology"],
            "Music History": ["music history"],
            "Composition": ["composition", "composer"],
        },
        "Film & Media": {
            "Film": ["film", "movie", "cinema"],
            "Visual Media": ["visual media"],
            "Animation": ["animation", "animated"],
        },
        "Architecture": {
            "Architecture": ["architecture", "architect"],
            "Buildings": ["building", "buildings"],
            "Urban Design": ["urban design"],
        },
        "Aesthetics": {
            "Beauty": ["beauty", "beautiful"],
            "Artistic Value": ["artistic value"],
            "Taste": ["taste", "aesthetic taste"],
            "Interpretation": ["art interpretation"],
        },
    },

    "Literature": {
        "Literary Works": {
            "Fiction": ["fiction", "novel", "story"],
            "Poetry": ["poetry", "poem", "poet"],
            "Drama": ["drama", "play"],
        },
        "Literary Theory": {
            "Narrative": ["narrative", "narrator"],
            "Symbolism": ["symbol", "symbolism"],
            "Metaphor": ["literary metaphor"],
            "Interpretation": ["literary interpretation"],
        },
        "Literature & Society": {
            "Literature & Culture": ["literature and culture"],
            "Literature & Politics": ["literature and politics"],
            "Literature & Identity": ["literature and identity"],
        },
        "Authors & Literary History": {
            "Writers": ["writer", "author"],
            "Literary Movements": ["literary movement"],
            "Literary History": ["literary history"],
        },
    },
}


# Context는 학문 분야와 별도로 붙이는 보조 태그
CONTEXT_KEYWORDS = {
    "Everyday Life": [
        "daily life", "everyday", "habit", "routine", "home"
    ],
    "Work": [
        "work", "workplace", "employee", "employer", "team", "office"
    ],
    "Education": [
        "school", "student", "teacher", "education", "learning"
    ],
    "Environment": [
        "environment", "climate", "pollution", "ecosystem", "conservation"
    ],
    "Technology": [
        "technology", "digital", "computer", "internet", "artificial intelligence"
    ],
    "Culture": [
        "culture", "cultural", "tradition", "art", "music"
    ],
    "Society": [
        "society", "social", "community", "population"
    ],
    "Consumer": [
        "consumer", "shopping", "advertising", "brand", "purchase"
    ],
    "Nature": [
        "animal", "plant", "forest", "ocean", "species"
    ],
}


# ============================================================
# 3. PDF / 텍스트 처리
# ============================================================

def extract_pdf_text(uploaded_file):
    """PDF의 텍스트 레이어를 읽는다. OCR은 사용하지 않는다."""
    data = uploaded_file.getvalue()

    with fitz.open(stream=data, filetype="pdf") as pdf:
        pages = [page.get_text("text") for page in pdf]

    return "\n".join(pages)


def clean_text(text):
    """PDF 추출 과정에서 생긴 헤더, 구분선, 불필요한 공백을 제거한다."""
    text = text.replace("\r", "\n")
    text = text.replace("\u00a0", " ")

    lines = []

    for line in text.splitlines():
        line = re.sub(r"\s+", " ", line).strip()

        if not line:
            continue

        # PDF에 반복되는 시험지 헤더 제거
        if "영어영역" in line:
            continue

        # 구분선 제거
        if re.fullmatch(r"[-_=─━—\s]{5,}", line):
            continue

        lines.append(line)

    return "\n".join(lines)


def split_questions(text):
    """PDF 전체 텍스트를 문제 번호별 블록으로 나눈다."""
    text = clean_text(text)

    matches = list(
        re.finditer(r"(?m)^\s*(\d{1,2})\s*[.)]\s*", text)
    )

    questions = []

    for i, match in enumerate(matches):
        number = int(match.group(1))

        if number in EXCLUDED_QUESTIONS:
            continue

        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)

        block = text[start:end].strip()

        if block:
            questions.append((number, block))

    return questions


# ============================================================
# 4. 문제 블록을 본문 / 참고단어 / 선지로 분리
# ============================================================

def split_options(text):
    """①~⑤ 선지를 각각 분리한다."""
    marker = re.search(r"[①②③④⑤]", text)

    if not marker:
        return text.strip(), []

    main = text[:marker.start()].strip()
    option_text = text[marker.start():].strip()

    matches = list(re.finditer(r"[①②③④⑤]", option_text))

    options = []

    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(option_text)

        item = option_text[start:end].strip()

        if item:
            options.append(item)

    return main, options


def split_prompt_and_passage(text):
    """
    문제 발문과 영어 본문을 분리한다.

    예:
    다음 글에서 ... 가장 적절한 것은? [3점]
    Humans ...
    """

    match = re.search(
        r"\?(?:\s*\[\s*\d+\s*점\s*\])?\s*",
        text
    )

    if match:
        prompt = text[:match.end()].strip()
        passage = text[match.end():].strip()
        return prompt, passage

    return "", text.strip()


def extract_vocab(text):
    """
    PDF에서 참고 영어단어 부분으로 보이는 bullet/별표 줄을 분리한다.
    """
    lines = text.splitlines()
    passage_lines = []
    vocab_lines = []

    for line in lines:
        stripped = line.strip()

        if (
            stripped.startswith("•")
            or stripped.startswith("*")
            or stripped.startswith("·")
        ):
            vocab_lines.append(stripped.lstrip("•*· ").strip())
        else:
            passage_lines.append(stripped)

    return (
        "\n".join(x for x in passage_lines if x),
        "\n".join(x for x in vocab_lines if x),
    )


def parse_question(number, block):
    """하나의 문제 블록을 DB에 넣을 수 있는 구조로 만든다."""
    block = re.sub(
        rf"^\s*{number}\s*[.)]\s*",
        "",
        block,
        count=1
    )

    main_text, options = split_options(block)
    prompt, passage = split_prompt_and_passage(main_text)

    passage, vocab = extract_vocab(passage)

    return {
        "question": number,
        "prompt": prompt,
        "passage": passage,
        "vocab": vocab,
        "options": "\n".join(options),
    }


# ============================================================
# 5. 메타데이터 / 주제 자동 분류
# ============================================================

def infer_metadata(filename):
    """파일명에서 연도 / 학년 / 시험월을 추정한다."""
    year_match = re.search(r"(20\d{2})", filename)
    grade_match = re.search(r"고\s*([123])", filename)
    month_match = re.search(r"(\d{1,2})\s*월", filename)

    return {
        "year": int(year_match.group(1)) if year_match else "",
        "grade": f"고{grade_match.group(1)}" if grade_match else "",
        "exam": f"{month_match.group(1)}월" if month_match else "",
    }


def classify(text):
    """
    키워드 기반 1차 분류.
    자동 분류는 '초안'이며 사람이 수정할 수 있도록 설계한다.
    """
    text = text.lower()

    scores = []

    for domain, fields in TAXONOMY.items():
        domain_score = 0
        best_field = ""
        best_subtopic = ""
        best_sub_score = 0

        for field, subtopics in fields.items():
            field_score = 0

            for subtopic, keywords in subtopics.items():
                sub_score = sum(
                    1 for keyword in keywords
                    if keyword.lower() in text
                )

                field_score += sub_score

                if sub_score > best_sub_score:
                    best_sub_score = sub_score
                    best_subtopic = subtopic

            if field_score > domain_score:
                domain_score = field_score
                best_field = field

        scores.append(
            (
                domain_score,
                best_sub_score,
                domain,
                best_field,
                best_subtopic,
            )
        )

    scores.sort(reverse=True)

    _, _, domain, field, subtopic = scores[0]

    # 아무 키워드도 없으면 Other로 둔다.
    if scores[0][0] == 0:
        domain = "Other"
        field = ""
        subtopic = ""

    context_scores = {
        context: sum(
            1 for keyword in keywords
            if keyword.lower() in text
        )
        for context, keywords in CONTEXT_KEYWORDS.items()
    }

    context = max(
        context_scores,
        key=context_scores.get
    )

    if context_scores[context] == 0:
        context = ""

    matched_keywords = []

    if domain in TAXONOMY:
        for field_data in TAXONOMY[domain].values():
            for keywords in field_data.values():
                for keyword in keywords:
                    if keyword.lower() in text:
                        matched_keywords.append(keyword)

    matched_keywords = list(dict.fromkeys(matched_keywords))[:12]

    return {
        "primary_topic": domain,
        "field": field,
        "subtopic": subtopic,
        "context": context,
        "keywords": ", ".join(matched_keywords),
    }


def infer_question_type(prompt):
    """발문을 보고 아주 거칠게 문제 유형을 추정한다."""
    text = prompt.lower()

    if "요지" in text:
        return "요지"
    if "주장" in text:
        return "주장"
    if "제목" in text:
        return "제목"
    if "주제" in text:
        return "주제"
    if "목적" in text:
        return "목적"
    if "빈칸" in text:
        return "빈칸"
    if "순서" in text:
        return "순서"
    if "삽입" in text:
        return "문장 삽입"
    if "무관" in text:
        return "무관 문장"
    if "어법" in text:
        return "어법"
    if "어휘" in text:
        return "어휘"

    return "미분류"


# ============================================================
# 6. 데이터 누적 / 중복 제거
# ============================================================

COLUMNS = [
    "year",
    "grade",
    "exam",
    "question",
    "prompt",
    "passage",
    "vocab",
    "options",
    "question_type",
    "primary_topic",
    "field",
    "subtopic",
    "context",
    "keywords",
]


def make_unique_key(row):
    return (
        str(row.get("year", "")),
        str(row.get("grade", "")),
        str(row.get("exam", "")),
        str(row.get("question", "")),
    )


def merge_rows(old_rows, new_rows):
    """같은 연도/학년/시험/문항이면 새 분석 결과로 갱신한다."""
    combined = old_rows + new_rows

    result = {}

    for row in combined:
        result[make_unique_key(row)] = row

    return list(result.values())


# ============================================================
# 7. Session State
# ============================================================

if "corpus" not in st.session_state:
    st.session_state.corpus = []


# ============================================================
# 8. 사이드바
# ============================================================

st.sidebar.title("📄 PDF 추가")

uploaded_files = st.sidebar.file_uploader(
    "모의고사 PDF",
    type=["pdf"],
    accept_multiple_files=True,
)

if uploaded_files:
    if st.sidebar.button(
        "이 PDF 분석해서 추가",
        type="primary",
        use_container_width=True,
    ):
        added_rows = []

        for uploaded_file in uploaded_files:
            metadata = infer_metadata(uploaded_file.name)

            try:
                text = extract_pdf_text(uploaded_file)
                questions = split_questions(text)

                for number, block in questions:
                    parsed = parse_question(number, block)

                    combined_text = " ".join(
                        [
                            parsed["prompt"],
                            parsed["passage"],
                            parsed["vocab"],
                            parsed["options"],
                        ]
                    )

                    classification = classify(combined_text)

                    row = {
                        **metadata,
                        **parsed,
                        "question_type": infer_question_type(
                            parsed["prompt"]
                        ),
                        **classification,
                    }

                    added_rows.append(row)

            except Exception as e:
                st.sidebar.error(
                    f"{uploaded_file.name} 처리 실패: {e}"
                )

        st.session_state.corpus = merge_rows(
            st.session_state.corpus,
            added_rows,
        )

        st.sidebar.success(
            f"완료: {len(added_rows)}개 지문 추가 / "
            f"현재 총 {len(st.session_state.corpus)}개"
        )


# ============================================================
# 9. 저장 / 불러오기
# ============================================================

st.sidebar.divider()
st.sidebar.subheader("💾 저장 / 불러오기")

csv_file = st.sidebar.file_uploader(
    "기존 corpus CSV 불러오기",
    type=["csv"],
)

if csv_file:
    try:
        loaded = pd.read_csv(csv_file).fillna("")
        loaded_rows = loaded.to_dict("records")

        st.session_state.corpus = merge_rows(
            st.session_state.corpus,
            loaded_rows,
        )

        st.sidebar.success(
            f"CSV 불러오기 완료: 총 {len(st.session_state.corpus)}개"
        )

    except Exception as e:
        st.sidebar.error(f"CSV 불러오기 실패: {e}")


if st.session_state.corpus:
    df_save = pd.DataFrame(
        st.session_state.corpus,
        columns=COLUMNS,
    )

    st.sidebar.download_button(
        "⬇️ 현재 corpus 저장",
        data=df_save.to_csv(index=False).encode("utf-8-sig"),
        file_name="ksat_english_corpus.csv",
        mime="text/csv",
        use_container_width=True,
    )


# ============================================================
# 10. 메인 화면
# ============================================================

st.title("📚 Korean High School English Reading Corpus")

st.caption(
    "2006–2026 고1·고2·고3 영어 독해 지문 개인용 데이터베이스"
)

st.info(
    "왼쪽에서 PDF를 업로드하면 Listening 및 제외 문항을 제거한 뒤 "
    "독해 지문을 자동 분류합니다."
)


if not st.session_state.corpus:
    st.warning(
        "아직 저장된 지문이 없습니다. "
        "왼쪽에서 모의고사 PDF를 추가해 주세요."
    )
    st.stop()


# ============================================================
# 11. 검색 / 필터
# ============================================================

st.sidebar.divider()
st.sidebar.subheader("🔎 검색 / 필터")

df = pd.DataFrame(
    st.session_state.corpus,
    columns=COLUMNS,
).fillna("")

search = st.sidebar.text_input(
    "검색어",
    placeholder="예: memory, evolution, leadership",
)

year_options = sorted(
    [x for x in df["year"].unique() if str(x) != ""],
    reverse=True,
)

grade_options = sorted(
    [x for x in df["grade"].unique() if x]
)

primary_options = sorted(
    [x for x in df["primary_topic"].unique() if x]
)

field_options = sorted(
    [x for x in df["field"].unique() if x]
)

context_options = sorted(
    [x for x in df["context"].unique() if x]
)

selected_year = st.sidebar.selectbox(
    "연도",
    ["전체"] + year_options,
)

selected_grade = st.sidebar.selectbox(
    "학년",
    ["전체"] + grade_options,
)

selected_primary = st.sidebar.selectbox(
    "Primary Topic",
    ["전체"] + primary_options,
)

selected_field = st.sidebar.selectbox(
    "Field",
    ["전체"] + field_options,
)

selected_context = st.sidebar.selectbox(
    "Context",
    ["전체"] + context_options,
)


filtered = df.copy()

if search:
    mask = filtered.apply(
        lambda row: search.lower()
        in " ".join(str(x) for x in row.values).lower(),
        axis=1,
    )
    filtered = filtered[mask]

if selected_year != "전체":
    filtered = filtered[
        filtered["year"].astype(str) == str(selected_year)
    ]

if selected_grade != "전체":
    filtered = filtered[
        filtered["grade"] == selected_grade
    ]

if selected_primary != "전체":
    filtered = filtered[
        filtered["primary_topic"] == selected_primary
    ]

if selected_field != "전체":
    filtered = filtered[
        filtered["field"] == selected_field
    ]

if selected_context != "전체":
    filtered = filtered[
        filtered["context"] == selected_context
    ]


st.subheader(
    f"검색 결과: {len(filtered)}개 / 전체 {len(df)}개"
)


# ============================================================
# 12. 지문 표시 + 직접 수정
# ============================================================

for index, (_, row) in enumerate(filtered.iterrows()):

    title = (
        f"Q{row['question']} · "
        f"{row['year']} · "
        f"{row['grade']} · "
        f"{row['exam']} · "
        f"{row['primary_topic']}"
    )

    with st.expander(title, expanded=False):

        st.caption(
            f"연도: {row['year']} | "
            f"학년: {row['grade']} | "
            f"시험: {row['exam']} | "
            f"문항: Q{row['question']}"
        )

        # -----------------------------
        # 문제 / 본문
        # -----------------------------

        st.markdown("### 문제")

        prompt = st.text_area(
            "문제 발문",
            value=str(row["prompt"]),
            height=80,
            key=f"prompt_{index}",
        )

        st.markdown("### 본문")

        passage = st.text_area(
            "본문",
            value=str(row["passage"]),
            height=300,
            key=f"passage_{index}",
        )

        st.markdown("### 참고 영어단어")

        vocab = st.text_area(
            "참고 영어단어",
            value=str(row["vocab"]),
            height=100,
            key=f"vocab_{index}",
        )

        st.markdown("### 선지")

        options_text = st.text_area(
            "선지",
            value=str(row["options"]),
            height=180,
            key=f"options_{index}",
        )

        st.markdown("### 분류")

        col1, col2 = st.columns(2)

        with col1:
            primary_values = sorted(TAXONOMY.keys())

            current_primary = (
                row["primary_topic"]
                if row["primary_topic"] in primary_values
                else primary_values[0]
            )

            primary = st.selectbox(
                "Primary Topic",
                primary_values,
                index=primary_values.index(current_primary),
                key=f"primary_{index}",
            )

        with col2:
            field_values = sorted(
                TAXONOMY.get(primary, {}).keys()
            )

            if field_values:
                current_field = (
                    row["field"]
                    if row["field"] in field_values
                    else field_values[0]
                )

                field = st.selectbox(
                    "Field",
                    field_values,
                    index=field_values.index(current_field),
                    key=f"field_{index}",
                )
            else:
                field = ""

        subtopic_values = sorted(
            TAXONOMY.get(primary, {})
            .get(field, {})
            .keys()
        )

        current_subtopic = (
            row["subtopic"]
            if row["subtopic"] in subtopic_values
            else (
                subtopic_values[0]
                if subtopic_values
                else ""
            )
        )

        subtopic = st.selectbox(
            "Subtopic",
            [""] + subtopic_values,
            index=(
                0
                if not current_subtopic
                else subtopic_values.index(current_subtopic) + 1
            ),
            key=f"subtopic_{index}",
        )

        context = st.selectbox(
            "Context",
            [""] + sorted(CONTEXT_KEYWORDS.keys()),
            index=(
                0
                if not row["context"]
                else (
                    sorted(CONTEXT_KEYWORDS.keys()).index(
                        row["context"]
                    ) + 1
                    if row["context"] in CONTEXT_KEYWORDS
                    else 0
                )
            ),
            key=f"context_{index}",
        )

        question_type = st.text_input(
            "문항 유형",
            value=str(row["question_type"]),
            key=f"type_{index}",
        )

        keywords = st.text_input(
            "Keywords",
            value=str(row["keywords"]),
            key=f"keywords_{index}",
        )

        if st.button(
            "💾 이 지문 수정사항 저장",
            key=f"save_{index}",
            use_container_width=True,
        ):

            original_key = make_unique_key(row)

            for stored_row in st.session_state.corpus:

                if make_unique_key(stored_row) == original_key:

                    stored_row.update(
                        {
                            "prompt": prompt,
                            "passage": passage,
                            "vocab": vocab,
                            "options": options_text,
                            "question_type": question_type,
                            "primary_topic": primary,
                            "field": field,
                            "subtopic": subtopic,
                            "context": context,
                            "keywords": keywords,
                        }
                    )

                    break

            st.success("수정사항을 저장했습니다.")
            st.rerun()


# ============================================================
# 13. 현재 데이터 요약
# ============================================================

st.divider()

st.subheader("📊 현재 corpus")

summary_col1, summary_col2, summary_col3 = st.columns(3)

with summary_col1:
    st.metric(
        "전체 지문",
        len(st.session_state.corpus),
    )

with summary_col2:
    st.metric(
        "Primary Topic",
        df["primary_topic"].nunique(),
    )

with summary_col3:
    st.metric(
        "연도",
        df["year"].nunique(),
    )
