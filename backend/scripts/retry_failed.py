#!/usr/bin/env python3
"""
Retry failed batches from Gemini enrichment
"""
import json
import os
from enrich_with_gemini import enrich_batch, load_vocabulary

def retry_failed_batches():
    """Retry all failed batches from checkpoint"""
    checkpoint_path = 'data/gemini_checkpoint.json'
    output_path = 'data/vocabulary_gemini.json'
    
    # Load checkpoint
    with open(checkpoint_path, 'r') as f:
        checkpoint = json.load(f)
    
    failed_batches = checkpoint.get('failed_batches', [])
    if not failed_batches:
        print("✅ No failed batches to retry!")
        return
    
    print(f"🔄 Retrying {len(failed_batches)} failed batch(es)...")
    
    # Load vocabulary and output
    vocabulary = load_vocabulary()
    with open(output_path, 'r') as f:
        output_data = json.load(f)
    
    success_count = 0
    still_failed = []
    
    for batch_num, failed_sense_ids in enumerate(failed_batches, 1):
        print(f"\n⏳ Retrying batch {batch_num}/{len(failed_batches)} ({len(failed_sense_ids)} words)...")
        
        # Get sense data for this batch
        batch_senses = [
            {'sense_id': sid, **vocabulary['senses'][sid]}
            for sid in failed_sense_ids
            if sid in vocabulary['senses']
        ]
        
        try:
            # Retry enrichment
            enriched = enrich_batch(batch_senses)
            
            if enriched:
                # Merge into output
                for item in enriched:
                    sense_id = item['sense_id']
                    if sense_id in output_data['senses']:
                        # Merge connections
                        if 'connections' not in output_data['senses'][sense_id]:
                            output_data['senses'][sense_id]['connections'] = {}
                        
                        # Add new Gemini data
                        for key in ['synonyms', 'antonyms', 'collocations', 'word_family', 'similar_words']:
                            if key in item:
                                output_data['senses'][sense_id]['connections'][key] = item[key]
                
                print(f"✅ Batch {batch_num} succeeded ({len(enriched)} words)")
                success_count += len(enriched)
            else:
                print(f"❌ Batch {batch_num} still failed")
                still_failed.append(failed_sense_ids)
        
        except Exception as e:
            print(f"❌ Batch {batch_num} error: {e}")
            still_failed.append(failed_sense_ids)
    
    # Save updated output
    with open(output_path, 'w') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    # Update checkpoint
    checkpoint['failed_batches'] = still_failed
    with open(checkpoint_path, 'w') as f:
        json.dump(checkpoint, f, indent=2)
    
    print("\n" + "="*60)
    print("✅ Retry Complete!")
    print("="*60)
    print(f"✅ Recovered: {success_count} words")
    print(f"❌ Still failed: {sum(len(b) for b in still_failed)} words")

if __name__ == '__main__':
    retry_failed_batches()








