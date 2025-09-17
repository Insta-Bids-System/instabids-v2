const sqlite3 = require('sqlite3').verbose();
const path = 'C:/Users/Not John Or Justin/Documents/instabids/data/cipher-sessions.db';

const db = new sqlite3.Database(path);

console.log('=== SEARCHING ALL MEMORY DATA ===');

// Get ALL data from store table
db.all("SELECT key, value, created_at, updated_at FROM store ORDER BY created_at", [], (err, rows) => {
    if (err) {
        console.error('Error querying all store data:', err);
        db.close();
        return;
    }
    
    console.log(`Found ${rows.length} total records:`);
    
    rows.forEach((row, index) => {
        console.log(`\n--- Record ${index + 1} ---`);
        console.log('Key:', row.key);
        console.log('Created:', new Date(row.created_at));
        console.log('Updated:', new Date(row.updated_at));
        
        // Try to parse the value as JSON
        try {
            const parsed = JSON.parse(row.value);
            console.log('Value (parsed):', parsed);
        } catch (e) {
            console.log('Value (raw):', row.value);
        }
    });
    
    db.close();
});