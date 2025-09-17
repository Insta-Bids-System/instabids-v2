const fs = require('fs');

// Create a simple 100x100 red square PNG
// This is the base64 encoded data for a small red square PNG
const base64Data = 'iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAFUlEQVR42mP8z8BQz0AEYBxVSF+FABJADveWkH6oAAAAAElFTkSuQmCC';

// Convert base64 to buffer
const buffer = Buffer.from(base64Data, 'base64');

// Write to file
fs.writeFileSync('test_kitchen.png', buffer);
console.log('Test image created: test_kitchen.png');