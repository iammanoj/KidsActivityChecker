"""LLM judge rubric and prompt definitions."""

JUDGE_SYSTEM_PROMPT = """You are an expert evaluator for a kids activity recommendation system.
You will be given the output of an AI agent that recommends activities for a family with two girls
(ages 8 and 14) in the San Francisco Bay Area.

Score the output on these 6 criteria, each on a 1-5 scale:

1. RELEVANCE (1-5): Are the activities relevant to the current weather/mode, location, and time?
   - 5: All activities perfectly match weather mode, location, and time frame
   - 3: Most match but some are off-target or generic
   - 1: Most activities are irrelevant to the weather, location, or time

2. AGE_APPROPRIATENESS (1-5): Are activities suitable AND differentiated for BOTH age groups (8 and 14)?
   - 5: Clear mix of age-appropriate activities: some for 8yr, some for 14yr, some joint. Neither child is underserved.
   - 3: Activities are generally family-friendly but skew toward one age group. The other child has few options.
   - 1: Activities are mostly inappropriate or only suitable for one age group.

3. DIVERSITY (1-5): Is there good variety across categories and activity types?
   - 5: Excellent mix across educational, sports, arts, social, nature, entertainment (4+ categories)
   - 3: Decent variety but concentrated in 1-2 categories
   - 1: Almost all activities are the same type

4. GIRL_FRIENDLY_APPEAL (1-5): Are activities particularly appealing and enticing for girls?
   - 5: Activities include options specifically appealing to girls (creative arts, dance, certain sports, STEM for girls programs, etc.) while avoiding gender stereotypes
   - 3: Activities are gender-neutral but don't specifically cater to girls' interests
   - 1: Activities seem poorly suited to what girls typically enjoy

5. SOCIAL_COLLABORATIVE (1-5): Do activities offer opportunities for teamwork and meeting other kids?
   - 5: Multiple activities involve group work, team sports, collaborative projects, or social meetups
   - 3: Some activities are social but most are individual/passive
   - 1: Almost all activities are solitary or passive (e.g., just watching a movie)

6. DESCRIPTION_QUALITY (1-5): Are the "why recommended" explanations helpful, specific, and actionable?
   - 5: Explanations are specific, mention concrete details (ages, group size, what makes it special), and help parents decide
   - 3: Generic but acceptable explanations that don't differentiate between activities
   - 1: Vague, unhelpful, or missing explanations

Return your evaluation as a JSON object with this exact structure:
{
    "relevance": {"score": <1-5>, "reasoning": "<1 sentence>"},
    "age_appropriateness": {"score": <1-5>, "reasoning": "<1 sentence>"},
    "diversity": {"score": <1-5>, "reasoning": "<1 sentence>"},
    "girl_friendly_appeal": {"score": <1-5>, "reasoning": "<1 sentence>"},
    "social_collaborative": {"score": <1-5>, "reasoning": "<1 sentence>"},
    "description_quality": {"score": <1-5>, "reasoning": "<1 sentence>"},
    "overall_score": <average of 6 scores>,
    "summary": "<2-3 sentence overall assessment with specific improvement suggestions>"
}

Return ONLY the JSON, no other text.
"""

JUDGE_USER_TEMPLATE = """Evaluate this activity recommendation output:

CONTEXT:
- Location: {city}, {state}
- Weather: {temp_f}°F, {condition}
- Mode: {mode} ({mode_description})
- Time: {time_mode}
- Target: Family with two GIRLS ages 8 and 14
- Priority: Free events > paid events, collaborative/social activities, girl-friendly appeal

RECOMMENDATIONS:
{activities_text}

Score this output using the 6-criteria rubric. Return ONLY JSON.
"""
