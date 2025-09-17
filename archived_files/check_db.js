const sqlite3 = require('sqlite3').verbose();
const path = 'C:/Users/Not John Or Justin/Documents/instabids/data/cipher-sessions.db';

console.log('Checking Cipher database...');

const db = new sqlite3.Database(path, (err) => {
    if (err) {
        console.error('Error opening database:', err);
        return;
    }
    console.log('Database opened successfully');
});

// Get table info
db.all("SELECT name FROM sqlite_master WHERE type='table'", [], (err, rows) => {
    if (err) {
        console.error('Error querying tables:', err);
        return;
    }
    console.log('Tables found:', rows.map(row => row.name));
    
    // Check sessions table if it exists
    if (rows.find(row => row.name === 'sessions')) {
        db.all("SELECT COUNT(*) as count FROM sessions", [], (err, countRows) => {
            if (err) {
                console.error('Error counting sessions:', err);
            } else {
                console.log('Number of sessions:', countRows[0].count);
            }
            
            // Get sample session data
            db.all("SELECT sessionId, createdAt FROM sessions LIMIT 3", [], (err, sessionRows) => {
                if (err) {
                    console.error('Error querying sessions:', err);
                } else {
                    console.log('Sample sessions:', sessionRows);
                }
                db.close();
            });
        });
    } else {
        console.log('No sessions table found');
        db.close();
    }
});