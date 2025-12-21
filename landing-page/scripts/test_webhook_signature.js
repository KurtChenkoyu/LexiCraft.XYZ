/**
 * Test Lemon Squeezy Webhook Signature Verification
 * 
 * This script tests the webhook signature verification logic
 * without needing to actually receive a webhook from Lemon Squeezy.
 * 
 * Usage:
 *   node scripts/test_webhook_signature.js
 */

const crypto = require('crypto');

// Test webhook secret (use the same one from .env.local)
const WEBHOOK_SECRET = process.env.LEMON_SQUEEZY_WEBHOOK_SECRET || 'test-secret-key';

/**
 * Verify Lemon Squeezy webhook signature using HMAC-SHA256
 */
function verifySignature(body, signature, secret) {
  try {
    // Extract hash from signature (format: "sha256=<hash>" or just "<hash>")
    const signatureHash = signature.replace(/^sha256=/, '');
    
    // Compute HMAC-SHA256
    const hmac = crypto.createHmac('sha256', secret);
    const digest = hmac.update(body).digest('hex');
    
    // Use timing-safe comparison
    return crypto.timingSafeEqual(
      Buffer.from(signatureHash, 'hex'),
      Buffer.from(digest, 'hex')
    );
  } catch (error) {
    console.error('Signature verification error:', error);
    return false;
  }
}

// Test data
const testBody = JSON.stringify({
  meta: {
    event_name: 'subscription_created',
    custom_data: {}
  },
  data: {
    type: 'subscriptions',
    id: '123',
    attributes: {
      status: 'active',
      customer_email: 'test@example.com',
      variant_name: '6-Month Pass',
      ends_at: '2025-06-30T00:00:00Z'
    }
  }
});

// Generate a valid signature
const hmac = crypto.createHmac('sha256', WEBHOOK_SECRET);
const validDigest = hmac.update(testBody).digest('hex');
const validSignature = `sha256=${validDigest}`;

console.log('='.repeat(60));
console.log('Testing Webhook Signature Verification');
console.log('='.repeat(60));
console.log(`Webhook Secret: ${WEBHOOK_SECRET.substring(0, 10)}...`);
console.log();

// Test 1: Valid signature
console.log('📝 Test 1: Valid signature');
console.log('-'.repeat(60));
const test1 = verifySignature(testBody, validSignature, WEBHOOK_SECRET);
console.log(`Signature: ${validSignature.substring(0, 20)}...`);
console.log(`Result: ${test1 ? '✅ PASSED' : '❌ FAILED'}`);
console.log();

// Test 2: Invalid signature (wrong hash)
console.log('📝 Test 2: Invalid signature (wrong hash)');
console.log('-'.repeat(60));
const invalidSignature = 'sha256=0000000000000000000000000000000000000000000000000000000000000000';
const test2 = verifySignature(testBody, invalidSignature, WEBHOOK_SECRET);
console.log(`Signature: ${invalidSignature}`);
console.log(`Result: ${test2 ? '❌ FAILED (should reject)' : '✅ PASSED (correctly rejected)'}`);
console.log();

// Test 3: Signature without sha256= prefix
console.log('📝 Test 3: Signature without sha256= prefix');
console.log('-'.repeat(60));
const signatureWithoutPrefix = validDigest;
const test3 = verifySignature(testBody, signatureWithoutPrefix, WEBHOOK_SECRET);
console.log(`Signature: ${signatureWithoutPrefix.substring(0, 20)}...`);
console.log(`Result: ${test3 ? '✅ PASSED' : '❌ FAILED'}`);
console.log();

// Test 4: Empty signature
console.log('📝 Test 4: Empty signature');
console.log('-'.repeat(60));
const test4 = verifySignature(testBody, '', WEBHOOK_SECRET);
console.log(`Result: ${test4 ? '❌ FAILED (should reject)' : '✅ PASSED (correctly rejected)'}`);
console.log();

// Summary
console.log('='.repeat(60));
const allPassed = test1 && !test2 && test3 && !test4;
console.log(allPassed ? '✅ All signature verification tests PASSED' : '❌ Some tests FAILED');
console.log('='.repeat(60));

process.exit(allPassed ? 0 : 1);

