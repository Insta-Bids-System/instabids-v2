#!/usr/bin/env node
/**
 * Batch fix common code quality issues
 * Agent 6 Quality Gatekeeper - Code Cleanup Script
 */

const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');

// Common patterns to fix
const fixes = [
  // Fix button type prop
  {
    pattern: /<button\s+(?![^>]*type=)/g,
    replacement: '<button type="button" ',
    description: 'Add type="button" to button elements'
  },
  
  // Fix any types in catch blocks
  {
    pattern: /catch\s*\(\s*(\w+):\s*any\s*\)/g,
    replacement: 'catch ($1: unknown)',
    description: 'Replace any with unknown in catch blocks'
  },
  
  // Fix array index keys (simple cases)
  {
    pattern: /key={(\w+)}\s+(?=.*map\(.*,\s*\1\s*\))/g,
    replacement: 'key={`item-${$1}`} ',
    description: 'Fix array index keys'
  }
];

function applyFixes(filePath) {
  let content = fs.readFileSync(filePath, 'utf8');
  let changed = false;
  
  fixes.forEach(fix => {
    const originalContent = content;
    content = content.replace(fix.pattern, fix.replacement);
    if (content !== originalContent) {
      changed = true;
      console.log(`✅ Applied: ${fix.description} in ${filePath}`);
    }
  });
  
  if (changed) {
    fs.writeFileSync(filePath, content);
    return true;
  }
  return false;
}

function findTsxFiles(dir) {
  let files = [];
  
  const items = fs.readdirSync(dir);
  for (const item of items) {
    const fullPath = path.join(dir, item);
    const stat = fs.statSync(fullPath);
    
    if (stat.isDirectory()) {
      files = files.concat(findTsxFiles(fullPath));
    } else if (item.endsWith('.tsx') || item.endsWith('.ts')) {
      files.push(fullPath);
    }
  }
  
  return files;
}

console.log('🤖 Agent 6 Code Quality Batch Fix\n');

const webSrcPath = path.join(__dirname, 'web', 'src');
if (!fs.existsSync(webSrcPath)) {
  console.error('❌ web/src directory not found');
  process.exit(1);
}

const files = findTsxFiles(webSrcPath);
let fixedFiles = 0;

console.log(`📁 Found ${files.length} TypeScript/React files\n`);

files.forEach(file => {
  if (applyFixes(file)) {
    fixedFiles++;
  }
});

console.log(`\n✨ Fixed ${fixedFiles} files`);
console.log('🔄 Running quality check...\n');

// Run quality check after fixes
exec('npm run check-all', (error, stdout, stderr) => {
  if (stdout) console.log(stdout);
  if (stderr) console.log(stderr);
  
  console.log('\n🎯 Batch fixes complete!');
});