const sqlite3 = require('sqlite3').verbose();
const path = 'C:/Users/Not John Or Justin/Documents/instabids/data/cipher-sessions.db';

const db = new sqlite3.Database(path);

console.log('=== CHECKING DATABASE CONTENT ===');

// Check store table
db.all("SELECT COUNT(*) as count FROM store", [], (err, rows) => {
    if (err) {
        console.error('Error counting store:', err);
    } else {
        console.log('Store table records:', rows[0].count);
    }
    
    // Get sample data from store
    db.all("SELECT * FROM store LIMIT 3", [], (err, storeRows) => {
        if (err) {
            console.error('Error querying store:', err);
        } else {
            console.log('Sample store records:', storeRows);
        }
        
        // Check lists table
        db.all("SELECT COUNT(*) as count FROM lists", [], (err, rows) => {
            if (err) {
                console.error('Error counting lists:', err);
            } else {
                console.log('Lists table records:', rows[0].count);
            }
            
            // Get sample data from lists
            db.all("SELECT * FROM lists LIMIT 3", [], (err, listRows) => {
                if (err) {
                    console.error('Error querying lists:', err);
                } else {
                    console.log('Sample list records:', listRows);
                }
                
                // Check list_metadata table
                db.all("SELECT * FROM list_metadata LIMIT 3", [], (err, metaRows) => {
                    if (err) {
                        console.error('Error querying list_metadata:', err);
                    } else {
                        console.log('Sample metadata records:', metaRows);
                    }
                    db.close();
                });
            });
        });
    });
});