#!/usr/bin/env python
"""
Smoke test to verify analysis produces unique, context-aware results.
Tests three different post types and confirms variation in output.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'visaguardai.settings')
django.setup()

from dashboard.intelligent_analyzer import analyze_post_intelligent

def test_analysis_variation():
    """Test that different posts produce different, contextual analyses"""
    
    # Test posts with distinct characteristics
    test_posts = [
        {
            "name": "Alcohol + Travel",
            "post_data": {
                "caption": "Celebrating with a drink in Paris 🍷",
                "post_id": "test1",
                "created_at": "2025-10-08T18:30:00.000Z",
                "location_name": "Paris, France",
                "likes_count": 85,
                "comments_count": 12,
                "type": "Image",
                "hashtags": ["paris", "wine"],
                "mentions": []
            }
        },
        {
            "name": "Professional Achievement",
            "post_data": {
                "caption": "Honored to present our 2025 research at the university",
                "post_id": "test2",
                "created_at": "2025-10-07T14:00:00.000Z",
                "location_name": "Boston, MA",
                "likes_count": 342,
                "comments_count": 45,
                "type": "Image",
                "hashtags": ["research", "academia"],
                "mentions": ["university"]
            }
        },
        {
            "name": "Sensitive Location",
            "post_data": {
                "caption": "Travel update: visiting family in Tehran next month",
                "post_id": "test3",
                "created_at": "2025-10-06T10:00:00.000Z",
                "location_name": "Tehran, Iran",
                "likes_count": 25,
                "comments_count": 8,
                "type": "Text",
                "hashtags": ["family", "travel"],
                "mentions": []
            }
        }
    ]
    
    print("\n" + "="*80)
    print("🧪 SMOKE TEST: Analysis Variation & Context-Awareness")
    print("="*80 + "\n")
    
    results = []
    
    for test in test_posts:
        print(f"\n📊 Testing: {test['name']}")
        print(f"   Caption: {test['post_data']['caption']}")
        print(f"   Location: {test['post_data']['location_name']}")
        print(f"   Engagement: {test['post_data']['likes_count']} likes")
        
        try:
            analysis = analyze_post_intelligent("Instagram", test['post_data'])
            
            # Extract statuses
            reinforcement_status = analysis.get('content_reinforcement', {}).get('status', 'N/A')
            suppression_status = analysis.get('content_suppression', {}).get('status', 'N/A')
            flag_status = analysis.get('content_flag', {}).get('status', 'N/A')
            risk_score = analysis.get('risk_score', 'N/A')
            
            # Extract reasons (first 100 chars)
            reinforcement_reason = analysis.get('content_reinforcement', {}).get('reason', '')[:100]
            suppression_reason = analysis.get('content_suppression', {}).get('reason', '')[:100]
            flag_reason = analysis.get('content_flag', {}).get('reason', '')[:100]
            
            results.append({
                'name': test['name'],
                'reinforcement': reinforcement_status,
                'suppression': suppression_status,
                'flag': flag_status,
                'risk_score': risk_score,
                'reasons': {
                    'reinforcement': reinforcement_reason,
                    'suppression': suppression_reason,
                    'flag': flag_reason
                }
            })
            
            print(f"   ✅ Analysis complete")
            print(f"      Reinforcement: {reinforcement_status}")
            print(f"      Suppression: {suppression_status}")
            print(f"      Flag: {flag_status}")
            print(f"      Risk Score: {risk_score}")
            
        except Exception as e:
            print(f"   ❌ Analysis failed: {e}")
            results.append({'name': test['name'], 'error': str(e)})
    
    # Verify variation
    print("\n" + "="*80)
    print("📈 VARIATION CHECK")
    print("="*80)
    
    # Check if all three have different status combinations
    status_combos = set()
    for r in results:
        if 'error' not in r:
            combo = f"{r['reinforcement']}-{r['suppression']}-{r['flag']}"
            status_combos.add(combo)
    
    print(f"\n✅ Unique status combinations: {len(status_combos)}/3")
    
    if len(status_combos) >= 2:
        print("✅ PASS: Analysis shows variation across different post types")
    else:
        print("⚠️  WARNING: All analyses returned similar statuses")
    
    # Check if reasons reference actual content
    print("\n" + "="*80)
    print("📝 CONTENT-AWARENESS CHECK")
    print("="*80)
    
    for r in results:
        if 'error' not in r:
            print(f"\n{r['name']}:")
            print(f"  Reinforcement reason: {r['reasons']['reinforcement']}...")
            print(f"  Suppression reason: {r['reasons']['suppression']}...")
            print(f"  Flag reason: {r['reasons']['flag']}...")
            
            # Check for generic phrases (should NOT appear)
            generic_phrases = ['Professional content', 'Positive promotion', 'No issues', 'Dummy data']
            has_generic = any(phrase.lower() in str(r['reasons']).lower() for phrase in generic_phrases)
            
            if has_generic:
                print(f"  ⚠️  WARNING: Contains generic phrases")
            else:
                print(f"  ✅ PASS: No generic boilerplate detected")
    
    print("\n" + "="*80)
    print("✅ SMOKE TEST COMPLETE")
    print("="*80 + "\n")

if __name__ == "__main__":
    test_analysis_variation()







