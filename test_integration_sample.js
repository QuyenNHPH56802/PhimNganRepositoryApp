#!/usr/bin/env node
/**
 * Integration Test Sample - Full Upload → Render Pipeline
 * 
 * Tests the complete workflow:
 * 1. Create project
 * 2. Upload video asset
 * 3. Trigger workflow
 * 4. Poll workflow status until completion
 * 5. Verify render output
 */

const http = require('http');
const fs = require('fs');
const path = require('path');

const API_BASE = 'localhost:8000';
const POLL_INTERVAL_MS = 5000;
const MAX_POLL_ATTEMPTS = 120; // 10 minutes max

// Sample video path - user should provide this
const SAMPLE_VIDEO_PATH = process.argv[2] || './sample.mp4';

function httpRequest(method, path, body = null) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: 'localhost',
      port: 8000,
      path,
      method,
      headers: {
        'Content-Type': 'application/json',
      },
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
    if (body) req.write(JSON.stringify(body));
    req.end();
  });
}

async function createProject() {
  console.log('📦 Creating project...');
  const { data } = await httpRequest('POST', '/projects', {
    title: `Integration Test ${new Date().toISOString()}`,
    quality_mode: 'balanced',
    source_language: 'zh',
    target_language: 'vi',
  });
  console.log(`✅ Project created: ${data.id}`);
  return data.id;
}

async function uploadVideo(projectId, videoPath) {
  console.log(`📤 Uploading video: ${videoPath}...`);
  
  // Step 1: Get presigned URL
  const filename = path.basename(videoPath);
  const { data: presign } = await httpRequest('POST', `/projects/${projectId}/assets/presign`, {
    filename,
    content_type: 'video/mp4',
  });
  
  console.log(`  Presign URL: ${presign.upload_url}`);
  
  // Step 2: Upload file to presigned URL (simplified - real impl needs multipart)
  // For this sample, we'll just create asset record directly
  const { data: asset } = await httpRequest('POST', `/projects/${projectId}/assets`, {
    filename,
    content_type: 'video/mp4',
    storage_path: `projects/${projectId}/assets/${filename}`,
    file_size: fs.statSync(videoPath).size,
    asset_type: 'video',
  });
  
  console.log(`✅ Asset created: ${asset.id}`);
  return asset.id;
}

async function triggerWorkflow(projectId, assetId) {
  console.log('🚀 Triggering workflow...');
  const { data } = await httpRequest('POST', `/projects/${projectId}/workflows`, {
    asset_id: assetId,
    quality_mode: 'balanced',
  });
  console.log(`✅ Workflow started: ${data.workflow_id}`);
  return data.workflow_id;
}

async function pollWorkflowStatus(projectId, workflowId) {
  console.log('⏳ Polling workflow status...');
  
  for (let i = 0; i < MAX_POLL_ATTEMPTS; i++) {
    try {
      const { data } = await httpRequest('GET', `/projects/${projectId}/workflows/${workflowId}`);
      
      console.log(`  [${i + 1}/${MAX_POLL_ATTEMPTS}] Status: ${data.status} | Phase: ${data.current_phase || 'N/A'}`);
      
      if (data.status === 'completed') {
        console.log('✅ Workflow completed successfully!');
        return data;
      }
      
      if (data.status === 'failed') {
        console.error('❌ Workflow failed:', data.error_message);
        throw new Error(`Workflow failed: ${data.error_message}`);
      }
      
      // Wait before next poll
      await new Promise(resolve => setTimeout(resolve, POLL_INTERVAL_MS));
      
    } catch (err) {
      console.error(`  Polling error: ${err.message}`);
      // Continue polling even on transient errors
    }
  }
  
  throw new Error('Workflow timeout - exceeded max poll attempts');
}

async function verifyRenderOutput(projectId) {
  console.log('🔍 Verifying render output...');
  
  // Check if render assets exist
  const { data: assets } = await httpRequest('GET', `/projects/${projectId}/assets`);
  const renderAsset = assets.find(a => a.asset_type === 'rendered_video');
  
  if (!renderAsset) {
    throw new Error('No rendered video asset found');
  }
  
  console.log(`✅ Render output verified: ${renderAsset.filename} (${renderAsset.file_size} bytes)`);
  return renderAsset;
}

async function main() {
  console.log('=== Integration Test: Full Pipeline ===\n');
  
  try {
    // Check if sample video exists
    if (!fs.existsSync(SAMPLE_VIDEO_PATH)) {
      console.error(`❌ Sample video not found: ${SAMPLE_VIDEO_PATH}`);
      console.log('\nUsage: node test_integration_sample.js <path-to-video.mp4>');
      process.exit(1);
    }
    
    // Run pipeline
    const projectId = await createProject();
    const assetId = await uploadVideo(projectId, SAMPLE_VIDEO_PATH);
    const workflowId = await triggerWorkflow(projectId, assetId);
    await pollWorkflowStatus(projectId, workflowId);
    await verifyRenderOutput(projectId);
    
    console.log('\n✅ INTEGRATION TEST PASSED\n');
    process.exit(0);
    
  } catch (err) {
    console.error('\n❌ INTEGRATION TEST FAILED');
    console.error(err.message);
    console.error(err.stack);
    process.exit(1);
  }
}

main();
