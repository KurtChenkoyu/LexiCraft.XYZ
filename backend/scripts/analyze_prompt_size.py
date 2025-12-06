"""
Analyze prompt size and cost implications for 7,000 learning points.
"""

# Scenario analysis
scenarios = {
    "all_4_layers": {
        "description": "Word with all 4 layers (current example)",
        "characters": 6300,
        "layers": 4,
        "relationships": 4
    },
    "layer_1_only": {
        "description": "Word with no relationships (Layer 1 only)",
        "characters": 2500,  # Estimated base prompt
        "layers": 1,
        "relationships": 0
    },
    "layer_1_2": {
        "description": "Word with opposites only",
        "characters": 4000,  # Estimated
        "layers": 2,
        "relationships": 2
    },
    "layer_1_3": {
        "description": "Word with similar only",
        "characters": 3800,  # Estimated
        "layers": 2,
        "relationships": 1
    }
}

# Gemini API pricing (as of 2024)
# Gemini 1.5 Pro: ~$1.25 per 1M input tokens, ~$5.00 per 1M output tokens
# Rough estimate: 1 token ≈ 4 characters
TOKENS_PER_CHAR = 0.25
INPUT_COST_PER_1M_TOKENS = 1.25
OUTPUT_COST_PER_1M_TOKENS = 5.00

# Estimated output size (JSON response)
AVG_OUTPUT_CHARS = 2000  # Estimated JSON response size

def calculate_cost(characters, num_requests):
    """Calculate API cost for given prompt size and number of requests."""
    input_tokens = characters * TOKENS_PER_CHAR
    output_tokens = AVG_OUTPUT_CHARS * TOKENS_PER_CHAR
    
    total_input_tokens = input_tokens * num_requests
    total_output_tokens = output_tokens * num_requests
    
    input_cost = (total_input_tokens / 1_000_000) * INPUT_COST_PER_1M_TOKENS
    output_cost = (total_output_tokens / 1_000_000) * OUTPUT_COST_PER_1M_TOKENS
    
    return {
        "input_tokens_per_request": input_tokens,
        "output_tokens_per_request": output_tokens,
        "total_input_tokens": total_input_tokens,
        "total_output_tokens": total_output_tokens,
        "input_cost": input_cost,
        "output_cost": output_cost,
        "total_cost": input_cost + output_cost
    }

# Distribution assumptions (realistic for vocabulary)
# Most words have some relationships, but not all 4 layers
distribution = {
    "all_4_layers": 0.15,  # 15% have all relationships
    "layer_1_2": 0.25,     # 25% have opposites
    "layer_1_3": 0.20,     # 20% have similar
    "layer_1_4": 0.10,     # 10% have confused
    "layer_1_only": 0.30   # 30% have no relationships
}

TOTAL_LEARNING_POINTS = 7000

print("=" * 80)
print("PROMPT SIZE & COST ANALYSIS FOR 7,000 LEARNING POINTS")
print("=" * 80)
print()

print("📊 CURRENT PROMPT SIZE BREAKDOWN:")
print(f"  Full prompt (4 layers): ~{scenarios['all_4_layers']['characters']:,} characters")
print(f"  Base prompt (Layer 1 only): ~{scenarios['layer_1_only']['characters']:,} characters")
print(f"  Average prompt (weighted): ~{sum(s['characters'] * distribution.get(k, 0) for k, s in scenarios.items() if k != 'layer_1_3'):,.0f} characters")
print()

print("💰 COST ANALYSIS (Gemini 1.5 Pro):")
print(f"  Input: ${INPUT_COST_PER_1M_TOKENS} per 1M tokens")
print(f"  Output: ${OUTPUT_COST_PER_1M_TOKENS} per 1M tokens")
print(f"  Token estimate: 1 token ≈ 4 characters")
print()

# Calculate for worst case (all 4 layers)
worst_case = calculate_cost(scenarios['all_4_layers']['characters'], TOTAL_LEARNING_POINTS)
print("⚠️  WORST CASE (All 7,000 with 4 layers):")
print(f"  Input tokens per request: {worst_case['input_tokens_per_request']:,.0f}")
print(f"  Total input tokens: {worst_case['total_input_tokens']:,.0f}")
print(f"  Total cost: ${worst_case['total_cost']:.2f}")
print(f"    - Input: ${worst_case['input_cost']:.2f}")
print(f"    - Output: ${worst_case['output_cost']:.2f}")
print()

# Calculate for realistic distribution
realistic_costs = {}
for scenario_key, percentage in distribution.items():
    if scenario_key in scenarios:
        count = int(TOTAL_LEARNING_POINTS * percentage)
        cost = calculate_cost(scenarios[scenario_key]['characters'], count)
        realistic_costs[scenario_key] = cost

total_realistic_cost = sum(c['total_cost'] for c in realistic_costs.values())
total_realistic_input = sum(c['total_input_tokens'] for c in realistic_costs.values())
total_realistic_output = sum(c['total_output_tokens'] for c in realistic_costs.values())

print("📈 REALISTIC DISTRIBUTION:")
for scenario_key, percentage in distribution.items():
    if scenario_key in scenarios:
        count = int(TOTAL_LEARNING_POINTS * percentage)
        cost = realistic_costs[scenario_key]
        print(f"  {scenarios[scenario_key]['description']}: {count:,} requests")
        print(f"    Cost: ${cost['total_cost']:.2f} ({percentage*100:.0f}%)")
print()
print(f"  TOTAL REALISTIC COST: ${total_realistic_cost:.2f}")
print(f"    - Input: ${sum(c['input_cost'] for c in realistic_costs.values()):.2f}")
print(f"    - Output: ${sum(c['output_cost'] for c in realistic_costs.values()):.2f}")
print()

print("🔍 PROMPT SIZE BREAKDOWN (Full 4-layer prompt):")
print("  Base instructions: ~800 chars")
print("  Context section: ~600 chars")
print("  Layer 1 instructions: ~400 chars")
print("  Layer 2 instructions: ~800 chars (with 2 relationships)")
print("  Layer 3 instructions: ~700 chars (with 1 relationship)")
print("  Layer 4 instructions: ~700 chars (with 1 relationship)")
print("  JSON schema: ~2,000 chars")
print("  Relationship definitions: ~500 chars")
print("  Total: ~6,300 chars")
print()

print("💡 OPTIMIZATION OPPORTUNITIES:")
print("  1. Compress relationship definitions (remove redundant text)")
print("  2. Simplify JSON schema (shorter field names, less explanation)")
print("  3. Remove example structures (save ~300 chars per layer)")
print("  4. Condense instructions (combine similar requirements)")
print("  5. Use abbreviations for common phrases")
print()

# Calculate optimized sizes
optimizations = {
    "remove_example_structures": 300 * 3,  # 3 layers have examples
    "compress_instructions": 400,
    "simplify_json_schema": 500,
    "condense_requirements": 300
}

total_optimization = sum(optimizations.values())
optimized_size = scenarios['all_4_layers']['characters'] - total_optimization

print(f"  Estimated savings: ~{total_optimization:,} characters")
print(f"  Optimized size: ~{optimized_size:,} characters ({optimized_size/scenarios['all_4_layers']['characters']*100:.0f}% of original)")
print()

optimized_cost = calculate_cost(optimized_size, TOTAL_LEARNING_POINTS)
print(f"  Optimized cost (worst case): ${optimized_cost['total_cost']:.2f}")
print(f"  Savings: ${worst_case['total_cost'] - optimized_cost['total_cost']:.2f} ({((worst_case['total_cost'] - optimized_cost['total_cost']) / worst_case['total_cost'] * 100):.0f}% reduction)")
print()

print("⚡ ALTERNATIVE APPROACHES:")
print("  1. Batch processing: Generate multiple senses in one call")
print("     - Pros: Lower per-request overhead, better context")
print("     - Cons: More complex parsing, larger single requests")
print()
print("  2. Two-stage generation:")
print("     - Level 2a: Layer 1 only (all senses)")
print("     - Level 2b: Layers 2-4 (only senses with relationships)")
print("     - Pros: Most senses use smaller prompt")
print("     - Cons: Two API calls for relationship-rich words")
print()
print("  3. Template compression:")
print("     - Use shorter, more concise instructions")
print("     - Remove redundant explanations")
print("     - Pros: Immediate 20-30% reduction")
print("     - Cons: May reduce LLM clarity")
print()

print("=" * 80)
print("RECOMMENDATION:")
print("=" * 80)
print(f"  Current realistic cost: ${total_realistic_cost:.2f} for 7,000 learning points")
print(f"  With optimizations: ~${total_realistic_cost * 0.75:.2f} (25% reduction)")
print()
print("  The hybrid approach already helps significantly:")
print(f"  - 30% of words use minimal prompt (Layer 1 only)")
print(f"  - Average prompt size is ~{sum(s['characters'] * distribution.get(k, 0) for k, s in scenarios.items() if k in scenarios):,.0f} chars")
print()
print("  Consider implementing optimizations for 20-30% cost savings.")
print("=" * 80)

