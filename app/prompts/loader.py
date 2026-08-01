from typing import Dict

class PromptLoader:
    """Manages prompt template structures and dynamic format renders."""
    
    # Store standard templates here or load from disk
    TEMPLATES: Dict[str, str] = {
        "candidate_extraction": (
            "You are an expert HR Parser. Extract the candidate's name, email, phone, skills, "
            "work experience, and education from this resume raw text: {raw_text}. Return structured JSON."
        ),
        "scoring_reasoning": (
            "Given the candidate profile details: {candidate_profile} and Job Description requirements: {job_description}, "
            "analyze matching status. Outline strengths, key mismatches, and justify scoring breakdown."
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
