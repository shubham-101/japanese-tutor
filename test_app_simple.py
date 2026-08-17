#!/usr/bin/env python3
"""
Simple test suite for Japanese Tutor Application (no external dependencies)
"""

import urllib.request
import urllib.error
import json
import sys

BASE_URL = "http://127.0.0.1:8000"
FRONTEND_URL = "http://127.0.0.1:5173"

def print_test(name, passed, message=""):
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} | {name}")
    if message:
        print(f"       {message}")

def test_backend_health():
    """Test if backend is running"""
    try:
        with urllib.request.urlopen(f"{BASE_URL}/", timeout=5) as response:
            data = json.loads(response.read().decode())
            passed = response.status == 200 and data.get("status") == "running"
            print_test("Backend Health Check", passed, f"Status: {data.get('status')}")
            return passed
    except Exception as e:
        print_test("Backend Health Check", False, str(e))
        return False

def test_get_study_modes():
    """Test GET /study/modes endpoint"""
    try:
        with urllib.request.urlopen(f"{BASE_URL}/study/modes", timeout=5) as response:
            data = json.loads(response.read().decode())
            passed = response.status == 200 and isinstance(data, dict)
            modes = list(data.keys()) if passed else []
            print_test("Get Study Modes", passed, f"Modes: {', '.join(modes)}")
            return passed, data
    except Exception as e:
        print_test("Get Study Modes", False, str(e))
        return False, {}

def test_create_study_session(mode="grammar", level="N4"):
    """Test POST /study endpoint"""
    try:
        payload = json.dumps({
            "mode": mode,
            "jlpt_level": level
        }).encode('utf-8')
        
        req = urllib.request.Request(
            f"{BASE_URL}/study",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode())
            passed = response.status == 200 and "session_id" in data
            session_id = data.get("session_id") if passed else None
            question = data.get("question", "")[:50] + "..." if data.get("question") else ""
            print_test(
                f"Create Study Session ({mode}, {level})",
                passed,
                f"Session ID: {session_id}, Question: {question}"
            )
            return passed, data
    except urllib.error.HTTPError as e:
        error_data = e.read().decode()
        print_test(f"Create Study Session ({mode}, {level})", False, f"HTTP {e.code}: {error_data[:100]}")
        return False, {}
    except Exception as e:
        print_test(f"Create Study Session ({mode}, {level})", False, str(e))
        return False, {}

def test_submit_answer(session_id, answer="N4"):
    """Test POST /study/{session_id}/answer endpoint"""
    try:
        req = urllib.request.Request(
            f"{BASE_URL}/study/{session_id}/answer?answer={answer}",
            data=b'',
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            passed = response.status == 200 and "correct" in data
            correct = data.get("correct", False)
            print_test(
                f"Submit Answer (Session {session_id})",
                passed,
                f"Correct: {correct}, Answer: '{answer}'"
            )
            return passed, data
    except urllib.error.HTTPError as e:
        error_data = e.read().decode()
        print_test(f"Submit Answer (Session {session_id})", False, f"HTTP {e.code}")
        return False, {}
    except Exception as e:
        print_test(f"Submit Answer (Session {session_id})", False, str(e))
        return False, {}

def test_cors_preflight():
    """Test CORS preflight request"""
    try:
        req = urllib.request.Request(
            f"{BASE_URL}/study",
            headers={
                "Origin": "http://127.0.0.1:5173",
                "Access-Control-Request-Method": "POST"
            },
            method="OPTIONS"
        )
        
        with urllib.request.urlopen(req, timeout=5) as response:
            passed = response.status == 200
            print_test("CORS Preflight", passed, f"Status Code: {response.status}")
            return passed
    except Exception as e:
        print_test("CORS Preflight", False, str(e))
        return False

def main():
    print("=" * 70)
    print("JAPANESE TUTOR APPLICATION TEST SUITE")
    print("=" * 70)
    print()

    # Phase 1: Infrastructure Tests
    print("PHASE 1: INFRASTRUCTURE TESTS")
    print("-" * 70)
    backend_ok = test_backend_health()
    cors_ok = test_cors_preflight()
    print()

    if not backend_ok:
        print("❌ Backend is not running. Cannot proceed with API tests.")
        return

    # Phase 2: API Endpoint Tests
    print("PHASE 2: API ENDPOINT TESTS")
    print("-" * 70)
    modes_ok, modes = test_get_study_modes()
    print()

    # Phase 3: Study Session Flow Tests
    print("PHASE 3: STUDY SESSION WORKFLOW TESTS")
    print("-" * 70)
    
    test_modes = ["grammar", "vocabulary"]
    for mode in test_modes:
        if mode not in modes:
            print(f"⚠️  Mode '{mode}' not available, skipping...")
            continue
        
        session_ok, session = test_create_study_session(mode=mode, level="N4")
        
        if session_ok:
            session_id = session.get("session_id")
            options = session.get("options", [])
            print(f"   Question: {session.get('question')}")
            if options:
                print(f"   Options: {options}")
            
            # Test submitting an answer
            test_answer = options[0] if options else "test_answer"
            answer_ok, result = test_submit_answer(session_id, answer=test_answer)
            
            if answer_ok:
                print(f"   Correct Answer: {result.get('correct_answer')}")
                print(f"   Explanation: {result.get('explanation', 'N/A')[:80]}...")
        print()

    # Summary
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Backend Health:        {'✅ PASS' if backend_ok else '❌ FAIL'}")
    print(f"CORS Preflight:        {'✅ PASS' if cors_ok else '❌ FAIL'}")
    print(f"Study Modes Endpoint:  {'✅ PASS' if modes_ok else '❌ FAIL'}")
    print()
    print("✅ Open http://127.0.0.1:5173 in your browser to test the UI")

if __name__ == "__main__":
    main()
