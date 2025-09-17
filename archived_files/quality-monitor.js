#!/usr/bin/env node

/**
 * InstaBids Quality Monitor - Agent 6 Automated Quality Tracking
 * 
 * This script provides real-time quality monitoring and progress tracking
 * for the InstaBids codebase. It runs quality checks and maintains
 * historical quality metrics.
 * 
 * Usage:
 *   node quality-monitor.js         # Run quality check and update metrics
 *   node quality-monitor.js --watch # Continuous monitoring mode
 *   node quality-monitor.js --report # Generate quality report
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

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
const watchMode = args.includes('--watch');
const reportMode = args.includes('--report');

// Quality metrics file
const METRICS_FILE = path.join(__dirname, 'quality-metrics.json');

// Helper functions
function log(message, color = colors.reset) {
    const timestamp = new Date().toISOString().split('T')[1].split('.')[0];
    console.log(`${colors.cyan}[${timestamp}]${colors.reset} ${color}${message}${colors.reset}`);
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

// Load existing metrics or create new ones
function loadMetrics() {
    if (fs.existsSync(METRICS_FILE)) {
        try {
            return JSON.parse(fs.readFileSync(METRICS_FILE, 'utf8'));
        } catch (error) {
            log('Warning: Could not load existing metrics, starting fresh', colors.yellow);
        }
    }
    
    return {
        created: new Date().toISOString(),
        measurements: [],
        milestones: []
    };
}

// Save metrics to file
function saveMetrics(metrics) {
    fs.writeFileSync(METRICS_FILE, JSON.stringify(metrics, null, 2));
}

// Run quality check and extract metrics
function getQualityMetrics() {
    const metrics = {
        timestamp: new Date().toISOString(),
        python: { errors: 0, warnings: 0, score: 100 },
        typescript: { errors: 0, warnings: 0, score: 0 },
        overall: { errors: 0, warnings: 0, score: 0 }
    };
    
    // Check Python with Ruff
    log('Checking Python quality...', colors.blue);
    const pythonResult = execCommand('ruff check --statistics', path.join(__dirname, 'ai-agents'));
    
    if (pythonResult.success) {
        // Parse Ruff statistics output
        const lines = pythonResult.output.split('\\n');
        let errorCount = 0;
        
        for (const line of lines) {
            const match = line.match(/^\\s*(\\d+)\\s+/);
            if (match) {
                errorCount += parseInt(match[1]);
            }
        }
        
        metrics.python.errors = errorCount;
        metrics.python.score = Math.max(0, 100 - (errorCount / 10)); // Rough scoring
    } else {
        log('Python check failed', colors.red);
    }
    
    // Check TypeScript with Biome
    log('Checking TypeScript quality...', colors.blue);
    const tsResult = execCommand('npx biome check --diagnostic-level=error', path.join(__dirname, 'web'));
    
    if (!tsResult.success) {
        // Parse Biome output for error counts
        const output = tsResult.output;
        const errorMatch = output.match(/Found (\\d+) errors/);
        const warningMatch = output.match(/Found (\\d+) warnings/);
        
        if (errorMatch) metrics.typescript.errors = parseInt(errorMatch[1]);
        if (warningMatch) metrics.typescript.warnings = parseInt(warningMatch[1]);
        
        // Calculate TypeScript score (0-100)
        const totalIssues = metrics.typescript.errors + (metrics.typescript.warnings * 0.5);
        metrics.typescript.score = Math.max(0, 100 - (totalIssues / 5));
    } else {
        metrics.typescript.score = 100;
    }
    
    // Calculate overall metrics
    metrics.overall.errors = metrics.python.errors + metrics.typescript.errors;
    metrics.overall.warnings = metrics.python.warnings + metrics.typescript.warnings;
    metrics.overall.score = (metrics.python.score + metrics.typescript.score) / 2;
    
    return metrics;
}

// Generate quality report
function generateReport(metrics) {
    log('\\n🤖 InstaBids Quality Monitor Report', colors.cyan + colors.bright);
    log('=' . repeat(60), colors.cyan);
    
    const latest = metrics.measurements[metrics.measurements.length - 1];
    const previous = metrics.measurements[metrics.measurements.length - 2];
    
    if (!latest) {
        log('No quality data available yet', colors.yellow);
        return;
    }
    
    // Current status
    log('\\n📊 Current Quality Status:', colors.blue + colors.bright);
    log(`Overall Score: ${latest.overall.score.toFixed(1)}/100`, getScoreColor(latest.overall.score));
    log(`Python Score:  ${latest.python.score.toFixed(1)}/100`, getScoreColor(latest.python.score));
    log(`TypeScript:    ${latest.typescript.score.toFixed(1)}/100`, getScoreColor(latest.typescript.score));
    
    // Issue counts
    log('\\n🐛 Issue Breakdown:', colors.blue + colors.bright);
    log(`Total Errors:   ${latest.overall.errors}`, latest.overall.errors > 0 ? colors.red : colors.green);
    log(`Total Warnings: ${latest.overall.warnings}`, latest.overall.warnings > 0 ? colors.yellow : colors.green);
    
    // Trend analysis
    if (previous) {
        log('\\n📈 Quality Trends:', colors.blue + colors.bright);
        
        const scoreChange = latest.overall.score - previous.overall.score;
        const errorChange = latest.overall.errors - previous.overall.errors;
        
        if (scoreChange > 0) {
            log(`Score improved by ${scoreChange.toFixed(1)} points`, colors.green);
        } else if (scoreChange < 0) {
            log(`Score decreased by ${Math.abs(scoreChange).toFixed(1)} points`, colors.red);
        } else {
            log('Score unchanged', colors.yellow);
        }
        
        if (errorChange < 0) {
            log(`${Math.abs(errorChange)} fewer errors`, colors.green);
        } else if (errorChange > 0) {
            log(`${errorChange} more errors`, colors.red);
        } else {
            log('Error count unchanged', colors.yellow);
        }
    }
    
    // Historical summary
    if (metrics.measurements.length > 1) {
        log('\\n📚 Historical Summary:', colors.blue + colors.bright);
        log(`Total measurements: ${metrics.measurements.length}`);
        log(`Tracking since: ${new Date(metrics.created).toLocaleDateString()}`);
        
        const firstMeasurement = metrics.measurements[0];
        const totalScoreImprovement = latest.overall.score - firstMeasurement.overall.score;
        const totalErrorReduction = firstMeasurement.overall.errors - latest.overall.errors;
        
        log(`Total score improvement: ${totalScoreImprovement.toFixed(1)} points`, colors.green);
        log(`Total error reduction: ${totalErrorReduction} issues`, colors.green);
    }
    
    // Milestones
    if (metrics.milestones.length > 0) {
        log('\\n🎯 Quality Milestones:', colors.blue + colors.bright);
        metrics.milestones.slice(-5).forEach(milestone => {
            log(`${milestone.date}: ${milestone.description}`, colors.green);
        });
    }
}

// Get color based on score
function getScoreColor(score) {
    if (score >= 90) return colors.green;
    if (score >= 70) return colors.yellow;
    return colors.red;
}

// Check for quality milestones
function checkMilestones(metrics, currentMetrics) {
    const milestones = [];
    
    // Check for major score improvements
    if (metrics.measurements.length > 0) {
        const previous = metrics.measurements[metrics.measurements.length - 1];
        
        if (currentMetrics.overall.score >= 90 && previous.overall.score < 90) {
            milestones.push({
                date: new Date().toISOString().split('T')[0],
                description: 'Achieved 90+ overall quality score! 🎉',
                score: currentMetrics.overall.score
            });
        }
        
        if (currentMetrics.python.score >= 95 && previous.python.score < 95) {
            milestones.push({
                date: new Date().toISOString().split('T')[0],
                description: 'Python codebase achieved 95+ quality score! 🐍',
                score: currentMetrics.python.score
            });
        }
        
        if (currentMetrics.typescript.score >= 80 && previous.typescript.score < 80) {
            milestones.push({
                date: new Date().toISOString().split('T')[0],
                description: 'TypeScript codebase achieved 80+ quality score! ⚛️',
                score: currentMetrics.typescript.score
            });
        }
    }
    
    return milestones;
}

// Main monitoring function
async function runQualityCheck() {
    log('🔍 Running quality monitoring...', colors.cyan);
    
    // Load existing metrics
    const metrics = loadMetrics();
    
    // Get current quality metrics
    const currentMetrics = getQualityMetrics();
    
    // Check for milestones
    const newMilestones = checkMilestones(metrics, currentMetrics);
    metrics.milestones.push(...newMilestones);
    
    // Add current measurement
    metrics.measurements.push(currentMetrics);
    
    // Keep only last 100 measurements to avoid huge files
    if (metrics.measurements.length > 100) {
        metrics.measurements = metrics.measurements.slice(-100);
    }
    
    // Save updated metrics
    saveMetrics(metrics);
    
    // Log milestones
    newMilestones.forEach(milestone => {
        log(`🎯 MILESTONE: ${milestone.description}`, colors.green + colors.bright);
    });
    
    // Quick status
    log(`✅ Quality check complete - Score: ${currentMetrics.overall.score.toFixed(1)}/100`, colors.green);
    
    return { metrics, currentMetrics };
}

// Watch mode - continuous monitoring
async function runWatchMode() {
    log('👀 Starting continuous quality monitoring...', colors.magenta + colors.bright);
    log('Press Ctrl+C to stop', colors.yellow);
    
    while (true) {
        try {
            await runQualityCheck();
            
            // Wait 30 minutes between checks
            await new Promise(resolve => setTimeout(resolve, 30 * 60 * 1000));
        } catch (error) {
            log(`Error in watch mode: ${error.message}`, colors.red);
            // Wait 5 minutes before retrying
            await new Promise(resolve => setTimeout(resolve, 5 * 60 * 1000));
        }
    }
}

// Main execution
async function main() {
    try {
        if (watchMode) {
            await runWatchMode();
        } else if (reportMode) {
            const metrics = loadMetrics();
            generateReport(metrics);
        } else {
            const { metrics } = await runQualityCheck();
            
            // Show brief report by default
            const latest = metrics.measurements[metrics.measurements.length - 1];
            log('\\n📊 Quality Summary:', colors.cyan);
            log(`Overall: ${latest.overall.score.toFixed(1)}/100 (${latest.overall.errors} errors, ${latest.overall.warnings} warnings)`);
        }
    } catch (error) {
        log(`Error: ${error.message}`, colors.red);
        process.exit(1);
    }
}

// Handle graceful shutdown
process.on('SIGINT', () => {
    log('\\n👋 Quality monitoring stopped', colors.yellow);
    process.exit(0);
});

// Run the main function
main();