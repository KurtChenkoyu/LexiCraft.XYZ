"""
Test script to verify enhanced explanation approach with multiple examples.
Tests different types of idiomatic expressions to ensure consistency.
"""

import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)

def test_explanation(example_en, word, literal_meaning):
    """Test explanation for a single example."""
    
    model = genai.GenerativeModel('gemini-2.0-flash')
    
    test_prompt = f"""
You are a helpful language learning guide helping Taiwan EFL learners understand English expressions. 
Your role is to help learners CONNECT with the language naturally, not to teach or correct them.
Focus on creating pathways that help learners see how English expressions work.

IMPORTANT: Vary your explanation style. Do NOT default to "想像一下" (imagine) for every explanation.
Use diverse approaches: direct descriptions, natural metaphors, examples, or comparisons.
Only use "想像一下" when it genuinely helps create a clear connection pathway.

English Example: "{example_en}"

TASK: Provide TWO Chinese versions:

1. LITERAL TRANSLATION (word-for-word):
   - Shows how English constructs meaning
   - Maps English words directly to Chinese
   - Use Traditional Chinese (Taiwan usage)

2. EXPLANATION (identifies what the sentence REALLY means):
   - Actively find and explain nuances that might be easily missed when going from English to Chinese
   - Highlight cultural context, implied meanings, and idiomatic expressions
   - **CRITICAL: For idiomatic expressions, help learners CONNECT the literal meaning to the idiomatic meaning:**
     * Create a natural CONNECTION and PATHWAY - help learners see how the meaning flows
     * VARY your explanation style - do NOT default to "想像一下" for every explanation
     * Use diverse approaches:
       - Direct descriptions: "原本的意思是...，在這裡引申為..."
       - Natural metaphors: "就像..." (like), "如同..." (as if) - embedded naturally
       - Examples: "例如..." (for example)
       - Comparisons: "可以想成..." (can think of it as)
       - Only use "想像一下" when it genuinely helps create a clear pathway
     * Show the semantic pathway: how the literal meaning naturally leads to the idiomatic meaning
     * Start with what the expression means, then show the connection - don't force metaphors
     * NEVER start with "不是..." (not...) or "字面上...但實際上" (literally...but actually) - these create disconnection
     * NEVER create disconnection - idioms are EXTENSIONS, help learners see the connection pathway
     * Focus on helping learners CONNECT naturally, not teaching them - be a guide, not a teacher
     
     * EXAMPLE OF GOOD EXPLANATION (natural pathway, varied language):
       "原本你被困住，前面有一道牆擋著你 (literal break)。這道牆突然出現一個缺口 (metaphorical break)，讓你可以通過，繼續前進。所以「a break」就像是打破了阻礙你前進的困境，給你帶來一個新的開始和更好的機會 (idiomatic meaning)。"
     
     * EXAMPLE OF BAD EXPLANATION (starts with negation - AVOID THIS):
       "「break」在這裡不是指打破東西，而是指一個好機會。" ❌
   - Explain subtle meanings that literal translation would lose
   - Use simple, everyday Chinese vocabulary that learners can understand
   - Use Traditional Chinese (Taiwan usage)

Return a JSON object:
{{
    "example_en": "{example_en}",
    "example_zh_translation": "...",
    "example_zh_explanation": "..."
}}
"""
    
    try:
        response = model.generate_content(
            test_prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        
        data = json.loads(response.text)
        return data
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def analyze_explanation(explanation, word):
    """Analyze if explanation shows connection pathway."""
    
    # Check for disconnection (bad)
    disconnection_indicators = ['不是指', '不是', '不是說', '並非']
    has_disconnection = any(ind in explanation for ind in disconnection_indicators)
    
    # Check for connection (good)
    connection_indicators = [
        '就像', '如同', '如同', '比喻', '引申', '延伸', '轉化',
        '從...到', '→', '演變', '發展', '連接', '連結', '關係'
    ]
    has_connection = any(ind in explanation for ind in connection_indicators)
    
    # Check for pathway/metaphor
    pathway_indicators = ['想像', '例如', '比方', '就像', '如同', '好比']
    has_pathway = any(ind in explanation for ind in pathway_indicators)
    
    return {
        'has_disconnection': has_disconnection,
        'has_connection': has_connection,
        'has_pathway': has_pathway,
        'score': (1 if has_connection else 0) + (1 if has_pathway else 0) - (1 if has_disconnection else 0)
    }

def main():
    """Test multiple examples."""
    
    test_cases = [
        {
            'example': "Getting that job was a real break for him; it changed his life.",
            'word': 'break',
            'literal': '打破、中斷'
        },
        {
            'example': "She ran out of patience waiting for the bus.",
            'word': 'run out of',
            'literal': '用完、耗盡'
        },
        {
            'example': "He finally broke the ice at the party by telling a joke.",
            'word': 'break the ice',
            'literal': '打破冰'
        },
        {
            'example': "The news hit him like a ton of bricks.",
            'word': 'hit',
            'literal': '打擊、撞擊'
        },
        {
            'example': "I need to catch up on my work this weekend.",
            'word': 'catch up',
            'literal': '追上、趕上'
        },
        {
            'example': "She turned down the job offer because of the salary.",
            'word': 'turn down',
            'literal': '轉下、降低'
        },
        {
            'example': "The company went under during the economic crisis.",
            'word': 'go under',
            'literal': '在...之下'
        },
        {
            'example': "I'll look into the matter and get back to you.",
            'word': 'look into',
            'literal': '看進、調查'
        },
        {
            'example': "She came across an old photo while cleaning.",
            'word': 'come across',
            'literal': '過來、穿過'
        },
        {
            'example': "He put off the meeting until next week.",
            'word': 'put off',
            'literal': '放下、推遲'
        },
        {
            'example': "The plan fell through at the last minute.",
            'word': 'fall through',
            'literal': '穿過、掉下'
        }
    ]
    
    print("=" * 80)
    print("TESTING MULTIPLE EXAMPLES")
    print("=" * 80)
    print()
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}/{len(test_cases)}: {test_case['word']}")
        print(f"Example: {test_case['example']}")
        print()
        print("Calling API...")
        
        data = test_explanation(
            test_case['example'],
            test_case['word'],
            test_case['literal']
        )
        
        if data:
            explanation = data.get('example_zh_explanation', '')
            analysis = analyze_explanation(explanation, test_case['word'])
            
            print("=" * 80)
            print(f"RESULTS - Test {i}: {test_case['word']}")
            print("=" * 80)
            print()
            print("📝 ENGLISH:")
            print(f"  {data.get('example_en', 'N/A')}")
            print()
            print("🔤 TRANSLATION:")
            print(f"  {data.get('example_zh_translation', 'N/A')}")
            print()
            print("💡 EXPLANATION:")
            print(f"  {explanation}")
            print()
            print("=" * 80)
            print("ANALYSIS:")
            print("=" * 80)
            print(f"  Has Connection: {'✅' if analysis['has_connection'] else '❌'}")
            print(f"  Has Pathway: {'✅' if analysis['has_pathway'] else '❌'}")
            print(f"  Has Disconnection: {'❌' if analysis['has_disconnection'] else '✅'}")
            print(f"  Score: {analysis['score']}/2")
            print()
            
            results.append({
                'word': test_case['word'],
                'analysis': analysis,
                'explanation': explanation[:100] + '...' if len(explanation) > 100 else explanation
            })
        else:
            print(f"❌ Failed to get response for {test_case['word']}")
            print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    
    total_score = sum(r['analysis']['score'] for r in results)
    max_score = len(results) * 2
    
    print(f"Total Score: {total_score}/{max_score}")
    print()
    
    for r in results:
        status = "✅" if r['analysis']['score'] >= 1 else "⚠️"
        print(f"{status} {r['word']}: Score {r['analysis']['score']}/2")
        if r['analysis']['has_disconnection']:
            print(f"   ⚠️  Contains disconnection statements")
        if r['analysis']['has_connection'] and r['analysis']['has_pathway']:
            print(f"   ✅ Shows connection pathway")
    
    print()
    print("=" * 80)
    print("RECOMMENDATION")
    print("=" * 80)
    print()
    
    if total_score >= len(results) * 1.5:
        print("✅ Approach works well! Ready to update main prompts.")
    elif total_score >= len(results):
        print("⚠️  Approach mostly works, but may need minor refinements.")
    else:
        print("❌ Approach needs more work before updating prompts.")
    
    return results

if __name__ == "__main__":
    main()

