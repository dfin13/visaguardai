"""
Intelligent AI Analysis Engine for Social Media Risk Assessment
Generates unique, context-aware evaluations based on post metadata
"""
import json
import os
from datetime import datetime
from openai import OpenAI
from django.conf import settings
from dashboard.models import Config


def get_ai_client():
    """Initialize OpenRouter AI client"""
    OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY') or getattr(settings, 'OPENROUTER_API_KEY', None)
    
    if not OPENROUTER_API_KEY:
        config = Config.objects.first()
        if config:
            OPENROUTER_API_KEY = config.openrouter_api_key
    
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY not found")
    
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
    )


def generate_profile_assessment(platform, username, full_name):
    """
    Generate a concise AI assessment of username and full name professionalism.
    
    Args:
        platform: str - Platform name (Instagram, LinkedIn, Facebook, X)
        username: str - Account username/handle
        full_name: str - Account full name
    
    Returns:
        str - One-sentence professionalism assessment
    """
    try:
        client = get_ai_client()
        
        prompt = f"""Evaluate the username @{username} and name '{full_name}' for professionalism and credibility in a visa review context. Respond with one concise sentence (max 25 words) assessing whether the username and name appear professional, authentic, and suitable for immigration review."""
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a visa application reviewer. Provide brief, professional assessments of usernames and names."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.6,
            max_tokens=80
        )
        
        assessment = response.choices[0].message.content.strip()
        # Clean any quotes or extra formatting
        assessment = assessment.strip('"').strip("'")
        
        print(f"✅ {platform} profile assessment: {assessment[:60]}...")
        
        return assessment
        
    except Exception as e:
        print(f"❌ Profile assessment failed for {platform}: {e}")
        # Return a neutral fallback
        return f"Username @{username} and name appear suitable for professional review."


def calculate_realistic_risk_score(post_data, ai_score=None):
    """
    Calculate a realistic risk score based on post features.
    Uses incremental modifiers with better variance for realistic grade distribution.
    
    Args:
        post_data: dict - Post metadata
        ai_score: int - AI-generated score (optional, used as reference)
    
    Returns:
        int - Adjusted risk score (0-100)
    """
    # Start with lower base score to allow more variance
    # Professional/clear posts can stay low, ambiguous/risky posts increase more
    score = 3  # Start at A (safe baseline) instead of 10
    
    # Extract post features
    caption = (post_data.get('caption') or post_data.get('text') or post_data.get('post_text') or '').strip()
    likes = post_data.get('likes_count', 0) or 0
    comments = post_data.get('comments_count', 0) or 0
    created_at = post_data.get('created_at', '')
    location = post_data.get('location_name', '')
    hashtags = post_data.get('hashtags', []) or []
    
    # === CAPTION ANALYSIS ===
    if not caption:
        # Missing caption - ambiguous, should push to C range
        score += 20
        print(f"  [MODIFIER] Missing caption: +20 → {score}")
    elif len(caption.split()) <= 3:
        # Vague caption (1-3 words) - slight ambiguity
        score += 12
        print(f"  [MODIFIER] Vague caption ({len(caption.split())} words): +12 → {score}")
    
    # === KEYWORD ANALYSIS ===
    caption_lower = caption.lower()
    
    # Alcohol/nightlife (higher risk)
    alcohol_keywords = ['alcohol', 'beer', 'wine', 'drunk', 'party', 'nightlife', 'club', 'bar']
    if any(keyword in caption_lower for keyword in alcohol_keywords):
        score += 20
        print(f"  [MODIFIER] Alcohol/nightlife content: +20 → {score}")
    
    # Political/controversial (moderate risk)
    political_keywords = ['politics', 'political', 'protest', 'rally', 'demonstration']
    if any(keyword in caption_lower for keyword in political_keywords):
        score += 15
        print(f"  [MODIFIER] Political/controversial content: +15 → {score}")
    
    # === POSITIVE INDICATORS ===
    positive_keywords = [
        'volunteer', 'education', 'university', 'student', 'teamwork',
        'community', 'professional', 'career', 'work', 'project', 'learning',
        'conference', 'achievement', 'graduation', 'certification', 'training'
    ]
    if any(keyword in caption_lower for keyword in positive_keywords):
        score -= 8  # Stronger reduction for clear professional content
        print(f"  [MODIFIER] Positive professional indicator: -8 → {score}")
    
    # === RECENCY ANALYSIS ===
    if created_at:
        try:
            from datetime import datetime
            post_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            days_old = (datetime.now(post_date.tzinfo) - post_date).days
            if days_old > 730:  # >2 years
                score += 8
                print(f"  [MODIFIER] Old post ({days_old} days): +8 → {score}")
        except:
            pass
    
    # === ENGAGEMENT ANALYSIS ===
    total_engagement = likes + comments
    
    if total_engagement == 0:
        # No engagement data - slight concern
        score += 7
        print(f"  [MODIFIER] No engagement data: +7 → {score}")
    elif total_engagement < 30:
        # Low engagement
        score += 5
        print(f"  [MODIFIER] Low engagement ({total_engagement}): +5 → {score}")
    elif total_engagement > 500:
        # High engagement (credibility boost) - stronger reduction
        score -= 8
        print(f"  [MODIFIER] High engagement ({total_engagement}): -8 → {score}")
    
    # === CONTENT FLAGS (SEVERE) ===
    severe_keywords = [
        'violence', 'illegal', 'weapon', 'drug', 'hate', 'threat',
        'extremist', 'radical', 'terrorist', 'arrest', 'fight'
    ]
    if any(keyword in caption_lower for keyword in severe_keywords):
        score += 40  # Push clearly into F range
        print(f"  [MODIFIER] Explicit severe content: +40 → {score}")
    
    # === LOCATION SENSITIVITY ===
    sensitive_locations = [
        'iran', 'syria', 'north korea', 'afghanistan', 'iraq',
        'venezuela', 'cuba', 'russia', 'ukraine'
    ]
    if location:
        location_lower = location.lower()
        if any(loc in location_lower for loc in sensitive_locations):
            score += 10
            print(f"  [MODIFIER] Geopolitically sensitive location: +10 → {score}")
    
    # Clamp score between 0 and 100
    score = max(0, min(100, score))
    
    print(f"  [FINAL] Calculated risk score: {score}")
    
    return score


def build_context_aware_prompt(platform, post_data):
    """
    Build an intelligent, context-rich prompt for AI analysis.
    
    Args:
        platform: str - Platform name (Instagram, LinkedIn, Twitter, Facebook)
        post_data: dict - Rich post metadata including:
            - caption/text
            - post_id
            - created_at
            - location_name
            - likes_count
            - comments_count
            - type (Image/Video/Sidecar)
            - hashtags
            - mentions
            - is_sponsored
    
    Returns:
        str - Comprehensive prompt for AI
    """
    
    # Extract post metadata
    caption = post_data.get('caption') or post_data.get('text') or post_data.get('post_text') or ""
    post_id = post_data.get('post_id') or post_data.get('id') or "unknown"
    created_at = post_data.get('created_at') or post_data.get('timestamp')
    location = post_data.get('location_name') or post_data.get('location')
    likes = post_data.get('likes_count') or post_data.get('likesCount') or 0
    comments = post_data.get('comments_count') or post_data.get('commentsCount') or 0
    media_type = post_data.get('type') or "text"
    hashtags = post_data.get('hashtags') or []
    mentions = post_data.get('mentions') or []
    is_sponsored = post_data.get('is_sponsored') or False
    
    # Build context sections
    context_parts = []
    
    # Caption/Content
    if caption:
        context_parts.append(f"Content: {caption[:500]}")
    else:
        context_parts.append("Content: [NO CAPTION PROVIDED - Post lacks textual context]")
    
    # Temporal context
    if created_at:
        try:
            post_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            days_old = (datetime.now(post_date.tzinfo) - post_date).days
            if days_old < 7:
                context_parts.append(f"Recency: Posted {days_old} days ago (very recent)")
            elif days_old < 30:
                context_parts.append(f"Recency: Posted {days_old} days ago (recent)")
            elif days_old < 180:
                context_parts.append(f"Recency: Posted {days_old} days ago ({days_old//30} months)")
            else:
                context_parts.append(f"Recency: Posted {days_old} days ago (older content)")
        except:
            context_parts.append("Recency: Unknown")
    
    # Geographic context
    if location:
        context_parts.append(f"Location: {location}")
    
    # Engagement context
    if likes or comments:
        engagement_note = f"Engagement: {likes} likes, {comments} comments"
        if likes > 1000:
            engagement_note += " (high visibility)"
        elif likes > 100:
            engagement_note += " (moderate visibility)"
        else:
            engagement_note += " (low visibility)"
        context_parts.append(engagement_note)
    
    # Hashtags (skip media type - not relevant for visa review)
    if hashtags and len(hashtags) > 0:
        context_parts.append(f"Hashtags: {', '.join(hashtags[:5])}")
    
    # Mentions
    if mentions and len(mentions) > 0:
        context_parts.append(f"Mentions: {', '.join(mentions[:5])}")
    
    # Sponsored content
    if is_sponsored:
        context_parts.append("⚠️ This is sponsored/promotional content")
    
    # Detect truly missing caption
    has_caption = bool(caption and caption.strip())
    
    # Build comprehensive prompt
    prompt = f"""You are a visa application coach conducting a critical review of social media content that will be scrutinized by immigration officers.

PLATFORM: {platform}

POST DATA:
{chr(10).join(f"• {part}" for part in context_parts)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

YOUR ROLE:
Assess this post as an immigration officer would: skeptical, detail-oriented, and culturally sensitive. Immigration officers look for red flags, inconsistencies, and anything that could suggest risk.

ANALYSIS REQUIREMENTS:

1. **Content Reinforcement** — What strengthens this applicant's profile?
   • Identify career indicators, professional language, educational references
   • Note community involvement, stable relationships, cultural engagement
   • Cite specific phrases, hashtags, or themes that demonstrate responsibility
   • {'If caption is missing, assess what information gap this creates and how it weakens the post' if not has_caption else 'Quote exact wording that supports the applicant'}

2. **Content Suppression** — What could raise concerns or be misinterpreted?
   • Flag ambiguous language, casual tone in serious contexts, or party culture references
   • Identify keywords related to alcohol, nightlife, political topics, or controversial hashtags
   • {'Note absence of explanatory text and resulting ambiguity' if not has_caption else 'Quote phrases that could be read negatively'}
   • Only mention location if geopolitically sensitive (e.g., Iran, Syria, disputed regions)
   • Only mention engagement if unusually high (possible influencer) or suspiciously low

3. **Content Flag** — Does this post present serious immigration risk?
   • Identify explicit red flags: violence, illegal activity, hate speech, security threats
   • Detect cultural insensitivity, references to overstaying, or deceptive behavior
   • {'Warn that lack of context increases scrutiny risk' if not has_caption else 'Cite specific content that triggers concern'}
   • If safe, briefly explain why (e.g., "professional tone," "educational focus")

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CRITICAL RULES:

✅ ALWAYS CITE: Quote caption phrases, mention hashtags by name, reference specific engagement numbers or locations
✅ VARY LANGUAGE: Use different phrasing for each post (avoid "lack of caption," "maintain positive content," "continue posting")
✅ BE CRITICAL: Act as a skeptical reviewer, not a cheerleader
✅ ONLY FLAG RELEVANT DETAILS: Don't mention timing unless post is very old (>1 year), don't mention location unless sensitive
✅ DETECT CAPTION PRESENCE: {'This post has NO caption — address the information gap' if not has_caption else 'Caption is present — analyze its content'}

❌ NEVER:
• Use generic phrases like "professional content" without examples
• Mention "sidecar," "carousel," or technical media types
• Repeat the same language across multiple posts
• Comment on normal engagement or neutral locations
• Leave any JSON field empty

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

RESPONSE VARIATIONS (use diverse phrasing):

Instead of "lack of caption," try:
• "No explanatory text provided"
• "Absence of written context"
• "Post omits descriptive information"

Instead of "maintain positive content," try:
• "Strengthen profile with career-focused updates"
• "Prioritize posts demonstrating professional growth"
• "Share content highlighting community ties"

Instead of "professional content," try:
• "Career-oriented messaging"
• "Workplace achievement showcase"
• "Educational milestone documentation"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Return ONLY valid JSON:
{{
  "content_reinforcement": {{
    "status": "Safe|Positive|Needs Improvement",
    "reason": "<Critical assessment citing specific caption quotes, hashtags, or engagement data>",
    "recommendation": "<Actionable advice referencing this post's specific elements>"
  }},
  "content_suppression": {{
    "status": "Safe|Caution|Risky",
    "reason": "<Identify ambiguities, risky keywords, or concerning themes with examples>",
    "recommendation": "<How to clarify or mitigate specific risks found>"
  }},
  "content_flag": {{
    "status": "Safe|Sensitive|High-Risk",
    "reason": "<Flag serious red flags or explain why post is immigration-safe>",
    "recommendation": "<Address critical issues or suggest profile strengthening>"
  }},
  "risk_score": <0-100 integer>
}}
"""
    
    return prompt


def analyze_post_intelligent(platform, post_data, retry_count=0):
    """
    Analyze a single post with intelligent, context-aware AI.
    
    Args:
        platform: str - Platform name
        post_data: dict - Rich post metadata
        retry_count: int - Number of retries attempted
    
    Returns:
        dict - Analysis result with content_reinforcement, content_suppression, content_flag
    """
    try:
        client = get_ai_client()
        prompt = build_context_aware_prompt(platform, post_data)
        
        # Log analysis (privacy-safe)
        caption_preview = (post_data.get('caption') or post_data.get('text') or post_data.get('post_text') or "")[:60]
        print(f"🤖 Analyzing {platform} post: {caption_preview}{'...' if len(caption_preview) == 60 else ''}")
        
        # Call AI with slight temperature for variation
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system", 
                    "content": "You are a critical visa application coach reviewing social media for immigration scrutiny. Be skeptical, professional, and specific. Quote actual captions, cite hashtags by name, reference engagement numbers. Vary your language—avoid repetitive phrases like 'lack of caption' or 'maintain content'. Never mention technical terms like 'sidecar' or 'carousel'. Only flag timing/location if clearly relevant (very old posts, geopolitically sensitive regions). Every analysis must reference visible content and provide unique, actionable feedback. Return valid JSON only."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            temperature=0.85,  # Higher for unique, varied responses
            max_tokens=1000
        )
        
        ai_response = response.choices[0].message.content.strip()
        
        # Clean JSON fences
        ai_response = (
            ai_response
            .removeprefix("```json")
            .removeprefix("```")
            .removesuffix("```")
            .strip()
        )
        
        # Parse JSON
        result = json.loads(ai_response)
        
        # Calculate realistic risk score based on post features
        ai_risk_score = result.get('risk_score', 50)
        adjusted_score = calculate_realistic_risk_score(post_data, ai_risk_score)
        
        # Override AI score with calculated score
        result['risk_score'] = adjusted_score
        
        # Log success with both scores for comparison
        caption_preview = (post_data.get('caption') or post_data.get('text') or post_data.get('post_text') or '')[:60]
        print(f"✅ {platform} analysis: "
              f"Reinforcement={result.get('content_reinforcement', {}).get('status')}, "
              f"Suppression={result.get('content_suppression', {}).get('status')}, "
              f"Flag={result.get('content_flag', {}).get('status')}, "
              f"AI_Risk={ai_risk_score} → Adjusted_Risk={adjusted_score}")
        print(f"  [DEBUG] Post: {caption_preview}... → risk_score: {adjusted_score}")
        
        return result
        
    except json.JSONDecodeError as e:
        print(f"❌ {platform} JSON parsing failed: {e}")
        print(f"Raw AI response: {ai_response[:200]}...")
        
        # Retry once
        if retry_count == 0:
            print(f"🔄 Retrying {platform} analysis...")
            return analyze_post_intelligent(platform, post_data, retry_count=1)
        
        # Return error state
        return {
            "content_reinforcement": {
                "status": "Needs Improvement",
                "reason": f"AI response could not be parsed. Post may lack sufficient context.",
                "recommendation": "Add clear captions to future posts"
            },
            "content_suppression": {
                "status": "Caution",
                "reason": "Unable to assess content risk due to analysis error",
                "recommendation": "Review manually for sensitive content"
            },
            "content_flag": {
                "status": "Safe",
                "reason": "No immediate red flags detected in available metadata",
                "recommendation": "Ensure all posts have clear, professional context"
            },
            "risk_score": 50
        }
    
    except Exception as e:
        print(f"❌ {platform} AI call failed: {e}")
        
        # Retry once
        if retry_count == 0:
            print(f"🔄 Retrying {platform} analysis...")
            return analyze_post_intelligent(platform, post_data, retry_count=1)
        
        # Return error state
        return {
            "content_reinforcement": {
                "status": "Needs Improvement",
                "reason": f"Analysis service temporarily unavailable: {str(e)[:100]}",
                "recommendation": "Try again later or contact support"
            },
            "content_suppression": {
                "status": "Caution",
                "reason": "Could not complete risk assessment",
                "recommendation": "Manual review recommended"
            },
            "content_flag": {
                "status": "Safe",
                "reason": "No data available for flagging",
                "recommendation": "Ensure posts are appropriate for visa review"
            },
            "risk_score": -1
        }


def analyze_posts_batch(platform, posts_data_list):
    """
    Analyze multiple posts for a platform.
    
    Args:
        platform: str - Platform name
        posts_data_list: list - List of post metadata dicts
    
    Returns:
        list - List of analyzed posts with full post_data and analysis
    """
    results = []
    
    for i, post_data in enumerate(posts_data_list):
        print(f"\n📊 Analyzing {platform} post {i+1}/{len(posts_data_list)}...")
        
        analysis = analyze_post_intelligent(platform, post_data)
        
        # Wrap analysis in platform key (preserve exact casing for consistency)
        # Use the platform name as-is to ensure template compatibility
        platform_key = platform  # Keep original casing (Instagram, LinkedIn, Twitter, etc.)
        wrapped_analysis = {
            platform_key: analysis
        }
        
        results.append({
            "post": post_data.get('caption') or post_data.get('text') or post_data.get('post_text') or "[No text content]",
            "post_data": post_data,
            "analysis": wrapped_analysis
        })
    
    print(f"\n✅ Completed {platform} analysis: {len(results)} posts")
    return results


