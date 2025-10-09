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
    
    # Media context
    if media_type:
        context_parts.append(f"Media Type: {media_type}")
    
    # Hashtags
    if hashtags and len(hashtags) > 0:
        context_parts.append(f"Hashtags: {', '.join(hashtags[:5])}")
    
    # Mentions
    if mentions and len(mentions) > 0:
        context_parts.append(f"Mentions: {', '.join(mentions[:5])}")
    
    # Sponsored content
    if is_sponsored:
        context_parts.append("⚠️ This is sponsored/promotional content")
    
    # Build comprehensive prompt with cautious, professional tone
    prompt = f"""You are a senior immigration visa application auditor conducting a professional risk assessment of social media content for visa eligibility evaluation.

═══════════════════════════════════════════════════════════
PLATFORM: {platform}
POST IDENTIFIER: {post_id}
═══════════════════════════════════════════════════════════

CONTENT CONTEXT:
{chr(10).join(f"• {part}" for part in context_parts)}

═══════════════════════════════════════════════════════════
ANALYSIS MANDATE:
═══════════════════════════════════════════════════════════

You are evaluating this post for potential visa application risk. Your analysis must be:
• **PROFESSIONALLY CAUTIOUS** – Even seemingly safe content should note areas for improvement
• **NEVER PURELY POSITIVE** – Every post has room for enhancement or carries subtle risk
• **CONTEXT-SPECIFIC** – Reference exact keywords, locations, engagement metrics, tone, hashtags
• **EVALUATIVE & SERIOUS** – Use formal language befitting an official government review
• **VARIED IN WORDING** – Avoid repetitive phrasing; use synonyms and natural variation

═══════════════════════════════════════════════════════════
SECTION 1: CONTENT REINFORCEMENT
═══════════════════════════════════════════════════════════

Identify elements that **may** support visa credibility (but note limitations):
• Professional demonstrations, educational content, community involvement
• Family ties, cultural engagement, career-related activity
• Positive social contributions or humanitarian efforts

**IMPORTANT:**
- Even strong posts should have mild critique (e.g., "While this demonstrates engagement, clarity could be improved...")
- Reference specific details: engagement level, location, keywords, tone
- Provide an **actionable recommendation** to enhance credibility

═══════════════════════════════════════════════════════════
SECTION 2: CONTENT SUPPRESSION
═══════════════════════════════════════════════════════════

Identify elements that **could be misinterpreted** or raise concerns:
• Ambiguous context, missing captions, casual/unprofessional tone
• Political statements, controversial topics, alcohol/nightlife references
• Vague locations, sensitive regions, or culturally loaded symbolism
• Low engagement (may suggest limited social integration)
• High engagement (may suggest excessive social media focus)

**MISSING CAPTION HANDLING:**
If no caption: "No caption provided, which obscures intent and may raise questions about professionalism or purpose."
Alternative phrasing: "Absence of descriptive text limits context, creating ambiguity for reviewers."

**ENGAGEMENT INTERPRETATION:**
- High engagement (>1000 likes): "Significant visibility suggests strong social influence; ensure content consistently reflects professional conduct."
- Moderate engagement (100-1000): "Moderate reach indicates stable but not excessive social presence; acceptable but monitor tone."
- Low engagement (<100): "Limited visibility reduces risk of wide interpretation, though may suggest weak community ties."

**ALWAYS provide a caption improvement example** if caption is weak or missing:
Example format: "Consider adding: *'Honored to participate in the annual tech summit — moments like these reinforce my commitment to innovation and community building.'*"

**GEOPOLITICAL SENSITIVITY:**
If post location is in a region under diplomatic tension, conflict, or sanctions, note:
"Posts originating from [Region] may attract heightened scrutiny due to current geopolitical sensitivities; frame such content with diplomatic neutrality."

═══════════════════════════════════════════════════════════
SECTION 3: CONTENT FLAG
═══════════════════════════════════════════════════════════

Identify **high-risk elements** that could jeopardize approval:
• Violence, illegal activities, hate speech, extremist symbolism
• Security threats, false information, document fraud indicators
• Associations with sanctioned entities or restricted organizations

Even if no major flags exist, note **potential** concerns:
"While no overt red flags are present, the [casual tone/location/hashtag choice] warrants monitoring to ensure consistency with a professional visa application narrative."

═══════════════════════════════════════════════════════════
RISK SCORING GUIDELINES:
═══════════════════════════════════════════════════════════

Assign a risk score (0-100) where:
• 1-9: Very low risk, professional content with minor improvable areas
• 10-19: Low risk, acceptable but with noticeable areas for improvement
• 20-29: Moderate risk, contains ambiguous or mildly concerning elements
• 30-39: Elevated risk, multiple concerns or significant ambiguity
• 40+: High risk, contains problematic content requiring serious review

**BIAS TOWARD CAUTION**: When uncertain, score higher (e.g., missing caption = 20-30, not 5)

═══════════════════════════════════════════════════════════
OUTPUT FORMAT (VALID JSON ONLY):
═══════════════════════════════════════════════════════════

{{
  "content_reinforcement": {{
    "status": "Moderate|Positive|Needs Improvement",
    "reason": "<2-3 sentences referencing specific content details, with at least one caveat or limitation>",
    "recommendation": "<one specific, actionable suggestion to improve credibility>"
  }},
  "content_suppression": {{
    "status": "Safe|Caution|Risky",
    "reason": "<2-3 sentences explaining what could be misinterpreted, with specific references to caption/location/engagement/tone>",
    "recommendation": "<how to reduce risk; if caption is weak/missing, provide an example improved caption in italics>"
  }},
  "content_flag": {{
    "status": "Safe|Watch|High-Risk",
    "reason": "<2-3 sentences identifying any red flags or noting that while no major concerns exist, certain elements warrant monitoring>",
    "recommendation": "<guidance on maintaining compliance or addressing sensitivities>"
  }},
  "risk_score": <integer 1-100>
}}

**CRITICAL:** 
- Every field must be fully populated with unique, context-specific text
- Use varied phrasing (avoid saying "The post demonstrates..." repeatedly)
- Reference actual post details (keywords, hashtags, location, engagement numbers)
- Maintain a serious, evaluative, slightly skeptical tone throughout
- NEVER return purely positive analysis; always note improvements or concerns
    
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
                    "content": "You are an expert visa application reviewer. Return valid JSON only."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            temperature=0.7,  # Slight randomness for unique responses
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
        
        # Log success
        print(f"✅ {platform} analysis: "
              f"Reinforcement={result.get('content_reinforcement', {}).get('status')}, "
              f"Suppression={result.get('content_suppression', {}).get('status')}, "
              f"Flag={result.get('content_flag', {}).get('status')}, "
              f"Risk={result.get('risk_score')}")
        
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
        
        # Wrap analysis in platform key
        platform_key = platform.capitalize()
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


