#!/usr/bin/env node

/**
 * InstaBids Code Quality Check - Agent 6 Unified Linter
 * 
 * This script runs all code quality checks across the entire codebase.
 * Use this for fast inner-loop development and agent quality checks.
 * 
 * Usage:
 *   node check-all.js           # Run all checks
 *   node check-all.js --fix     # Run checks and auto-fix issues
 *   node check-all.js --web     # Only check web directory (TypeScript)
 *   node check-all.js --python  # Only check ai-agents directory (Python)
 */

const { execSync } = require('child_process');
const path = require('path');
const fs = require('fs');

// Colors for console output
const colors = {
    reset: '\x1b[0m',
    bright: '\x1b[1m',
    red: '\x1b[31m',
    green: '\x1b[32m',
    yellow: '\x1b[33m',
    blue: '\x1b[34m',
    magenta: '\x1b[35m',
    cyan: '\x1b[36m',
};

// Command line arguments
const args = process.argv.slice(2);
const shouldFix = args.includes('--fix');
const webOnly = args.includes('--web');
const pythonOnly = args.includes('--python');

// Helper functions
function log(message, color = colors.reset) {
    console.log(`${color}${message}${colors.reset}`);
}

function execCommand(command, cwd = process.cwd()) {
    try {
        const result = execSync(command, { 
            cwd, 
            encoding: 'utf8',
            stdio: 'pipe'
        });
        return { success: true, output: result };
    } catch (error) {
        return { 
            success: false, 
            output: error.stdout || error.stderr || error.message 
        };
    }
}

function checkDirectory(dir) {
    try {
        return fs.existsSync(dir) && fs.lstatSync(dir).isDirectory();
    } catch {
        return false;
    }
}

// Main execution
async function main() {
    log('\n🤖 InstaBids Code Quality Check - Agent 6', colors.cyan + colors.bright);
    log('=' .repeat(60), colors.cyan);
    
    const startTime = Date.now();
    let totalErrors = 0;
    let totalWarnings = 0;
    let totalFixed = 0;
    
    // Check TypeScript/JavaScript with Biome
    if (!pythonOnly) {
        log('\n📦 Checking TypeScript/JavaScript (Biome)...', colors.blue + colors.bright);
        
        const webDir = path.join(process.cwd(), 'web');
        if (!checkDirectory(webDir)) {
            log('❌ Web directory not found', colors.red);
        } else {
            const biomeCommand = shouldFix ? 'npx biome check --write' : 'npx biome check';
            const result = execCommand(biomeCommand, webDir);
            
            if (result.success) {
                log('✅ Biome check passed', colors.green);
                // Parse output for statistics
                const output = result.output;
                if (output.includes('Checked')) {
                    log(`   ${output.trim()}`, colors.reset);
                }
            } else {
                // Parse Biome output for error counts
                const output = result.output;
                const errorMatch = output.match(/(\d+) error/);
                const warningMatch = output.match(/(\d+) warning/);
                const fixedMatch = output.match(/(\d+) fixed/);
                
                if (errorMatch) totalErrors += parseInt(errorMatch[1]);
                if (warningMatch) totalWarnings += parseInt(warningMatch[1]);
                if (fixedMatch) totalFixed += parseInt(fixedMatch[1]);
                
                log('⚠️  Biome found issues:', colors.yellow);
                console.log(output);
            }
        }
    }
    
    // Check Python with Ruff
    if (!webOnly) {
        log('\n🐍 Checking Python (Ruff)...', colors.blue + colors.bright);
        
        const aiAgentsDir = path.join(process.cwd(), 'ai-agents');
        if (!checkDirectory(aiAgentsDir)) {
            log('❌ ai-agents directory not found', colors.red);
        } else {
            const ruffCommand = shouldFix ? 'ruff check --fix' : 'ruff check --statistics';
            const result = execCommand(ruffCommand, aiAgentsDir);
            
            if (result.success && !shouldFix) {
                log('✅ Ruff check passed', colors.green);
            } else {
                // Parse Ruff output for statistics
                const output = result.output;
                
                if (shouldFix) {
                    // Parse fix results
                    const fixedMatch = output.match(/(\d+) fixed/);
                    const remainingMatch = output.match(/(\d+) remaining/);
                    
                    if (fixedMatch) totalFixed += parseInt(fixedMatch[1]);
                    if (remainingMatch) totalErrors += parseInt(remainingMatch[1]);
                    
                    log(`🔧 Ruff auto-fixed issues`, colors.green);
                    if (remainingMatch && parseInt(remainingMatch[1]) > 0) {
                        log(`   ${remainingMatch[1]} issues remaining (need manual review)`, colors.yellow);
                    }
                } else {
                    // Parse statistics
                    const lines = output.split('\\n');
                    let errorCount = 0;
                    
                    for (const line of lines) {
                        const match = line.match(/^\\s*(\\d+)\\s+/);
                        if (match) {
                            errorCount += parseInt(match[1]);
                        }
                    }
                    
                    totalErrors += errorCount;
                    
                    if (errorCount > 0) {
                        log(`⚠️  Ruff found ${errorCount} issues:`, colors.yellow);
                        console.log(output);
                    } else {
                        log('✅ No Python issues found', colors.green);
                    }
                }
            }
        }
    }
    
    // Summary
    const endTime = Date.now();
    const duration = ((endTime - startTime) / 1000).toFixed(2);
    
    log('\\n' + '=' . repeat(60), colors.cyan);
    log('📊 Summary:', colors.cyan + colors.bright);
    
    if (shouldFix) {
        log(`✅ Fixed: ${totalFixed} issues`, colors.green);
        if (totalErrors > 0) {
            log(`⚠️  Remaining: ${totalErrors} issues (need manual review)`, colors.yellow);
        }
    } else {
        if (totalErrors > 0) {
            log(`❌ Errors: ${totalErrors}`, colors.red);
        }
        if (totalWarnings > 0) {
            log(`⚠️  Warnings: ${totalWarnings}`, colors.yellow);
        }
        if (totalErrors === 0 && totalWarnings === 0) {
            log('🎉 All checks passed!', colors.green + colors.bright);
        }
    }
    
    log(`⏱️  Completed in ${duration}s`, colors.reset);
    
    // Agent 6 specific message
    log('\\n🤖 Agent 6 Code Quality Status:', colors.magenta + colors.bright);
    if (totalErrors === 0 && totalWarnings === 0) {
        log('✅ Codebase is clean and ready for production', colors.green);
    } else if (totalErrors < 200) {
        log('⚡ Good progress! Continue fixing remaining issues', colors.yellow);
    } else {
        log('🚧 Major cleanup needed. Run with --fix flag first', colors.red);
    }
    
    // Exit with appropriate code
    process.exit(totalErrors > 0 ? 1 : 0);
}

// Handle errors gracefully
process.on('uncaughtException', (error) => {
    log(`\\n❌ Error: ${error.message}`, colors.red);
    process.exit(1);
});

// Run the main function
main().catch((error) => {
    log(`\\n❌ Error: ${error.message}`, colors.red);
    process.exit(1);
});