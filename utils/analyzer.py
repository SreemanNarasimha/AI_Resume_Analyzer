import spacy
from sentence_transformers import SentenceTransformer, util
import numpy as np

# Load models simply. 
# Streamlit will have pre-installed these from requirements.txt
try:
    NLP_SPACY = spacy.load("en_core_web_md")
except OSError:
    # Fallback for local development if you haven't downloaded it yet
    import os
    os.system("python -m spacy download en_core_web_md")
    NLP_SPACY = spacy.load("en_core_web_md")

NLP_BERT = SentenceTransformer('all-MiniLM-L6-v2')

# --- Predefined Keyword Dictionary ---
# Expanded list for better matching
TECH_SKILLS = {
    "python", "java", "c++", "javascript", "typescript", "html", "css", "sql", "nosql", 
    "react", "angular", "vue", "django", "flask", "fastapi", "spring boot", "node.js",
    "aws", "azure", "gcp", "docker", "kubernetes", "tensorflow", "pytorch", "scikit-learn",
    "pandas", "numpy", "git", "linux", "jenkins", "ci/cd", "rest api", "graphql", "machine learning",
    "deep learning", "nlp", "computer vision", "statistics", "data analysis", "big data"
}

SOFT_SKILLS = {
    "communication", "leadership", "teamwork", "problem solving", "critical thinking", 
    "time management", "adaptability", "creativity", "collaboration", "mentoring", 
    "presentation", "agile", "scrum", "negotiation", "conflict resolution", "emotional intelligence"
}

TOOLS_SOFTWARE = {
    "jira", "confluence", "slack", "trello", "asana", "microsoft office", "excel", 
    "power bi", "tableau", "visual studio code", "pycharm", "intellij", "eclipse", 
    "figma", "sketch", "adobe xd", "photoshop", "illustrator"
}

EDUCATION_KEYWORDS = {
    "bachelor", "master", "phd", "degree", "diploma", "certification", "certified", 
    "university", "college", "bootcamp", "bsc", "msc", "mba", "dba"
}

ACTION_VERBS = [
    "Architected", "Deployed", "Engineered", "Optimized", "Spearheaded", "Facilitated",
    "Orchestrated", "Developed", "Designed", "Implemented", "Executed", "Collaborated",
    "Analyzed", "Streamlined", "Pioneered", "Transformed", "Integrated", "Formulated"
]

def get_embeddings(text):
    """
    Generates vector embeddings for input text.
    """
    return NLP_BERT.encode(text, convert_to_tensor=True)

def calculate_similarity(resume_text, job_desc_text):
    """
    Calculates Cosine Similarity between Resume and JD embeddings.
    Math: Cosine Similarity = (A . B) / (||A|| * ||B||)
    Where A and B are the vector embeddings of the texts.
    Returns a score between 0 and 1.
    """
    embedding_resume = get_embeddings(resume_text)
    embedding_jd = get_embeddings(job_desc_text)
    
    # util.cos_sim returns a tensor, we convert to float
    similarity_score = util.cos_sim(embedding_resume, embedding_jd).item()
    return similarity_score

def extract_entities_and_keywords(text):
    """
    Extracts entities using Spacy NER and keywords using direct string matching
    against predefined categories.
    """
    doc = NLP_SPACY(text.lower())
    
    found_skills = {
        "Technical Skills": set(),
        "Soft Skills": set(),
        "Tools/Software": set(),
        "Education": set()
    }
    
    # 1. Spacy NER for specific entities (ORG, PRODUCT, GPE usually good for companies/tech)
    # Note: Spacy default models aren't perfect for all tech skills, so we combine with dictionary match
    # We mainly use NER here to potentially find things we missed or specific entities
    
    # 2. Dictionary / Token Matching (Lemmatized for robust matching)
    # We iterate over tokens to match single words, and checking n-grams is harder without a phrase matcher
    # For simplicity/speed in this prototype, we'll do substring checks on the cleaned text or set intersection
    
    # Efficient approach: Check presence of keywords in the text
    # A set intersection on tokens is faster
    tokens = set([token.text for token in doc])
    # Also include bigrams if needed, but 'spring boot' needs special handling
    
    # Helper to check phrases
    def check_keywords(keyword_set, category):
        for keyword in keyword_set:
            if keyword in text.lower(): # Simple substring match is often effective for multi-word skills like "machine learning"
                found_skills[category].add(keyword.title())

    check_keywords(TECH_SKILLS, "Technical Skills")
    check_keywords(SOFT_SKILLS, "Soft Skills")
    check_keywords(TOOLS_SOFTWARE, "Tools/Software")
    check_keywords(EDUCATION_KEYWORDS, "Education")
    
    return found_skills

def analyze_gap(resume_text, jd_text):
    """
    Performs the full semantic gap analysis.
    """
    # 1. Match Score
    match_score = calculate_similarity(resume_text, jd_text)
    
    # 2. Extract Skills
    resume_skills = extract_entities_and_keywords(resume_text)
    jd_skills = extract_entities_and_keywords(jd_text)
    
    # 3. Calculate "Visual" scores for the radar chart
    # We compare the MATCHING skills count vs JD skills count
    category_scores = {}
    gap_analysis = []
    
    for category in ["Technical Skills", "Soft Skills", "Tools/Software", "Education"]:
        r_set = resume_skills[category]
        j_set = jd_skills[category]
        
        # Avoid division by zero
        total_req = len(j_set)
        matches = r_set.intersection(j_set)
        missing = j_set - r_set
        
        # Score: How many of the REQUIRED skills does the resume have?
        if total_req > 0:
            score = len(matches) / total_req
        else:
            # If JD requires nothing in this category, do we give 100%?
            # Or maybe checking Resume strength independently?
            # Let's assume 1.0 (100%) if no requirements to meet.
            score = 1.0 if not j_set else 0.0
            
        category_scores[category] = {
            "Resume Score": score * 100, # Normalized to 0-100
             # For the radar chart, we might want to plot "Resume" vs "Job"
             # But "Job" is the benchmark (100%). 
             # Let's return raw counts for the chart or normalized? 
             # Requirement says: Compare "Resume Strength" vs "Job Requirement"
             # We will return the counts to let the visualizer handle normalizing if needed,
             # OR we return a score. Let's return the computed percentage match for that category.
            "Match Count": len(matches),
            "Total Required": total_req
        }
        
        # Populate Gap Table Data
        for skill in matches:
            gap_analysis.append({"Category": category, "Skill": skill, "Status": "Found", "Importance": "High"}) # Simplified importance
        for skill in missing:
            gap_analysis.append({"Category": category, "Skill": skill, "Status": "Missing", "Importance": "High"})

    return match_score, category_scores, gap_analysis, resume_skills, jd_skills

def get_improvement_suggestions(missing_skills):
    """
    Generates actionable bullet point suggestions for missing skills.
    Uses Semantic Similarity to pair the 'Missing Skill' with the best 'Action Verb'.
    """
    if not missing_skills:
        return []

    suggestions = []
    
    # Pre-encode all action verbs once
    verb_embeddings = NLP_BERT.encode(ACTION_VERBS, convert_to_tensor=True)

    for skill in missing_skills:
        # Encode the skill
        skill_embedding = NLP_BERT.encode(skill, convert_to_tensor=True)
        
        # Find best matching verb
        cosine_scores = util.cos_sim(skill_embedding, verb_embeddings)[0]
        best_verb_idx = np.argmax(cosine_scores.cpu().numpy())
        best_action_verb = ACTION_VERBS[best_verb_idx]
        
        # Create Suggestion
        # Heuristic: "Technical" skills often fit "Engineered/Deployed". Soft skills fit "Facilitated".
        # The model should naturally pick up on this semantic relationship.
        suggestions.append(f"{best_action_verb} {skill} to [Measurable Impact/Result].")
        
    return suggestions

def analyze_tone(text):
    """
    Analyzes the tone of the text by comparing it to defined tone archetypes.
    Returns the dominant tone and a confidence score.
    """
    # Tone Prototypes
    tones = {
        "Confident/Action-Oriented": [
            "Spearheaded successful project launch.",
            "Led cross-functional teams to victory.",
            "Achieved record-breaking results.",
            "Driven and ambitious professional.",
            "Executed strategic initiatives."
        ],
        "Academic/Research-Focused": [
            "Conducted extensive research.",
            "Analysis matches theoretical models.",
            "Published peer-reviewed papers.",
            "Investigated complex phenomena.",
            "Methodology involved quantitative analysis."
        ],
        "Managerial/Strategic": [
            "Optimized operational workflows.",
            "Strategic planning and execution.",
            "Mentored junior developers.",
            "Stakeholder management and reporting.",
            "Budget allocation and resource planning."
        ],
        "Passive/Weak": [
            "Helped with the project.",
            "Responsible for writing code.",
            "Worked on some tasks.",
            "Assisted the team lead.",
            "Did data entry."
        ]
    }
    
    # Encode text chunks (to avoid length limits and get local tone)
    # For simplicity, we encode the whole text and the prototypes
    text_emb = get_embeddings(text[:1000]) # First 1000 chars gives the "First Impression"
    
    tone_scores = {}
    
    for tone_name, sentences in tones.items():
        # Encode archetype sentences and average them
        prototype_emb = NLP_BERT.encode(sentences, convert_to_tensor=True)
        # Average vector
        avg_prototype = prototype_emb.mean(dim=0)
        
        # Sim
        score = util.cos_sim(text_emb, avg_prototype).item()
        tone_scores[tone_name] = score
        
    # Find max
    dominant_tone = max(tone_scores, key=tone_scores.get)
    return dominant_tone, tone_scores

def identify_irrelevant_content(resume_text, jd_text):
    """
    Identifies sentences or keywords in the resume that have low semantic similarity
    to the job description, suggesting "Fluff" removal.
    """
    # Split resume into sentence-like chunks for analysis
    # Spacy is good for sentence segmentation
    doc = NLP_SPACY(resume_text)
    sentences = [sent.text.strip() for sent in doc.sents if len(sent.text.split()) > 4] # Ignore very short segments
    
    if not sentences:
        return []

    # Get embeddings
    jd_embedding = get_embeddings(jd_text)
    sentence_embeddings = NLP_BERT.encode(sentences, convert_to_tensor=True)
    
    # Calculate similarity for each sentence against JD
    # We want to find the ones with lowest similarity scores
    cosine_scores = util.cos_sim(sentence_embeddings, jd_embedding)
    
    # Define a "Fluff" threshold (e.g., bottom 15% of relevance or absolute score < 0.1)
    # Visualizing top candidates for removal
    irrelevant_items = []
    
    # Convert tensors to list
    scores = cosine_scores.cpu().numpy().flatten()
    
    # Pair and sort
    scored_sentences = sorted(zip(sentences, scores), key=lambda x: x[1])
    
    # Return bottom 3-5 weak sentences
    for sent, score in scored_sentences[:5]:
        irrelevant_items.append({
             "text": sent,
             "score": float(score),
             "suggestion": "Consider removing or rephrasing to align with JD."
        })
        
    return irrelevant_items

