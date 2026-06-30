/**
 * Frontend API Service Tests
 * Tests for API communication with backend
 */

// Mock API Service
class APIService {
  constructor(baseURL = process.env.REACT_APP_API_URL || 'http://localhost:8000') {
    this.baseURL = baseURL;
  }

  async chat(text) {
    if (!text || text.trim().length === 0) {
      throw new Error('Text cannot be empty');
    }

    if (text.length > 500) {
      throw new Error('Text too long (max 500 chars)');
    }

    try {
      const response = await fetch(`${this.baseURL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.statusCode}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Chat API error:', error);
      throw error;
    }
  }

  async health() {
    try {
      const response = await fetch(`${this.baseURL}/health`);
      return response.ok ? await response.json() : null;
    } catch {
      return null;
    }
  }
}

// Test Cases
async function testValidChat() {
  const api = new APIService();
  try {
    const result = await api.chat('Hello, how are you?');
    console.log('✅ Valid chat test passed:', result);
  } catch (e) {
    console.error('❌ Valid chat test failed:', e.message);
  }
}

async function testEmptyChat() {
  const api = new APIService();
  try {
    await api.chat('');
    console.error('❌ Empty chat test should have thrown error');
  } catch (e) {
    console.log('✅ Empty chat test passed (correctly rejected)');
  }
}

async function testLongChat() {
  const api = new APIService();
  try {
    const longText = 'a'.repeat(501);
    await api.chat(longText);
    console.error('❌ Long chat test should have thrown error');
  } catch (e) {
    console.log('✅ Long chat test passed (correctly rejected)');
  }
}

async function testHealthCheck() {
  const api = new APIService();
  const health = await api.health();
  if (health) {
    console.log('✅ Health check test passed:', health);
  } else {
    console.log('⚠️ Health check test: Backend not responding');
  }
}

// Run tests
async function runAllTests() {
  console.log('🧪 Running Frontend API Tests...\n');

  await testHealthCheck();
  await testEmptyChat();
  await testLongChat();
  await testValidChat();

  console.log('\n✅ Frontend API tests completed!');
}

// Export for Jest
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { APIService, runAllTests };
}

// Run if executed directly
if (typeof window === 'undefined') {
  runAllTests().catch(console.error);
}
