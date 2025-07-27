#!/usr/bin/env node

/**
 * Build verification script
 * Ensures all necessary files and configurations are in place before build
 */

const fs = require('fs');
const path = require('path');

console.log('🔧 Running pre-build checks...');

// Check if essential files exist
const essentialFiles = [
  'package.json',
  'public/index.html',
  'src/index.js',
  'src/App.js'
];

let allFilesExist = true;

for (const file of essentialFiles) {
  const filePath = path.join(__dirname, file);
  if (!fs.existsSync(filePath)) {
    console.error(`❌ Missing essential file: ${file}`);
    allFilesExist = false;
  } else {
    console.log(`✅ Found: ${file}`);
  }
}

// Check environment configuration
const envPath = path.join(__dirname, '.env');
if (fs.existsSync(envPath)) {
  const envContent = fs.readFileSync(envPath, 'utf8');
  if (envContent.includes('REACT_APP_BACKEND_URL')) {
    console.log('✅ Backend URL configuration found');
  } else {
    console.warn('⚠️ REACT_APP_BACKEND_URL not found in .env');
  }
} else {
  console.warn('⚠️ No .env file found');
}

if (allFilesExist) {
  console.log('🎉 All pre-build checks passed!');
  process.exit(0);
} else {
  console.error('❌ Pre-build checks failed!');
  process.exit(1);
}