"""
Test script to verify enhanced explanation approach.
Tests if LLM can explain HOW literal words connect to idiomatic meanings.
"""

import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

def test_enhanced_explanation():
    """Test the enhanced explanation approach with an idiomatic example."""
    
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    # Test with "break" idiomatic usage
    test_prompt = """
You are an expert EFL curriculum developer for Taiwan, specializing in vocabulary instruction for B1 learners.

English Example: "Getting that job was a real break for him; it changed his life."

TASK: Provide TWO Chinese versions:

1. LITERAL TRANSLATION (word-for-word):
   - Shows how English constructs meaning
   - Maps English words directly to Chinese

2. EXPLANATION (identifies what the sentence REALLY means):
   - Actively find and explain nuances that might be easily missed when going from English to Chinese
   - Highlight cultural context, implied meanings, and idiomatic expressions
   - **CRITICAL: For idiomatic expressions, show HOW the literal meaning EXTENDS to the idiomatic meaning:**
     * Create a CONNECTION and PATHWAY from literal to idiomatic (not disconnection)
     * Use metaphors that show how the meaning evolves/extends (e.g., "break" = interrupt/change → breaking through a barrier → opportunity)
     * Show the semantic pathway: how the literal meaning naturally leads to the idiomatic meaning
     * AVOID "不是..." (not...) statements that create disconnection - idioms are EXTENSIONS, not opposites
     * Help learners see the logical connection and pathway, not just memorize the meaning
   - Explain subtle meanings that literal translation would lose
   - Use simple, everyday Chinese vocabulary that learners can understand

Return a JSON object:
{
    "example_en": "Getting that job was a real break for him; it changed his life.",
    "example_zh_translation": "...",
    "example_zh_explanation": "..."
}
"""
    
    print("=" * 80)
    print("TESTING ENHANCED EXPLANATION APPROACH")
    print("=" * 80)
    print()
    print("Test Example: 'Getting that job was a real break for him'")
    print()
    print("Key Requirement: Explanation should show HOW 'break' (literal)")
    print("connects to 'break' (idiomatic meaning)")
    print()
    print("Calling Gemini API...")
    print()
    
    try:
        response = model.generate_content(
            test_prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        
        data = json.loads(response.text)
        
        print("=" * 80)
        print("RESULTS")
        print("=" * 80)
        print()
        print("📝 ENGLISH:")
        print(f"  {data.get('example_en', 'N/A')}")
        print()
        print("🔤 LITERAL TRANSLATION:")
        print(f"  {data.get('example_zh_translation', 'N/A')}")
        print()
        print("💡 EXPLANATION:")
        print(f"  {data.get('example_zh_explanation', 'N/A')}")
        print()
        print("=" * 80)
        print("ANALYSIS")
        print("=" * 80)
        print()
        
        explanation = data.get('example_zh_explanation', '')
        
        # Check if explanation shows the connection
        connection_indicators = [
            '原本', '比喻', '連接', '連結', '關係', '就像', '如同',
            '意思是', '指的是', '來自', '源於', '轉化', '延伸'
        ]
        
        has_connection = any(indicator in explanation for indicator in connection_indicators)
        
        if has_connection:
            print("✅ EXPLANATION SHOWS CONNECTION:")
            print("   The explanation appears to explain HOW the literal word")
            print("   connects to the idiomatic meaning.")
        else:
            print("⚠️  EXPLANATION MAY NOT SHOW CONNECTION:")
            print("   The explanation might not clearly show HOW 'break'")
            print("   (literal) connects to 'break' (idiomatic).")
            print()
            print("   Look for words like: 原本, 比喻, 連接, 就像, etc.")
        
        print()
        print("=" * 80)
        print("RECOMMENDATION")
        print("=" * 80)
        print()
        if has_connection:
            print("✅ The enhanced prompt approach appears to work!")
            print("   The LLM can explain the connection between literal and idiomatic meanings.")
            print("   Ready to update the main prompts.")
        else:
            print("⚠️  May need to strengthen the prompt further.")
            print("   Consider adding more explicit examples of what we want.")
        
        return data
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

if __name__ == "__main__":
    test_enhanced_explanation()

