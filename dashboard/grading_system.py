"""
Letter Grade Conversion System for VisaGuardAI Risk Analysis

Maps numeric risk scores (0-100) to letter grades with color coding
for professional visa application risk assessment.
"""

def risk_score_to_letter_grade(score):
    """
    Convert numeric risk score (0-100) to letter grade with metadata.
    
    Args:
        score (int/float): Risk score from 0-100
        
    Returns:
        dict: {
            'grade': 'A+',
            'descriptor': 'Safe',
            'color': 'green',
            'emoji': '🟢',
            'tailwind_color': 'text-green-500',
            'bg_color': 'bg-green-900/20'
        }
    """
    score = int(score)
    
    # Grade mapping based on exact specification
    if score <= 2:
        grade = 'A+'
    elif score <= 7:
        grade = 'A'
    elif score <= 9:
        grade = 'A-'
    elif score <= 12:
        grade = 'B+'
    elif score <= 17:
        grade = 'B'
    elif score <= 19:
        grade = 'B-'
    elif score <= 22:
        grade = 'C+'
    elif score <= 27:
        grade = 'C'
    elif score <= 29:
        grade = 'C-'
    elif score <= 32:
        grade = 'D+'
    elif score <= 37:
        grade = 'D'
    elif score <= 39:
        grade = 'D-'
    else:  # >= 40
        grade = 'F'
    
    # Color coding based on grade
    if grade in ['A+', 'A', 'A-']:
        descriptor = 'Safe'
        color = 'green'
        emoji = '🟢'
        tailwind_color = 'text-green-500'
        bg_color = 'bg-green-900/20'
        border_color = 'border-green-500/30'
    elif grade in ['B+', 'B', 'B-', 'C+', 'C', 'C-']:
        descriptor = 'Caution'
        color = 'orange'
        emoji = '🟠'
        tailwind_color = 'text-yellow-500'
        bg_color = 'bg-yellow-900/20'
        border_color = 'border-yellow-500/30'
    else:  # D+, D, D-, F
        descriptor = 'High Risk'
        color = 'red'
        emoji = '🔴'
        tailwind_color = 'text-red-500'
        bg_color = 'bg-red-900/20'
        border_color = 'border-red-500/30'
    
    return {
        'grade': grade,
        'descriptor': descriptor,
        'color': color,
        'emoji': emoji,
        'tailwind_color': tailwind_color,
        'bg_color': bg_color,
        'border_color': border_color,
        'numeric_score': score
    }


def format_grade_display(score):
    """
    Format letter grade for display.
    
    Args:
        score (int/float): Risk score from 0-100
        
    Returns:
        str: Formatted display string like "B- (Caution) 🟠"
    """
    grade_info = risk_score_to_letter_grade(score)
    return f"{grade_info['grade']} ({grade_info['descriptor']}) {grade_info['emoji']}"


# Template filter version for Django templates
from django import template
register = template.Library()

@register.filter(name='to_letter_grade')
def to_letter_grade(score):
    """Template filter to convert risk score to grade info."""
    if score is None or score < 0:
        return {
            'grade': 'N/A',
            'descriptor': 'Unknown',
            'color': 'gray',
            'emoji': '⚪',
            'tailwind_color': 'text-gray-500',
            'bg_color': 'bg-gray-900/20',
            'border_color': 'border-gray-500/30',
            'numeric_score': -1
        }
    return risk_score_to_letter_grade(score)

@register.filter(name='format_grade')
def format_grade(score):
    """Template filter to format grade display."""
    if score is None or score < 0:
        return "N/A (Unknown) ⚪"
    return format_grade_display(score)

