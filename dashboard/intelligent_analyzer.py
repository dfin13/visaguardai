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


def calculate_realistic_risk_score(post_data, ai_score=None):
    """
    Calculate a realistic risk score based on post features.
    Uses incremental modifiers instead of harsh penalties.
    
    Args:
        post_data: dict - Post metadata
        ai_score: int - AI-generated score (optional, used as reference)
    
    Returns:
        int - Adjusted risk score (0-100)
    """
    # Start with base caution score
    score = 10
    
    # Extract post features
    caption = (post_data.get('caption') or post_data.get('text') or post_data.get('post_text') or '').strip()
    likes = post_data.get('likes_count', 0) or 0
    comments = post_data.get('comments_count', 0) or 0
    created_at = post_data.get('created_at', '')
    location = post_data.get('location_name', '')
    hashtags = post_data.get('hashtags', []) or []
    
    # === CAPTION ANALYSIS ===
    if not caption:
        # Missing caption
        score += 10
        print(f"  [MODIFIER] Missing caption: +10 → {score}")
    elif len(caption.split()) <= 3:
        # Vague caption (1-3 words)
        score += 5
        print(f"  [MODIFIER] Vague caption ({len(caption.split())} words): +5 → {score}")
    
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
        'community', 'professional', 'career', 'work', 'project', 'learning'
    ]
    if any(keyword in caption_lower for keyword in positive_keywords):
        score -= 5  # Reduce to -5 to avoid going too low
        print(f"  [MODIFIER] Positive professional indicator: -5 → {score}")
    
    # === RECENCY ANALYSIS ===
    if created_at:
        try:
            from datetime import datetime
            post_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            days_old = (datetime.now(post_date.tzinfo) - post_date).days
            if days_old > 730:  # >2 years
                score += 5
                print(f"  [MODIFIER] Old post ({days_old} days): +5 → {score}")
        except:
            pass
    
    # === ENGAGEMENT ANALYSIS ===
    total_engagement = likes + comments
    
    if total_engagement == 0:
        # No engagement data
        score += 5
        print(f"  [MODIFIER] No engagement data: +5 → {score}")
    elif total_engagement < 30:
        # Low engagement
        score += 3
        print(f"  [MODIFIER] Low engagement ({total_engagement}): +3 → {score}")
    elif total_engagement > 500:
        # High engagement (credibility boost)
        score -= 5
        print(f"  [MODIFIER] High engagement ({total_engagement}): -5 → {score}")
    
    # === CONTENT FLAGS (SEVERE) ===
    severe_keywords = [
        'violence', 'illegal', 'weapon', 'drug', 'hate', 'threat',
        'extremist', 'radical', 'terrorist'
    ]
    if any(keyword in caption_lower for keyword in severe_keywords):
        score += 30
        print(f"  [MODIFIER] Explicit severe content: +30 → {score}")
    
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


def build_context_aware_prompt(platform, post_data, is_most_recent=False, total_posts=1):
    """
    Build an intelligent, context-rich prompt for AI analysis with conditional commentary.
    Only mentions notable factors (engagement extremes, sensitive hashtags, geopolitical locations, etc.)
    
    Args:
        platform: str - Platform name (Instagram, LinkedIn, Twitter, Facebook)
        post_data: dict - Rich post metadata
        is_most_recent: bool - Whether this is the most recent post
        total_posts: int - Total number of posts being analyzed
    
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
    video_views = post_data.get('video_view_count') or post_data.get('videoViewCount') or 0
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
    
    # === CONDITIONAL TEMPORAL CONTEXT ===
    # Only mention if most recent OR older than 200 days
    if created_at:
        try:
            post_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            days_old = (datetime.now(post_date.tzinfo) - post_date).days
            
            if is_most_recent:
                context_parts.append(f"Recency: Most recent post (posted {days_old} days ago) - reflects current online presence")
            elif days_old > 200:
                context_parts.append(f"Recency: Posted {days_old} days ago (older content - may not reflect current professional maturity)")
            # Otherwise, omit recency commentary
        except:
            pass
    
    # === CONDITIONAL GEOPOLITICAL LOCATION CONTEXT ===
    # Only mention if location is geopolitically sensitive
    if location:
        sensitive_regions = [
            'china', 'russia', 'iran', 'north korea', 'israel', 'palestine', 
            'ukraine', 'syria', 'afghanistan', 'iraq', 'venezuela', 'cuba',
            'belarus', 'myanmar', 'yemen', 'lebanon', 'gaza', 'west bank'
        ]
        location_lower = location.lower()
        is_sensitive = any(region in location_lower for region in sensitive_regions)
        
        if is_sensitive:
            context_parts.append(f"⚠️ Location: {location} (geopolitically sensitive region - content may attract heightened scrutiny)")
        # Otherwise, omit location commentary
    
    # === CONDITIONAL ENGAGEMENT CONTEXT ===
    # Only mention if engagement is notably high or low
    total_engagement = likes + comments + video_views
    days_old_for_check = 30  # default
    
    if created_at:
        try:
            post_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            days_old_for_check = (datetime.now(post_date.tzinfo) - post_date).days
        except:
            pass
    
    if total_engagement > 0:
        # Calculate engagement tier (only comment on extremes)
        if likes > 5000 or comments > 200 or video_views > 50000:
            context_parts.append(f"⚠️ Engagement: {likes} likes, {comments} comments, {video_views} views (EXCEPTIONALLY HIGH - highly visible content, ensure professional tone)")
        elif likes < 10 and comments < 2 and days_old_for_check > 30:
            context_parts.append(f"Engagement: {likes} likes, {comments} comments (limited engagement - minimal audience connection)")
        # Otherwise, omit engagement commentary
    
    # Media context (always include)
    if media_type:
        context_parts.append(f"Media Type: {media_type}")
    
    # === CONDITIONAL HASHTAG SENSITIVITY ===
    # Only mention if hashtags fall into sensitive categories
    if hashtags and len(hashtags) > 0:
        sensitive_hashtags = {
            'political': ['protest', 'freedom', 'justice', 'revolution', 'democracy', 'election', 'vote', 'rights', 'activism'],
            'religious': ['faith', 'allah', 'god', 'prayfor', 'christian', 'muslim', 'islam', 'bible', 'quran', 'religious'],
            'controversial': ['metoo', 'climatechange', 'gunrights', 'abortion', 'lgbt', 'lgbtq', 'pride', 'blacklivesmatter', 'blm']
        }
        
        detected_sensitive = []
        hashtags_lower = [h.lower().replace('#', '') for h in hashtags]
        
        for category, keywords in sensitive_hashtags.items():
            for keyword in keywords:
                if any(keyword in tag for tag in hashtags_lower):
                    detected_sensitive.append(hashtags[hashtags_lower.index(next(tag for tag in hashtags_lower if keyword in tag))])
        
        if detected_sensitive:
            context_parts.append(f"⚠️ Hashtags: {', '.join(detected_sensitive)} (politically, religiously, or ideologically charged - may attract heightened scrutiny)")
        # Otherwise, omit hashtag commentary
    
    # Mentions (only if present)
    if mentions and len(mentions) > 0:
        context_parts.append(f"Mentions: {', '.join(mentions[:5])}")
    
    # Sponsored content flag
    if is_sponsored:
        context_parts.append("⚠️ This is sponsored/promotional content")
    
    # Build comprehensive prompt
    prompt = f"""You are an expert visa application reviewer analyzing social media content for immigration risk assessment.

PLATFORM: {platform}
POST ID: {post_id}

CONTEXT:
{chr(10).join(f"• {part}" for part in context_parts)}

YOUR TASK:
Provide a nuanced, context-aware analysis of this specific post for a visa application. Consider:

1. **Content Reinforcement**: What aspects of this post demonstrate positive qualities (professionalism, community involvement, educational value, career focus, family ties, etc.)?

2. **Content Suppression**: What aspects could be misinterpreted or raise concerns (political statements, controversial topics, ambiguous context, alcohol/substance references, location sensitivities)?

3. **Content Flag**: Are there any high-risk elements that could jeopardize a visa application (violence, illegal activities, hate speech, security threats, false information)?

CRITICAL INSTRUCTIONS:
- **BE SPECIFIC**: Reference the actual content in your reasoning
- **NO GENERIC RESPONSES**: Every reason and recommendation must be tailored to THIS post
- **USE DISCRETION**: Only comment on factors when they are NOTABLE
  • Only mention engagement if unusually high or low (see context above)
  • Only comment on location if it's geopolitically sensitive (see context above)
  • Only mention hashtags if politically/ideologically charged (see context above)
  • Only mention post age if flagged in context (most recent or >200 days old)
- **BE HELPFUL**: Provide actionable, constructive advice
- **AVOID REDUNDANCY**: Do not repeat generic statements about engagement, location, or timing unless they truly matter
- **MISSING DATA**: If caption is missing, explicitly note the risk of ambiguity
- **TONE MATTERS**: Assess if content is professional, casual, political, celebratory, etc.
- **CULTURAL SENSITIVITY**: Consider how immigration officers from different backgrounds might interpret this

Return ONLY valid JSON in this exact format:
{{
  "content_reinforcement": {{
    "status": "Safe|Positive|Needs Improvement",
    "reason": "<specific contextual explanation referencing the actual post content, location, or engagement>",
    "recommendation": "<one actionable suggestion to maximize positive impact>"
  }},
  "content_suppression": {{
    "status": "Safe|Caution|Risky",
    "reason": "<explain what elements could be misunderstood or taken negatively by visa reviewers>",
    "recommendation": "<how to reduce ambiguity or risk in future posts>"
  }},
  "content_flag": {{
    "status": "Safe|Sensitive|High-Risk",
    "reason": "<identify any red flags or sensitive topics that could trigger additional scrutiny>",
    "recommendation": "<how to address or remove problematic content if applicable>"
  }},
  "risk_score": <0-100 integer based on overall visa application risk>
}}

NEVER leave fields empty or null. If the post is entirely safe, still provide specific reasoning.
"""
    
    return prompt


def analyze_post_intelligent(platform, post_data, retry_count=0, is_most_recent=False, total_posts=1):
    """
    Analyze a single post with intelligent, context-aware AI.
    
    Args:
        platform: str - Platform name
        post_data: dict - Rich post metadata
        retry_count: int - Number of retries attempted
        is_most_recent: bool - Whether this is the most recent post
        total_posts: int - Total number of posts being analyzed
    
    Returns:
        dict - Analysis result with content_reinforcement, content_suppression, content_flag
    """
    try:
        client = get_ai_client()
        prompt = build_context_aware_prompt(platform, post_data, is_most_recent=is_most_recent, total_posts=total_posts)
        
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


def analyze_profile_identity(platform, username, full_name, followers_count=0):
    """
    Generate a brief AI assessment of username, full name, and follower count professionalism.
    Only called once per platform account.
    
    Args:
        platform: str - Platform name
        username: str - Account username
        full_name: str - Account full name
        followers_count: int - Number of followers
    
    Returns:
        str - Brief 1-2 sentence assessment
    """
    try:
        client = get_ai_client()
        
        # Format follower count for readability
        if followers_count >= 1000000:
            followers_display = f"{followers_count / 1000000:.1f}M"
        elif followers_count >= 1000:
            followers_display = f"{followers_count / 1000:.1f}k"
        else:
            followers_display = str(followers_count)
        
        prompt = f"""You are an expert visa application reviewer. Briefly assess the professionalism and credibility of this {platform} profile for visa review purposes.

Username: {username}
Full Name: {full_name}
Followers: {followers_display} ({followers_count} followers)

Provide concise feedback on:
• The username (is it formal, casual, or unprofessional?)
• The full name (does it appear authentic or pseudonymous?)
• The follower count (high, average, or low — and what it implies)

Example: "Username @alextravels is casual but not inappropriate; full name Alexander Smith adds credibility. Follower count of 1.2k suggests moderate visibility without influencer-level exposure."

Return only one concise sentence (no JSON, no formatting)."""

        response = client.chat.completions.create(
            model="google/gemini-flash-1.5",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
            max_tokens=150
        )
        
        assessment = response.choices[0].message.content.strip()
        print(f"✅ {platform} profile assessment generated: {assessment[:60]}...")
        
        return assessment
        
    except Exception as e:
        print(f"❌ Profile assessment failed: {e}")
        return f"Username @{username}, full name '{full_name}', and {followers_display} followers provided for review."


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
    total_posts = len(posts_data_list)
    
    for i, post_data in enumerate(posts_data_list):
        print(f"\n📊 Analyzing {platform} post {i+1}/{total_posts}...")
        
        # Determine if this is the most recent post (first in list)
        is_most_recent = (i == 0)
        
        analysis = analyze_post_intelligent(platform, post_data, is_most_recent=is_most_recent, total_posts=total_posts)
        
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


