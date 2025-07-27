#!/usr/bin/env node

/**
 * Environment variable substitution script for production builds
 * This script creates .env file from .env.template with substituted values
 */

const fs = require('fs');
const path = require('path');

const templateFile = path.join(__dirname, '.env.template');
const envFile = path.join(__dirname, '.env');

try {
  let content;
  
  // Use template if available, otherwise use existing .env
  if (fs.existsSync(templateFile)) {
    content = fs.readFileSync(templateFile, 'utf8');
    console.log('📄 Using .env.template for environment substitution');
  } else if (fs.existsSync(envFile)) {
    content = fs.readFileSync(envFile, 'utf8');
    console.log('📄 Using existing .env file for substitution');
  } else {
    // Create default .env if neither exists
    content = 'REACT_APP_BACKEND_URL=${BACKEND_URL}\nREACT_APP_RAZORPAY_KEY_ID=rzp_test_demo123\n';
    console.log('📄 Creating default .env configuration');
  }
  
  // Replace ${BACKEND_URL} with actual BACKEND_URL environment variable
  if (process.env.BACKEND_URL) {
    content = content.replace(/\$\{BACKEND_URL\}/g, process.env.BACKEND_URL);
    console.log(`✅ Substituted BACKEND_URL with: ${process.env.BACKEND_URL}`);
  } else {
    // Fallback to localhost for development
    content = content.replace(/\$\{BACKEND_URL\}/g, 'http://localhost:8001');
    console.log('⚠️ BACKEND_URL not found, using localhost fallback');
  }
  
  // Write the updated content to .env
  fs.writeFileSync(envFile, content);
  console.log('✅ Environment variables substituted successfully');
  
} catch (error) {
  console.error('❌ Error substituting environment variables:', error);
  // Don't exit with error code to prevent build failure
  console.log('⚠️ Continuing with existing .env configuration');
}