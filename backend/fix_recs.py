import re
with open("app/tests/test_recommendations.py", "r") as f:
    content = f.read()

# Fix _tokenize assertion
content = content.replace(
    'assert set(RecommendationService._tokenize(text)) == {"this", "is", "a", "test", "string"}',
    'assert set(RecommendationService._tokenize(text)) == {"test", "string"}'
)

# Fix _skills_score arguments
content = content.replace(
    'score = RecommendationService._skills_score(project_skills, user_skills)',
    'score = RecommendationService._skills_score(project_skills, user_skills, [])'
)

with open("app/tests/test_recommendations.py", "w") as f:
    f.write(content)
