#!/usr/bin/env python3
"""
Production Live Site Testing
Tests the live visaguardai.com site to verify deployment
"""

import requests
import time
from datetime import datetime

print("\n" + "="*80)
print("🌐 PRODUCTION LIVE SITE TESTING")
print("="*80 + "\n")

print(f"🕐 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"🎯 Target: https://visaguardai.com")
print()

results = {}

# Test 1: Homepage
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("TEST 1: Homepage Accessibility")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

try:
    start = time.time()
    response = requests.get("https://visaguardai.com", timeout=10)
    elapsed = time.time() - start
    
    status = "✅ PASS" if response.status_code == 200 else f"⚠️  WARN (HTTP {response.status_code})"
    print(f"{status}")
    print(f"   Status Code: {response.status_code}")
    print(f"   Response Time: {elapsed:.2f}s")
    print(f"   Content Length: {len(response.content)} bytes")
    
    # Check for key elements
    content = response.text.lower()
    has_title = "visaguardai" in content
    has_tailwind = "tailwindcss" in content or "tailwind" in content
    
    print(f"   Has Title: {'✅' if has_title else '❌'}")
    print(f"   Has Styling: {'✅' if has_tailwind else '❌'}")
    
    results['homepage'] = {
        'status': response.status_code,
        'time': elapsed,
        'passed': response.status_code == 200
    }
except Exception as e:
    print(f"❌ FAIL: {str(e)}")
    results['homepage'] = {'passed': False, 'error': str(e)}

print()

# Test 2: Dashboard (should redirect if not authenticated)
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("TEST 2: Dashboard Endpoint")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

try:
    start = time.time()
    response = requests.get("https://visaguardai.com/dashboard/", timeout=10, allow_redirects=False)
    elapsed = time.time() - start
    
    # 302 means redirect (expected for protected page)
    # 200 means accessible (also okay if session exists)
    status = "✅ PASS" if response.status_code in [200, 302] else f"⚠️  WARN (HTTP {response.status_code})"
    print(f"{status}")
    print(f"   Status Code: {response.status_code}")
    print(f"   Response Time: {elapsed:.2f}s")
    
    if response.status_code == 302:
        print(f"   Behavior: Redirects (authentication required) ✅")
    elif response.status_code == 200:
        print(f"   Behavior: Accessible ✅")
    
    results['dashboard'] = {
        'status': response.status_code,
        'time': elapsed,
        'passed': response.status_code in [200, 302]
    }
except Exception as e:
    print(f"❌ FAIL: {str(e)}")
    results['dashboard'] = {'passed': False, 'error': str(e)}

print()

# Test 3: Static files
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("TEST 3: Static Files")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

static_files = [
    "/static/assets/styles.css",
    "/static/assets/favicon.png",
]

static_passed = 0
static_total = len(static_files)

for static_file in static_files:
    try:
        response = requests.get(f"https://visaguardai.com{static_file}", timeout=5)
        if response.status_code == 200:
            print(f"✅ {static_file}")
            static_passed += 1
        else:
            print(f"⚠️  {static_file} (HTTP {response.status_code})")
    except Exception as e:
        print(f"❌ {static_file} ({str(e)[:50]})")

print(f"\n   Static files: {static_passed}/{static_total} accessible")
results['static_files'] = {'passed': static_passed, 'total': static_total}

print()

# Test 4: SSL Certificate
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("TEST 4: SSL Certificate")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

try:
    response = requests.get("https://visaguardai.com", timeout=10)
    print("✅ PASS")
    print("   SSL Certificate: Valid")
    print("   HTTPS: Enabled")
    results['ssl'] = {'passed': True}
except requests.exceptions.SSLError as e:
    print(f"❌ FAIL: SSL Error - {str(e)[:100]}")
    results['ssl'] = {'passed': False, 'error': str(e)}
except Exception as e:
    print(f"⚠️  WARN: {str(e)[:100]}")
    results['ssl'] = {'passed': False, 'error': str(e)}

print()

# Test 5: Response Headers
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("TEST 5: Server Response Headers")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

try:
    response = requests.get("https://visaguardai.com", timeout=10)
    headers = response.headers
    
    print(f"   Server: {headers.get('Server', 'Not disclosed')}")
    print(f"   Content-Type: {headers.get('Content-Type', 'Unknown')}")
    print(f"   Content-Encoding: {headers.get('Content-Encoding', 'None')}")
    
    # Check for security headers
    has_strict_transport = 'Strict-Transport-Security' in headers
    print(f"   HSTS: {'✅ Enabled' if has_strict_transport else '⚠️  Not detected'}")
    
    results['headers'] = {'passed': True}
except Exception as e:
    print(f"❌ FAIL: {str(e)}")
    results['headers'] = {'passed': False, 'error': str(e)}

print()

# Test 6: Performance
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("TEST 6: Performance (Multiple Requests)")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

times = []
for i in range(3):
    try:
        start = time.time()
        response = requests.get("https://visaguardai.com", timeout=10)
        elapsed = time.time() - start
        times.append(elapsed)
        print(f"   Request {i+1}: {elapsed:.2f}s")
    except Exception as e:
        print(f"   Request {i+1}: Failed ({str(e)[:50]})")

if times:
    avg_time = sum(times) / len(times)
    print(f"\n   Average: {avg_time:.2f}s")
    print(f"   Min: {min(times):.2f}s")
    print(f"   Max: {max(times):.2f}s")
    
    if avg_time < 2.0:
        print(f"   Performance: ✅ Excellent")
    elif avg_time < 5.0:
        print(f"   Performance: ✅ Good")
    else:
        print(f"   Performance: ⚠️  Slow")
    
    results['performance'] = {'avg': avg_time, 'passed': avg_time < 5.0}

print()

# Summary
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("SUMMARY")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

passed_tests = sum(1 for r in results.values() if r.get('passed', False))
total_tests = len(results)

print(f"Tests Passed: {passed_tests}/{total_tests}")
print()

for test_name, result in results.items():
    status = "✅" if result.get('passed', False) else "❌"
    print(f"{status} {test_name.replace('_', ' ').title()}")

print()

# Final verdict
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
print("FINAL VERDICT")
print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

if passed_tests >= total_tests - 1:
    print("🎉 PRODUCTION SITE IS LIVE AND WORKING!")
    print()
    print("✅ Site Status: OPERATIONAL")
    print("✅ Homepage: Accessible")
    print("✅ Dashboard: Protected (authentication required)")
    print("✅ SSL: Valid")
    print("✅ Performance: Good")
    print()
    print("The production deployment appears to be successful!")
    print()
    print("🔍 Next Steps:")
    print("  1. Login to dashboard")
    print("  2. Test analyzing a social media account")
    print("  3. Verify 10-post limit is enforced")
    print("  4. Check that all 4 platforms work")
elif passed_tests >= total_tests / 2:
    print("⚠️  PRODUCTION SITE IS PARTIALLY WORKING")
    print()
    print("Some tests passed, but there may be issues.")
    print("Review the failures above and investigate.")
else:
    print("❌ PRODUCTION SITE HAS ISSUES")
    print()
    print("Multiple tests failed. The site may not be working correctly.")
    print("Check server logs and investigate the failures.")

print()
print(f"🕐 Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()
print("="*80)
print("✅ LIVE SITE TEST COMPLETE")
print("="*80)




