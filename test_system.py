#!/usr/bin/env python3
"""
System Test Suite for File Organizer
Tests all major components
"""

import sys
import os

def test_imports():
    """Test all imports work"""
    print("🧪 Testing imports...")
    try:
        from file_indexer import FileDatabase, FileIndexer
        from ai_tagger import AITagger
        from file_operations import FileOperations
        from conversational_ai import ConversationalAI
        from setup_wizard import load_user_profile, needs_setup
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False


def test_database():
    """Test database initialization"""
    print("\n🧪 Testing database...")
    try:
        from file_indexer import FileDatabase
        
        db = FileDatabase()
        
        # Test stats
        stats = db.get_stats()
        print(f"✅ Database initialized: {stats['total_files']} files indexed")
        
        # Test learning methods
        db.learn_pattern('test', 'test_key', 'test_value', 0.8)
        patterns = db.get_learned_patterns('test')
        assert len(patterns) > 0, "Pattern learning failed"
        print("✅ Pattern learning works")
        
        # Test conversation logging
        db.log_conversation("test message", "test response", "TEST", success=True)
        convos = db.get_recent_conversations(limit=1)
        assert len(convos) > 0, "Conversation logging failed"
        print("✅ Conversation logging works")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_conversational_ai():
    """Test enhanced conversational AI"""
    print("\n🧪 Testing conversational AI...")
    try:
        from file_indexer import FileDatabase
        from conversational_ai import ConversationalAI
        from setup_wizard import load_user_profile
        
        db = FileDatabase()
        profile = load_user_profile() or {
            "name": "Test User",
            "job": "Tester",
            "projects": ["Test Project"]
        }
        
        ai = ConversationalAI(
            model="llama3.2:3b",
            user_profile=profile,
            file_db=db
        )
        
        # Test intent detection
        intent = ai.detect_intent("find my files")
        assert intent == 'SEARCH', f"Intent detection failed: {intent}"
        print("✅ Intent detection works")
        
        # Test search term extraction
        terms = ai.extract_search_terms("find my invoice from yesterday")
        assert 'invoice' in terms.lower(), "Search term extraction failed"
        print("✅ Search term extraction works")
        
        # Test smart suggestions
        suggestions = ai.get_smart_suggestions()
        print(f"✅ Smart suggestions: {len(suggestions)} suggestions generated")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Conversational AI test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_file_operations():
    """Test file operations module"""
    print("\n🧪 Testing file operations...")
    try:
        from file_indexer import FileDatabase
        from file_operations import FileOperations
        
        db = FileDatabase()
        ops = FileOperations(db)
        
        print("✅ File operations module initialized")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ File operations test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ai_tagger():
    """Test AI tagging module"""
    print("\n🧪 Testing AI tagger...")
    try:
        from ai_tagger import AITagger
        from setup_wizard import load_user_profile
        
        profile = load_user_profile() or {"projects": ["Test"]}
        tagger = AITagger(user_profile=profile)
        
        # Test prompt building
        prompt = tagger.build_tagging_prompt(
            "test.txt",
            "This is test content about a project",
            ".txt"
        )
        assert "test.txt" in prompt, "Prompt building failed"
        print("✅ AI tagger initialized and prompt building works")
        
        return True
        
    except Exception as e:
        print(f"❌ AI tagger test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ollama_connection():
    """Test Ollama connection"""
    print("\n🧪 Testing Ollama connection...")
    try:
        import ollama
        
        # Try to list models
        models = ollama.list()
        
        # Handle different response formats
        if isinstance(models, dict) and 'models' in models:
            model_list = models['models']
        elif hasattr(models, 'models'):
            model_list = models.models
        else:
            model_list = list(models) if models else []
        
        print(f"✅ Ollama connected: {len(model_list)} models available")
        
        # Check for required model
        model_names = [m.get('name', str(m)) if isinstance(m, dict) else str(m) for m in model_list]
        if any('llama3.2:3b' in name or 'llama3.2' in name for name in model_names):
            print("✅ Required model (llama3.2) is available")
            return True
        else:
            print("⚠️  Warning: llama3.2:3b not found. Run: ollama pull llama3.2:3b")
            print(f"   Available models: {', '.join(model_names[:3])}")
            return False
            
    except Exception as e:
        print(f"❌ Ollama connection failed: {e}")
        print("   Make sure Ollama is running: ollama serve")
        return False


def main():
    """Run all tests"""
    print("=" * 60)
    print("🚀 File Organizer System Test Suite")
    print("=" * 60)
    
    results = {
        "Imports": test_imports(),
        "Database": test_database(),
        "Conversational AI": test_conversational_ai(),
        "File Operations": test_file_operations(),
        "AI Tagger": test_ai_tagger(),
        "Ollama Connection": test_ollama_connection()
    }
    
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:.<40} {status}")
    
    total = len(results)
    passed = sum(results.values())
    
    print("=" * 60)
    print(f"Total: {passed}/{total} tests passed ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("\n🎉 All tests passed! System is ready to use.")
        print("\n▶️  Run the app with: python file_organizer_app.py")
    else:
        print("\n⚠️  Some tests failed. Check errors above.")
    
    print("=" * 60)
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())

