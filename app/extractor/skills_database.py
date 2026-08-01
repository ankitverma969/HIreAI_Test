
# Canonical Skill Taxonomy mapping synonyms to standardized designations
SKILL_SYNONYMS: dict[str, str] = {
    # Programming
    "python": "Python", "py": "Python",
    "javascript": "JavaScript", "js": "JavaScript", "java script": "JavaScript",
    "typescript": "TypeScript", "ts": "TypeScript",
    "golang": "Go", "go": "Go",
    "rust": "Rust",
    "c++": "C++", "cpp": "C++",
    "c#": "C#", "csharp": "C#",
    "java": "Java",
    "ruby": "Ruby", "rails": "Ruby on Rails",
    "php": "PHP",
    "swift": "Swift",
    "kotlin": "Kotlin",
    "scala": "Scala",
    "sql": "SQL", "mysql": "MySQL", "postgresql": "PostgreSQL", "postgres": "PostgreSQL",
    "html": "HTML", "html5": "HTML", "css": "CSS", "css3": "CSS", "sass": "SASS", "scss": "SASS",

    # Frameworks
    "react": "React", "reactjs": "React", "react.js": "React",
    "angular": "Angular", "angularjs": "Angular",
    "vue": "Vue.js", "vuejs": "Vue.js", "vue.js": "Vue.js",
    "nextjs": "Next.js", "next.js": "Next.js",
    "nodejs": "Node.js", "node.js": "Node.js", "node": "Node.js",
    "express": "Express.js", "expressjs": "Express.js",
    "django": "Django",
    "flask": "Flask",
    "fastapi": "FastAPI",
    "spring": "Spring Boot", "springboot": "Spring Boot", "spring boot": "Spring Boot",
    "asp.net": "ASP.NET", "dotnet": "ASP.NET", ".net": "ASP.NET",

    # Cloud & DevOps
    "aws": "AWS", "amazon web services": "AWS",
    "azure": "Azure", "microsoft azure": "Azure",
    "gcp": "GCP", "google cloud": "GCP", "google cloud platform": "GCP",
    "docker": "Docker",
    "kubernetes": "Kubernetes", "k8s": "Kubernetes",
    "terraform": "Terraform",
    "jenkins": "Jenkins",
    "ansible": "Ansible",
    "git": "Git", "github": "Git", "gitlab": "Git",
    "ci/cd": "CI/CD", "cicd": "CI/CD", "continuous integration": "CI/CD",

    # Databases
    "mongodb": "MongoDB", "mongo": "MongoDB",
    "redis": "Redis",
    "sqlite": "SQLite",
    "oracle": "Oracle",
    "cassandra": "Cassandra",
    "dynamodb": "DynamoDB",

    # AI / ML & Data Science
    "machine learning": "Machine Learning", "ml": "Machine Learning",
    "deep learning": "Deep Learning", "dl": "Deep Learning",
    "nlp": "Natural Language Processing", "natural language processing": "Natural Language Processing",
    "llm": "LLMs", "llms": "LLMs", "large language models": "LLMs",
    "pytorch": "PyTorch",
    "tensorflow": "TensorFlow", "tf": "TensorFlow",
    "keras": "Keras",
    "scikit-learn": "Scikit-Learn", "scikit learn": "Scikit-Learn", "sklearn": "Scikit-Learn",
    "pandas": "Pandas",
    "numpy": "NumPy",
    "scipy": "SciPy",
    "langchain": "LangChain",
    "huggingface": "Hugging Face", "hugging face": "Hugging Face",
    "openai": "OpenAI",
    "data science": "Data Science", "data analysis": "Data Science",

    # Testing
    "pytest": "Pytest",
    "jest": "Jest",
    "selenium": "Selenium",
    "cypress": "Cypress",
    "junit": "JUnit",
    "postman": "Postman",

    # Tools & Methods
    "jira": "Jira",
    "confluence": "Confluence",
    "trello": "Trello",
    "slack": "Slack",
    "vs code": "VS Code", "vscode": "VS Code"
}

# Mapping of standardized canonical skills to their high-level category
SKILL_CATEGORIES: dict[str, str] = {
    "Python": "Programming", "JavaScript": "Programming", "TypeScript": "Programming",
    "Go": "Programming", "Rust": "Programming", "C++": "Programming", "C#": "Programming",
    "Java": "Programming", "Ruby": "Programming", "PHP": "Programming", "Swift": "Programming",
    "Kotlin": "Programming", "Scala": "Programming", "SQL": "Programming",
    "HTML": "Programming", "CSS": "Programming", "SASS": "Programming",

    "React": "Frameworks", "Angular": "Frameworks", "Vue.js": "Frameworks",
    "Next.js": "Frameworks", "Node.js": "Frameworks", "Express.js": "Frameworks",
    "Django": "Frameworks", "Flask": "Frameworks", "FastAPI": "Frameworks",
    "Spring Boot": "Frameworks", "ASP.NET": "Frameworks", "Ruby on Rails": "Frameworks",

    "AWS": "Cloud", "Azure": "Cloud", "GCP": "Cloud",
    "Docker": "DevOps", "Kubernetes": "DevOps", "Terraform": "DevOps",
    "Jenkins": "DevOps", "Ansible": "DevOps", "Git": "DevOps", "CI/CD": "DevOps",

    "MongoDB": "Databases", "Redis": "Databases", "SQLite": "Databases",
    "Oracle": "Databases", "Cassandra": "Databases", "DynamoDB": "Databases",
    "MySQL": "Databases", "PostgreSQL": "Databases",

    "Machine Learning": "AI/ML", "Deep Learning": "AI/ML", "Natural Language Processing": "AI/ML",
    "LLMs": "AI/ML", "PyTorch": "AI/ML", "TensorFlow": "AI/ML", "Keras": "AI/ML",
    "Scikit-Learn": "AI/ML", "Pandas": "Data Science", "NumPy": "Data Science",
    "SciPy": "Data Science", "LangChain": "AI/ML", "Hugging Face": "AI/ML",
    "OpenAI": "AI/ML", "Data Science": "Data Science",

    "Pytest": "Testing", "Jest": "Testing", "Selenium": "Testing",
    "Cypress": "Testing", "JUnit": "Testing", "Postman": "Testing",

    "Jira": "Tools", "Confluence": "Tools", "Trello": "Tools",
    "Slack": "Tools", "VS Code": "Tools"
}

def get_canonical_skill(skill_raw: str) -> str | None:
    """Resolves a raw skill mention to its standard canonical taxonomy name.

    Args:
        skill_raw: Extracted raw skill string.

    Returns:
        Canonical name if matched in database, otherwise None.
    """
    normalized = skill_raw.strip().lower()
    return SKILL_SYNONYMS.get(normalized)


def get_skill_category(canonical_name: str) -> str:
    """Returns the taxonomy category for a canonical skill.

    Args:
        canonical_name: Canonical skill string.

    Returns:
        The matched category string, default 'Tools'.
    """
    return SKILL_CATEGORIES.get(canonical_name, "Tools")
