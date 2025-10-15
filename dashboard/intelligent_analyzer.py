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
    
    # Log which key source is being used
    if os.getenv('OPENROUTER_API_KEY'):
        print("🔑 [AI Analyzer] Using OpenRouter key from .env")
    else:
        print("🔑 [AI Analyzer] Attempting to use OpenRouter key from Config table")
    
    if not OPENROUTER_API_KEY:
        config = Config.objects.first()
        if config:
            OPENROUTER_API_KEY = config.openrouter_api_key
    
    if not OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY not found")
    
    # OpenRouter requires additional headers for proper authentication
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
        default_headers={
            "HTTP-Referer": "https://visaguardai.com",
            "X-Title": "VisaGuardAI"
        }
    )


def generate_profile_assessment(platform, username):
    """
    Generate a concise AI assessment of username professionalism.
    Focuses only on the username/handle, not the full name.
    
    Args:
        platform: str - Platform name (Instagram, LinkedIn, Facebook, X)
        username: str - Account username/handle
    
    Returns:
        str - One-sentence professionalism assessment
    """
    try:
        client = get_ai_client()
        
        prompt = f"""Evaluate the {platform} username @{username} for professionalism and credibility in a visa review context. Assess whether the username appears real, appropriate, and credible (e.g., uses full name, professional terms) or contains concerning elements (numbers, slang, inappropriate terms). Respond with one concise sentence (max 25 words)."""
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are a visa application reviewer. Assess usernames for professionalism, authenticity, and appropriateness. Focus on whether the username looks real vs fake, professional vs casual, appropriate vs concerning."
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
        
        print(f"✅ {platform} username assessment: {assessment[:60]}...")
        
        return assessment
        
    except Exception as e:
        print(f"❌ Username assessment failed for {platform}: {e}")
        # Return a neutral fallback
        return f"Username @{username} appears suitable for professional review."


def calculate_realistic_risk_score(post_data, ai_score=None, platform="Instagram"):
    """
    Calculate a realistic risk score with platform-aware logic and better variance.
    Uses dynamic weighting - only applies modifiers when truly relevant.
    
    Args:
        post_data: dict - Post metadata
        ai_score: int - AI-generated score (optional, used as reference)
        platform: str - Platform name for platform-specific sensitivity
    
    Returns:
        int - Adjusted risk score (0-100)
    """
    try:
        # Start with safe baseline
        score = 2  # Start at A+ for truly neutral posts
        
        # Extract post features
        caption = (post_data.get('caption') or post_data.get('text') or post_data.get('post_text') or '').strip()
        likes = post_data.get('likes_count', 0) or 0
        comments = post_data.get('comments_count', 0) or 0
        created_at = post_data.get('created_at', '')
        location = post_data.get('location_name', '')
        hashtags = post_data.get('hashtags', []) or []
        caption_lower = caption.lower() if caption else ""
        
        # === RISKY ACTIVITY DETECTION (cap at B-/C+ range) ===
        risky_activities = [
            'cliff', 'jump', 'skydiv', 'bungee', 'extreme sport', 'base jump',
            'nightclub', 'casino', 'gambling'
        ]
        political_activities = ['protest', 'rally', 'demonstration']
        
        has_risky_activity = any(activity in caption_lower for activity in risky_activities)
        has_political_activity = any(activity in caption_lower for activity in political_activities)
        
        if has_risky_activity:
            score = max(score, 18)  # Minimum B- (cap A-range for risky activities)
            score += 8
            print(f"  [MODIFIER] Risky activity detected: capped at B-/C+ range → {score}")
        elif has_political_activity:
            # Political activities handled separately to avoid double-counting
            score = max(score, 15)  # Minimum B
            score += 6
            print(f"  [MODIFIER] Political activity detected: +6 → {score}")
        
        # === CAPTION ANALYSIS (smarter handling) ===
        if not caption:
            # Missing caption - only penalize if other context is unclear
            # Don't auto-penalize if engagement is high or location is clear
            if total_engagement := (likes + comments):
                if total_engagement < 50 and not location:
                    score += 15  # Ambiguous + low engagement
                    print(f"  [MODIFIER] Missing caption with low context: +15 → {score}")
                elif not location:
                    score += 8  # Some ambiguity but has engagement
                    print(f"  [MODIFIER] Missing caption (partial context): +8 → {score}")
                # else: Good engagement or location present - minimal penalty
            else:
                score += 18  # No caption, no engagement, no location
                print(f"  [MODIFIER] Missing caption (no context): +18 → {score}")
        elif len(caption.split()) <= 3 and not has_risky_activity:
            # Vague caption only matters if no risky activity already flagged
            score += 10
            print(f"  [MODIFIER] Vague caption ({len(caption.split())} words): +10 → {score}")
        
        # === POSITIVE INDICATORS (expanded) ===
        positive_keywords = [
            'volunteer', 'education', 'university', 'student', 'teamwork',
            'community', 'professional', 'career', 'work', 'project', 'learning',
            'conference', 'achievement', 'graduation', 'certification', 'training',
            'scholarship', 'internship', 'research', 'mentor', 'workshop', 'seminar',
            'degree', 'award', 'honor', 'service', 'charity', 'nonprofit'
        ]
        positive_count = sum(1 for keyword in positive_keywords if keyword in caption_lower)
        if positive_count > 0:
            reduction = min(12, positive_count * 6)  # Up to -12 for multiple indicators
            score -= reduction
            print(f"  [MODIFIER] Positive indicators ({positive_count}): -{reduction} → {score}")
        
        # === RISKY KEYWORDS (refined) ===
        # Alcohol/nightlife (higher risk)
        alcohol_keywords = ['alcohol', 'beer', 'wine', 'drunk', 'party', 'nightlife', 'club', 'bar', 'shots']
        if any(keyword in caption_lower for keyword in alcohol_keywords):
            score += 22  # Push toward D range
            print(f"  [MODIFIER] Alcohol/nightlife content: +22 → {score}")
        
        # Political/controversial (moderate-high risk) - avoid double-counting with political_activity
        political_keywords = ['politics', 'political', 'activist']
        if any(keyword in caption_lower for keyword in political_keywords) and not has_political_activity:
            score += 15
            print(f"  [MODIFIER] Political/controversial content: +15 → {score}")
        
        # === ENGAGEMENT ANALYSIS (dynamic - only when relevant) ===
        total_engagement = likes + comments
        
        # Only penalize very low engagement on older posts
        if created_at and total_engagement < 15:
            try:
                from datetime import datetime
                post_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                days_old = (datetime.now(post_date.tzinfo) - post_date).days
                if days_old > 90:  # 3+ months old with very low engagement
                    score += 6
                    print(f"  [MODIFIER] Old post with low engagement: +6 → {score}")
            except:
                pass
        
        # Reward exceptionally high engagement (credibility)
        if total_engagement > 1000:
            score -= 10
            print(f"  [MODIFIER] Very high engagement ({total_engagement}): -10 → {score}")
        elif total_engagement > 500:
            score -= 6
            print(f"  [MODIFIER] High engagement ({total_engagement}): -6 → {score}")
        
        # === SEVERE CONTENT FLAGS ===
        severe_keywords = [
            'violence', 'illegal', 'weapon', 'drug', 'hate', 'threat',
            'extremist', 'radical', 'terrorist', 'arrest', 'fight', 'assault'
        ]
        if any(keyword in caption_lower for keyword in severe_keywords):
            score += 45  # Push firmly into F range
            print(f"  [MODIFIER] Explicit severe content: +45 → {score}")
        
        # === LOCATION SENSITIVITY (only truly sensitive regions) ===
        if location:
            location_lower = location.lower()
            sensitive_locations = [
                'iran', 'syria', 'north korea', 'afghanistan', 'iraq',
                'venezuela', 'cuba', 'russia', 'ukraine', 'yemen', 'libya'
            ]
            if any(loc in location_lower for loc in sensitive_locations):
                score += 12
                print(f"  [MODIFIER] Geopolitically sensitive location: +12 → {score}")
        
        # === PLATFORM-SPECIFIC ADJUSTMENTS ===
        if platform == "LinkedIn":
            # LinkedIn: Apply higher scrutiny baseline
            if score < 5:  # No automatic A+ on LinkedIn
                score += 3
                print(f"  [MODIFIER] LinkedIn baseline scrutiny: +3 → {score}")
            
            # Slight penalty for very casual language on LinkedIn
            casual_indicators = ['lol', 'omg', 'lmao', 'haha', '🔥', '💯']
            if any(indicator in caption_lower for indicator in casual_indicators):
                score += 8
                print(f"  [MODIFIER] Casual tone on LinkedIn: +8 → {score}")
        
        # === RECENCY (only for very old posts) ===
        if created_at:
            try:
                from datetime import datetime
                post_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                days_old = (datetime.now(post_date.tzinfo) - post_date).days
                if days_old > 1095:  # >3 years (very outdated)
                    score += 10
                    print(f"  [MODIFIER] Very old post ({days_old} days): +10 → {score}")
            except:
                pass
        
        # === VARIANCE INJECTION (prevent clustering) ===
        # Add slight variance based on post characteristics to avoid identical scores
        import hashlib
        post_hash = hashlib.md5(f"{caption[:50]}{likes}{comments}".encode()).hexdigest()
        variance = int(post_hash[:2], 16) % 3  # 0-2 points variance
        score += variance
        if variance > 0:
            print(f"  [MODIFIER] Variance injection: +{variance} → {score}")
        
        # Clamp score between 0 and 100
        score = max(0, min(100, score))
        
        print(f"  [FINAL] {platform} calculated risk score: {score}")
        
        return score
        
    except Exception as e:
        print(f"  [ERROR] Risk scoring failed: {e}, returning default 15")
        return 15  # Safe default (B range)


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
    
    # Platform-specific scrutiny level
    platform_guidance = ""
    if platform == "LinkedIn":
        platform_guidance = """
⚠️ LINKEDIN PLATFORM NOTICE:
This is a professional networking platform. Apply heightened scrutiny:
• Even minor tone issues or unclear messaging should be noted
• Casual language is less acceptable than on Instagram
• Professional claims must appear credible and well-articulated
• Missing context or vague posts are more concerning on LinkedIn
• Do not assign A+ grades liberally - reserve for truly exceptional professional content
"""
    elif platform == "Instagram":
        platform_guidance = """
📸 INSTAGRAM PLATFORM NOTICE:
This is a lifestyle/visual platform. Apply balanced assessment:
• Allow full A-F grade range based on content appropriateness
• Lifestyle content is expected, but assess tone and context carefully
• Visual ambiguity (missing captions) requires careful consideration
• Professional, educational, or community content should be recognized
• Nightlife, parties, or risky activities warrant moderate to high scrutiny
"""
    elif platform == "Twitter":
        platform_guidance = """
🐦 TWITTER/X PLATFORM NOTICE:
This is a public discourse platform. Focus on tweet-specific characteristics:
• Evaluate TONE: Is it professional, casual, inflammatory, or divisive?
• Assess CLARITY: Are tweets clear and constructive, or vague and ambiguous?
• Check for CONTROVERSY: Political statements, inflammatory language, or polarizing content?
• Review PROFESSIONALISM: Does the tweet reflect maturity and thoughtfulness?
• Do NOT mention "captions" (tweets don't have captions)
• Do NOT focus on "community engagement" metrics unless exceptionally relevant
• DO evaluate the message itself: what does this tweet communicate about the person?
• Short tweets are normal - don't penalize brevity unless it creates ambiguity
• Allow full A-F grade range: thoughtful discourse = A grades, inflammatory/unclear = lower grades
"""
    
    # Build comprehensive prompt
    prompt = f"""You are a visa application coach conducting a critical review of social media content that will be scrutinized by immigration officers.

PLATFORM: {platform}

POST DATA:
{chr(10).join(f"• {part}" for part in context_parts)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{platform_guidance}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

YOUR ROLE:
Assess this post as an immigration officer would: skeptical, detail-oriented, and culturally sensitive. Immigration officers look for red flags, inconsistencies, and anything that could suggest risk.

ANALYSIS REQUIREMENTS:

1. **Content Strength** (What enhances credibility and demonstrates positive qualities?)
   • Identify professionalism, initiative, community impact, educational pursuits
   • Note career milestones, volunteer work, skill development, cultural enrichment
   • Cite specific language showing responsibility, authenticity, and stable connections
   • {'Assess how missing context weakens credibility and professional presentation' if not has_caption else 'Quote exact phrases demonstrating positive qualities'}
   • Use varied language: "demonstrates initiative," "shows community engagement," "reflects professional growth"

2. **Content Concern** (What ambiguities, tone issues, or context gaps could raise questions?)
   • Flag unclear messaging, casual tone in professional contexts, or lifestyle red flags
   • Note vague captions, party culture references, or ambiguous visual context
   • {'Note absence of explanatory detail and how it creates uncertainty about post purpose' if not has_caption else 'Quote phrases that lack clarity or could be misinterpreted'}
   • Only mention location if geopolitically sensitive or raises cultural questions
   • Only mention engagement if pattern suggests influencer activity or unusually low visibility
   • Avoid generic "Moderate Risk" - use "Limited clarity," "Some ambiguity," "Minor concern," "Mostly clear"

3. **Content Risk** (Does this post present serious immigration, legal, cultural, or safety concerns?)
   • Identify explicit external risks: political involvement, legal issues, security threats, cultural insensitivity
   • Detect references to violence, illegal activity, hate speech, overstaying, deceptive behavior
   • {'Warn that missing context prevents risk assessment and may trigger additional scrutiny' if not has_caption else 'Cite specific content triggering concern'}
   • If safe, concisely explain: "No significant external risks detected," "Content appears immigration-neutral"
   • Focus on serious factors only - benign lifestyle posts (cliff jumping, travel) are not high-risk unless combined with other flags

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CRITICAL RULES:

✅ ALWAYS CITE: Quote caption phrases, mention hashtags by name, reference specific engagement numbers or locations
✅ USE AUDIT LANGUAGE: Write like a formal visa risk audit - concise, credible, context-aware
✅ VARY VOCABULARY: Avoid repetitive "Moderate Risk" - use "Limited clarity," "Some concern," "Mostly safe," "Minor ambiguity"
✅ BE BALANCED: Recognize positive aspects while noting concerns (not just critical)
✅ BE SELECTIVE: Only flag truly relevant details (very old posts, sensitive locations, unusual engagement)
✅ DETECT CAPTION PRESENCE: {'This post has NO caption — address the information gap' if not has_caption else 'Caption is present — analyze its content'}
✅ BENIGN ACTIVITIES: Cliff jumping, travel adventures → moderate concern (C+/B-), not high risk unless other flags present

❌ NEVER:
• Use jargon like "suppression" or "reinforcement" in responses
• Use generic phrases like "professional content" without examples
• Mention technical terms ("sidecar," "carousel")
• Repeat identical language across posts
• Over-penalize benign lifestyle or creative posts
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

Return ONLY valid JSON (keep existing field names for compatibility):
{{
  "content_reinforcement": {{
    "status": "Safe|Positive|Needs Improvement",
    "reason": "<CONTENT STRENGTH: What enhances credibility? Cite specific positive qualities, professional language, or community impact>",
    "recommendation": "<How to strengthen profile further with specific, actionable advice>"
  }},
  "content_suppression": {{
    "status": "Safe|Caution|Risky",
    "reason": "<CONTENT CONCERN: What ambiguities or tone issues exist? Use varied language: 'Limited clarity,' 'Some ambiguity,' 'Minor concern,' 'Mostly clear'>",
    "recommendation": "<How to improve clarity or reduce potential misinterpretation>"
  }},
  "content_flag": {{
    "status": "Safe|Sensitive|High-Risk",
    "reason": "<CONTENT RISK: Serious external concerns only (political, legal, cultural, safety). If safe: 'No significant external risks detected' or 'Immigration-neutral content'>",
    "recommendation": "<Address serious issues or suggest broader profile improvements>"
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
        
        # Calculate realistic risk score based on post features (platform-aware)
        ai_risk_score = result.get('risk_score', 50)
        adjusted_score = calculate_realistic_risk_score(post_data, ai_risk_score, platform=platform)
        
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


def analyze_posts_batch(platform, posts_data_list, max_concurrent=5):
    """
    Analyze multiple posts for a platform with concurrent AI processing.
    
    Args:
        platform: str - Platform name
        posts_data_list: list - List of post metadata dicts
        max_concurrent: int - Max concurrent AI calls (default: 5, safe for rate limits)
    
    Returns:
        list - List of analyzed posts with full post_data and analysis (in original order)
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    import time
    
    if not posts_data_list:
        return []
    
    results = []
    num_posts = len(posts_data_list)
    
    # Determine optimal worker count (cap at max_concurrent to avoid rate limits)
    num_workers = min(max_concurrent, num_posts)
    
    print(f"\n🚀 Starting concurrent analysis for {num_posts} {platform} posts (max {num_workers} concurrent)")
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        # Submit all posts for concurrent analysis
        future_to_data = {}
        for i, post_data in enumerate(posts_data_list):
            print(f"📊 Submitting {platform} post {i+1}/{num_posts} for analysis...")
            future = executor.submit(analyze_post_intelligent, platform, post_data)
            future_to_data[future] = (i, post_data)
        
        # Collect results as they complete, storing by index
        index_to_result = {}
        completed_count = 0
        
        for future in as_completed(future_to_data):
            i, post_data = future_to_data[future]
            completed_count += 1
            
            try:
                analysis = future.result()
                
                # Wrap analysis in platform key (preserve exact casing for consistency)
                platform_key = platform  # Keep original casing (Instagram, LinkedIn, Twitter, etc.)
                wrapped_analysis = {
                    platform_key: analysis
                }
                
                # Store result with index for later sorting
                index_to_result[i] = {
                    "post": post_data.get('caption') or post_data.get('text') or post_data.get('post_text') or "[No text content]",
                    "post_data": post_data,
                    "analysis": wrapped_analysis
                }
                
                print(f"✅ {platform} post {i+1}/{num_posts} analysis complete ({completed_count}/{num_posts} done)")
                
            except Exception as e:
                print(f"❌ {platform} post {i+1} analysis failed: {e}")
                
                # Add error state for failed post
                index_to_result[i] = {
                    "post": post_data.get('caption') or post_data.get('text') or post_data.get('post_text') or "[Error analyzing post]",
                    "post_data": post_data,
                    "analysis": {
                        platform: {
                            "content_reinforcement": {
                                "status": "error",
                                "reason": f"Analysis failed: {str(e)[:100]}",
                                "recommendation": "Try again later"
                            },
                            "content_suppression": {
                                "status": "error",
                                "reason": "Could not assess content",
                                "recommendation": "Manual review recommended"
                            },
                            "content_flag": {
                                "status": "error",
                                "reason": "Unable to flag content",
                                "recommendation": "Review manually"
                            },
                            "risk_score": -1
                        }
                    }
                }
    
    # Return results in ORIGINAL ORDER (important for consistent display)
    for i in sorted(index_to_result.keys()):
        results.append(index_to_result[i])
    
    elapsed = time.time() - start_time
    print(f"\n✅ Completed {platform} concurrent batch analysis: {len(results)} posts in {elapsed:.2f}s")
    print(f"   Average: {elapsed/len(results):.2f}s per post (with {num_workers} concurrent workers)")
    
    return results


