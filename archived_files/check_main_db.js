const sqlite3 = require('sqlite3').verbose();
const path = 'C:/Users/Not John Or Justin/data/cipher-sessions.db';

const db = new sqlite3.Database(path, (err) => {
    if (err) {
        console.error('Error opening main database:', err);
        return;
    }
    console.log('Main database opened successfully');
});

// Get table info
db.all("SELECT name FROM sqlite_master WHERE type='table'", [], (err, rows) => {
    if (err) {
        console.error('Error querying tables:', err);
        return;
    }
    console.log('Tables found:', rows.map(row => row.name));
    
    // Check if it has the store table like the other one
    if (rows.find(row => row.name === 'store')) {
        db.all("SELECT COUNT(*) as count FROM store", [], (err, countRows) => {
            if (err) {
                console.error('Error counting store records:', err);
            } else {
                console.log('Total store records:', countRows[0].count);
                
                // Get sample data to see if it has InstaBids info
                db.all("SELECT key, created_at, length(value) as value_length FROM store ORDER BY created_at LIMIT 10", [], (err, sampleRows) => {
                    if (err) {
                        console.error('Error querying sample data:', err);
                    } else {
                        console.log('Sample records:');
                        sampleRows.forEach((row, i) => {
                            console.log(`${i+1}. Key: ${row.key}, Created: ${new Date(row.created_at)}, Value Length: ${row.value_length} chars`);
                        });
                    }
                    db.close();
                });
            }
        });
    } else {
        console.log('No store table found in main database');
        db.close();
    }
});