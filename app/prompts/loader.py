class PromptLoader:
    """Manages prompt template structures and dynamic format renders."""

    TEMPLATES: dict[str, str] = {
        "candidate_extraction": (
            "You are an expert HR Parser. Extract the candidate's name, email, phone, skills, "
            "work experience, and education from this resume raw text: {raw_text}. Return structured JSON."
        ),
        "scoring_reasoning": (
            "Given the candidate profile details: {candidate_profile} and Job Description requirements: {job_description}, "
            "analyze matching status. Outline strengths, key mismatches, and justify scoring breakdown."
        ),
        "candidate_analysis": (
            "You are an expert Talent Acquisition Agent and technical recruiter.\n"
            "Analyze the candidate's resume relative to the target Job Description.\n\n"
            "Job Description:\n{job_description}\n\n"
            "Candidate Profile:\n{candidate_profile}\n\n"
            "Please perform a detailed comparison and output a structured Pydantic object containing:\n"
            "1. Strengths: key matching credentials, experiences, or project feats.\n"
            "2. Weaknesses: deficiencies in matching experience level or technical background.\n"
            "3. Missing Skills: tech stack components mentioned in the JD but absent from the candidate.\n"
            "4. Interview Questions: exactly 5 personalized questions to validate the candidate's real skill depth on gaps, projects, and work history.\n"
            "5. Learning Recommendations: tailored study plans/course suggestions to bridge their technical gap.\n"
            "6. Hiring Summary: qualitative overview of their match alignment.\n"
            "7. Recommendation: one of 'Strong Hire', 'Hire', 'Consider', 'Review', 'Reject' based on their matching profile."
        )
    }

    @classmethod
    def get_prompt(cls, key: str, **kwargs: str) -> str:
        """Retrieves and formats a template string.

        Args:
            key: Template identifier name.
            kwargs: String variables to inject into placeholders.

        Returns:
            Formatted prompt string.

        Raises:
            KeyError: If prompt template name is not registered.
        """
        template = cls.TEMPLATES.get(key)
        if not template:
            raise KeyError(f"Prompt template for key '{key}' not found.")
        return template.format(**kwargs)
