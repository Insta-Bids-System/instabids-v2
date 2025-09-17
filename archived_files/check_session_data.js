const sqlite3 = require('sqlite3').verbose();
const path = 'C:/Users/Not John Or Justin/data/cipher-sessions.db';

const db = new sqlite3.Database(path);

console.log('=== CHECKING MAIN SESSION DATA ===');

// Get the big session record
db.all("SELECT key, value FROM store WHERE key = 'cipher:sessions:default'", [], (err, rows) => {
    if (err) {
        console.error('Error querying session data:', err);
        db.close();
        return;
    }
    
    if (rows.length > 0) {
        console.log('Found main session data!');
        console.log('Key:', rows[0].key);
        console.log('Value length:', rows[0].value.length, 'characters');
        
        try {
            const sessionData = JSON.parse(rows[0].value);
            console.log('Session data structure:', Object.keys(sessionData));
            
            // Look for any InstaBids-related content
            const valueStr = rows[0].value.toLowerCase();
            const instabidsMatches = (valueStr.match(/instabids/g) || []).length;
            const agentMatches = (valueStr.match(/agent/g) || []).length;
            const databaseMatches = (valueStr.match(/database/g) || []).length;
            
            console.log('Content analysis:');
            console.log('- "instabids" mentions:', instabidsMatches);
            console.log('- "agent" mentions:', agentMatches);
            console.log('- "database" mentions:', databaseMatches);
            
            // Show a sample of the content (first 500 chars)
            console.log('\nSample content (first 500 chars):');
            console.log(rows[0].value.substring(0, 500) + '...');
            
        } catch (e) {
            console.log('Could not parse session data as JSON');
            console.log('Raw data preview:', rows[0].value.substring(0, 200) + '...');
        }
    } else {
        console.log('No main session data found');
    }
    
    db.close();
});