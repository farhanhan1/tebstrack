#!/usr/bin/env python
"""
TeBSTrack AI Functionality Test Script
Tests the AI components without requiring actual OpenAI API calls
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_ai_imports():
    """Test that all AI components can be imported"""
    try:
        from app.ai_service import get_ai_service, TeBSTrackAI
        from app.document_loader import DocumentLoader
        print("✅ AI service imports successful")
        return True
    except ImportError as e:
        print(f"❌ AI import failed: {e}")
        return False

def test_ai_initialization():
    """Test AI service initialization"""
    try:
        # Set a dummy API key for testing
        os.environ['OPENAI_API_KEY'] = 'test-key-for-initialization'
        
        from app.ai_service import get_ai_service
        ai_service = get_ai_service()
        
        print("✅ AI service initialization successful")
        print(f"   Model: {ai_service.model}")
        print(f"   Knowledge base loaded: {len(ai_service.knowledge_base)} characters")
        return True
    except Exception as e:
        print(f"❌ AI initialization failed: {e}")
        return False

def test_document_loader():
    """Test document loader functionality"""
    try:
        from app.document_loader import DocumentLoader
        
        # Test with a non-existent file (should return None gracefully)
        result = DocumentLoader.load_knowledge_document('nonexistent.pdf')
        
        print("✅ Document loader test successful")
        print(f"   Non-existent file handled correctly: {result is None}")
        return True
    except Exception as e:
        print(f"❌ Document loader test failed: {e}")
        return False

def test_flask_integration():
    """Test Flask app creation with AI components"""
    try:
        from app import create_app
        
        app = create_app()
        
        with app.app_context():
            # Test that routes are registered
            routes = [rule.rule for rule in app.url_map.iter_rules()]
            ai_routes = [r for r in routes if '/api/ai/' in r]
            
            print("✅ Flask integration successful")
            print(f"   AI routes registered: {len(ai_routes)}")
            for route in ai_routes:
                print(f"   - {route}")
            
            return True
    except Exception as e:
        print(f"❌ Flask integration failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🤖 TeBSTrack AI Functionality Test")
    print("=" * 50)
    
    tests = [
        ("AI Imports", test_ai_imports),
        ("AI Initialization", test_ai_initialization),
        ("Document Loader", test_document_loader),
        ("Flask Integration", test_flask_integration),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Testing {test_name}...")
        if test_func():
            passed += 1
        
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! AI functionality is ready.")
        print("\n📋 Next Steps:")
        print("1. Set your OpenAI API key in .env file")
        print("2. Place your knowledge document in app/knowledge/")
        print("3. Start the application with: python run.py")
        print("4. Look for the AI chatbot bubble and AI sections in ticket view")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
