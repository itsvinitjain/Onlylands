#!/usr/bin/env node

/**
 * Environment variable substitution script for production builds
 * This script replaces ${VAR_NAME} placeholders in .env file with actual environment values
 */

const fs = require('fs');
const path = require('path');

const envFile = path.join(__dirname, '.env');

try {
  if (fs.existsSync(envFile)) {
    let content = fs.readFileSync(envFile, 'utf8');
    
    // Replace ${BACKEND_URL} with actual BACKEND_URL environment variable
    if (process.env.BACKEND_URL) {
      content = content.replace('${BACKEND_URL}', process.env.BACKEND_URL);
      console.log(`✅ Substituted BACKEND_URL with: ${process.env.BACKEND_URL}`);
    } else {
      // Fallback to localhost for development
      content = content.replace('${BACKEND_URL}', 'http://localhost:8001');
      console.log('⚠️ BACKEND_URL not found, using localhost fallback');
    }
    
    // Write the updated content back
    fs.writeFileSync(envFile, content);
    console.log('✅ Environment variables substituted successfully');
  }
} catch (error) {
  console.error('❌ Error substituting environment variables:', error);
  process.exit(1);
}