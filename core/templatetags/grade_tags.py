from django import template

register = template.Library()


def score_to_grade(score):
    """
    Convert numeric risk score (0-100) to letter grade with band and emoji.
    
    Args:
        score: float or int - Risk score from 0-100
    
    Returns:
        dict with keys: grade, band, emoji, color
    """
    s = float(score or 0)
    
    # Mapping (0 treated as A+)
    if s <= 2:
        g, band = "A+", "Safe"
    elif s <= 7:
        g, band = "A", "Safe"
    elif s <= 9:
        g, band = "A-", "Safe"
    elif s <= 12:
        g, band = "B+", "Caution"
    elif s <= 17:
        g, band = "B", "Caution"
    elif s <= 19:
        g, band = "B-", "Caution"
    elif s <= 22:
        g, band = "C+", "Caution"
    elif s <= 27:
        g, band = "C", "Caution"
    elif s <= 29:
        g, band = "C-", "Caution"
    elif s <= 32:
        g, band = "D+", "High Risk"
    elif s <= 37:
        g, band = "D", "High Risk"
    elif s <= 39:
        g, band = "D-", "High Risk"
    else:
        g, band = "F", "High Risk"
    
    # Emoji and color based on band
    emoji = "🟢" if band == "Safe" else ("🟠" if band == "Caution" else "🔴")
    color = "text-green-400" if band == "Safe" else ("text-amber-400" if band == "Caution" else "text-red-400")
    
    return {
        "grade": g,
        "band": band,
        "emoji": emoji,
        "color": color
    }


@register.filter
def letter_grade(score):
    """
    Template filter to convert risk score to letter grade.
    
    Usage in template:
        {% with lg=instagram_obj.risk_score|letter_grade %}
            {{ lg.grade }} ({{ lg.band }}) {{ lg.emoji }}
        {% endwith %}
    """
    return score_to_grade(score)

