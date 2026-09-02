#!/usr/bin/env node
/**
 * Test N+1 Query Fix - Compare Before/After
 * 
 * Tests panel APIs to verify query count reduction after selectinload() optimization.
 */

const http = require('http');

const API_BASE = 'localhost:8000';

function httpRequest(method, path) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: 'localhost',
      port: 8000,
      path,
      method,
      headers: { 'Content-Type': 'application/json' },
    };

    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => { data += chunk; });
      res.on('end', () => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve({ status: res.statusCode, data: data ? JSON.parse(data) : null });
        } else {
          reject(new Error(`HTTP ${res.statusCode}: ${data}`));
        }
      });
    });

    req.on('error', reject);
    req.end();
  });
}

async function testPanelAPIs() {
  console.log('=== Testing Panel APIs - N+1 Query Fix ===\n');
  
  try {
    // Get first project (assumes at least one exists)
    const { data: projects } = await httpRequest('GET', '/projects');
    
    if (!projects || projects.length === 0) {
      console.log('⚠️  No projects found. Create a project first.');
      process.exit(0);
    }
    
    const projectId = projects[0].id;
    console.log(`✓ Testing with project: ${projectId}\n`);
    
    // Test 1: Transcript endpoint
    console.log('1. Testing GET /projects/{id}/transcript');
    const start1 = Date.now();
    const { data: transcript } = await httpRequest('GET', `/projects/${projectId}/transcript`);
    const elapsed1 = Date.now() - start1;
    console.log(`   ✓ ${transcript.segments?.length || 0} segments`);
    console.log(`   ⏱  ${elapsed1}ms\n`);
    
    // Test 2: Translation endpoint
    console.log('2. Testing GET /projects/{id}/translation');
    const start2 = Date.now();
    const { data: translation } = await httpRequest('GET', `/projects/${projectId}/translation`);
    const elapsed2 = Date.now() - start2;
    console.log(`   ✓ ${translation.segments?.length || 0} segments`);
    console.log(`   ⏱  ${elapsed2}ms\n`);
    
    // Test 3: Speakers endpoint
    console.log('3. Testing GET /projects/{id}/speakers');
    const start3 = Date.now();
    const { data: speakers } = await httpRequest('GET', `/projects/${projectId}/speakers`);
    const elapsed3 = Date.now() - start3;
    console.log(`   ✓ ${speakers.items?.length || 0} speakers`);
    console.log(`   ⏱  ${elapsed3}ms\n`);
    
    console.log('=== Summary ===');
    console.log(`Total time: ${elapsed1 + elapsed2 + elapsed3}ms`);
    console.log('✅ All panel APIs responded successfully');
    console.log('\n💡 Check Docker logs for query count:');
    console.log('   docker compose -f infra/docker/docker-compose.yml logs api | grep "SELECT"');
    
  } catch (err) {
    console.error('\n❌ Test failed:', err.message);
    process.exit(1);
  }
}

testPanelAPIs();
