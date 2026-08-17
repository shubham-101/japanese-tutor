#!/usr/bin/env python3
"""
Comprehensive test suite for Japanese Tutor Application
Tests all API endpoints and application flow
"""

import requests
import json
import time

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
        response = requests.get(f"{BASE_URL}/", timeout=5)
        data = response.json()
        passed = response.status_code == 200 and data.get("status") == "running"
        print_test("Backend Health Check", passed, f"Status: {data.get('status')}")
        return passed
    except Exception as e:
        print_test("Backend Health Check", False, str(e))
        return False

def test_get_study_modes():
    """Test GET /study/modes endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/study/modes", timeout=5)
        data = response.json()
        passed = response.status_code == 200 and isinstance(data, dict)
        modes = list(data.keys()) if passed else []
        print_test("Get Study Modes", passed, f"Modes: {', '.join(modes)}")
        return passed, data
    except Exception as e:
        print_test("Get Study Modes", False, str(e))
        return False, {}

def test_create_study_session(mode="grammar", level="N4"):
    """Test POST /study endpoint"""
    try:
        payload = {
            "mode": mode,
            "jlpt_level": level
        }
        response = requests.post(
            f"{BASE_URL}/study",
            json=payload,
            timeout=30  # Longer timeout for AI generation
        )
        data = response.json()
        passed = response.status_code == 200 and "session_id" in data
        session_id = data.get("session_id") if passed else None
        question = data.get("question", "")[:50] + "..." if data.get("question") else ""
        print_test(
            f"Create Study Session ({mode}, {level})",
            passed,
            f"Session ID: {session_id}, Question: {question}"
        )
        return passed, data
    except Exception as e:
        print_test(f"Create Study Session ({mode}, {level})", False, str(e))
        return False, {}

def test_submit_answer(session_id, answer="N4"):
    """Test POST /study/{session_id}/answer endpoint"""
    try:
        response = requests.post(
            f"{BASE_URL}/study/{session_id}/answer",
            params={"answer": answer},
            timeout=10
        )
        data = response.json()
        passed = response.status_code == 200 and "correct" in data
        correct = data.get("correct", False)
        print_test(
            f"Submit Answer (Session {session_id})",
            passed,
            f"Correct: {correct}, Answer: '{answer}'"
        )
        return passed, data
    except Exception as e:
        print_test(f"Submit Answer (Session {session_id})", False, str(e))
        return False, {}

def test_frontend_access():
    """Test if frontend is accessible"""
    try:
        response = requests.get(f"{FRONTEND_URL}/", timeout=5)
        passed = response.status_code == 200
        print_test("Frontend Access", passed, f"Status Code: {response.status_code}")
        return passed
    except Exception as e:
        print_test("Frontend Access", False, str(e))
        return False

def test_cors_preflight():
    """Test CORS preflight request"""
    try:
        response = requests.options(
            f"{BASE_URL}/study",
            headers={
                "Origin": "http://127.0.0.1:5173",
                "Access-Control-Request-Method": "POST"
            },
            timeout=5
        )
        passed = response.status_code == 200
        print_test("CORS Preflight", passed, f"Status Code: {response.status_code}")
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
    frontend_ok = test_frontend_access()
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
    
    test_modes = ["grammar", "vocabulary", "kanji"]
    for mode in test_modes:
        if mode not in modes:
            print(f"⚠️  Mode '{mode}' not available, skipping...")
            continue
        
        session_ok, session = test_create_study_session(mode=mode, level="N4")
        
        if session_ok:
            session_id = session.get("session_id")
            print(f"   Question: {session.get('question')}")
            if session.get("options"):
                print(f"   Options: {session.get('options')}")
            
            # Test submitting an answer
            test_answer = session.get("options", ["answer"])[0] if session.get("options") else "test"
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
    print(f"Frontend Access:       {'✅ PASS' if frontend_ok else '❌ FAIL'}")
    print(f"CORS Preflight:        {'✅ PASS' if cors_ok else '❌ FAIL'}")
    print(f"Study Modes Endpoint:  {'✅ PASS' if modes_ok else '❌ FAIL'}")
    print()
    print("Recommendation: Open http://127.0.0.1:5173 in your browser to test UI")

if __name__ == "__main__":
    main()
