#!/usr/bin/env python3
"""
Test script to check knowledge base integration
"""

import requests
import json

def test_knowledge_base():
    """Test the knowledge base status and functionality"""
    
    # Test the knowledge base status endpoint
    print("🔍 Testing Knowledge Base Integration...")
    print("=" * 50)
    
    try:
        # Note: This would require login in a real scenario
        # For now, let's test the AI service directly
        
        # Import and test the AI service directly
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        from app.ai_service import get_ai_service
        
        ai_service = get_ai_service()
        
        # Check knowledge base status
        print("📋 Knowledge Base Status:")
        status = ai_service.get_knowledge_base_status()
        
        for key, value in status.items():
            print(f"  • {key}: {value}")
        
        print("\n" + "=" * 50)
        
        # Test with sample questions
        test_questions = [
            "How do I reset a user's VPN access?",
            "What steps should I follow for a server request?",
            "How to handle a laptop hardware issue?",
            "What's the procedure for M365 access requests?",
            "How do I troubleshoot DevOps pipeline issues?"
        ]
        
        print("🤖 Testing Knowledge Base Responses:")
        print("=" * 50)
        
        for i, question in enumerate(test_questions, 1):
            print(f"\n📝 Test {i}: {question}")
            print("-" * 40)
            
            try:
                response = ai_service.test_knowledge_base_integration(question)
                print(f"🤖 AI Response: {response[:200]}{'...' if len(response) > 200 else ''}")
                
                # Check if response references knowledge base
                kb_indicators = ['knowledge base', 'procedure', 'documented', 'follow these steps', 'guidelines']
                has_kb_reference = any(indicator in response.lower() for indicator in kb_indicators)
                print(f"✅ References Knowledge Base: {'Yes' if has_kb_reference else 'No'}")
                
            except Exception as e:
                print(f"❌ Error: {e}")
        
        print("\n" + "=" * 50)
        print("📊 Knowledge Base Integration Summary:")
        
        if status['loaded']:
            print("✅ Knowledge base is loaded")
            if status['has_document']:
                print("✅ Using actual knowledge document")
            else:
                print("⚠️ Using fallback knowledge content")
        else:
            print("❌ Knowledge base failed to load")
            
        print(f"📄 Content length: {status['content_length']} characters")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_knowledge_base()
