#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

// Find all TSX files in the web/src directory
function findTsxFiles(dir) {
    const files = [];
    const items = fs.readdirSync(dir);
    
    for (const item of items) {
        const fullPath = path.join(dir, item);
        const stat = fs.statSync(fullPath);
        
        if (stat.isDirectory()) {
            files.push(...findTsxFiles(fullPath));
        } else if (item.endsWith('.tsx')) {
            files.push(fullPath);
        }
    }
    
    return files;
}

// Fix button type issues in a file
function fixButtons(filePath) {
    let content = fs.readFileSync(filePath, 'utf8');
    let modified = false;
    
    // Pattern 1: <button onClick={...} without type
    const buttonPattern = /<button(\s+[^>]*?)onClick=\{[^}]+\}([^>]*?)>/g;
    content = content.replace(buttonPattern, (match, before, after) => {
        if (!match.includes('type=')) {
            modified = true;
            return `<button${before}type="button" onClick={match.match(/onClick=\{[^}]+\}/)[0]}${after}>`;
        }
        return match;
    });
    
    // Pattern 2: Simple fix for buttons without closing >
    const simpleButtonPattern = /<button\s+onClick=[^>]*(?!type=)[^>]*>/g;
    content = content.replace(simpleButtonPattern, (match) => {
        if (!match.includes('type=')) {
            modified = true;
            // Insert type="button" after <button
            return match.replace('<button', '<button type="button"');
        }
        return match;
    });
    
    if (modified) {
        fs.writeFileSync(filePath, content);
        console.log(`✅ Fixed buttons in: ${filePath}`);
        return 1;
    }
    
    return 0;
}

// Main execution
const webSrcDir = path.join(process.cwd(), 'web', 'src');
if (!fs.existsSync(webSrcDir)) {
    console.log('❌ web/src directory not found');
    process.exit(1);
}

console.log('🔧 Fixing button type attributes...');
const tsxFiles = findTsxFiles(webSrcDir);
let fixedCount = 0;

for (const file of tsxFiles) {
    fixedCount += fixButtons(file);
}

console.log(`\n🎉 Fixed ${fixedCount} files with button type issues`);
console.log('Run npm run check-all:web to verify fixes');