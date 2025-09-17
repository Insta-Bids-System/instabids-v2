const fs = require('fs');
const { createCanvas } = require('canvas');

// Create a 800x600 canvas
const canvas = createCanvas(800, 600);
const ctx = canvas.getContext('2d');

// Kitchen background
ctx.fillStyle = '#f0f0f0';
ctx.fillRect(0, 0, 800, 600);

// Cabinets
ctx.fillStyle = '#FFFFFF';
ctx.fillRect(50, 50, 700, 200);

// Cabinet doors with shaker style
ctx.strokeStyle = '#E0E0E0';
ctx.lineWidth = 2;
for (let i = 0; i < 7; i++) {
    const x = 50 + i * 100;
    ctx.strokeRect(x, 50, 100, 200);
    // Inner rectangle for shaker style
    ctx.strokeRect(x + 10, 60, 80, 180);
}

// Cabinet hardware
ctx.fillStyle = '#000000';
for (let i = 0; i < 7; i++) {
    const x = 50 + i * 100 + 80;
    ctx.fillRect(x, 140, 10, 2);
}

// Countertop (marble look)
ctx.fillStyle = '#F5F5F5';
ctx.fillRect(50, 250, 700, 50);
ctx.strokeStyle = '#D0D0D0';
ctx.beginPath();
ctx.moveTo(100, 260);
ctx.lineTo(150, 280);
ctx.moveTo(200, 255);
ctx.lineTo(250, 275);
ctx.moveTo(300, 265);
ctx.lineTo(350, 285);
ctx.stroke();

// Subway tile backsplash
ctx.fillStyle = '#FFFFFF';
ctx.fillRect(50, 300, 700, 100);
ctx.strokeStyle = '#E0E0E0';
ctx.lineWidth = 1;
// Draw subway tiles
for (let row = 0; row < 5; row++) {
    for (let col = 0; col < 14; col++) {
        const offset = row % 2 === 0 ? 0 : 25;
        ctx.strokeRect(50 + col * 50 + offset, 300 + row * 20, 50, 20);
    }
}

// Hardwood floor
ctx.fillStyle = '#8B6F47';
ctx.fillRect(0, 400, 800, 200);
// Floor boards
ctx.strokeStyle = '#7A5F37';
ctx.lineWidth = 1;
for (let i = 0; i < 8; i++) {
    ctx.beginPath();
    ctx.moveTo(0, 400 + i * 25);
    ctx.lineTo(800, 400 + i * 25);
    ctx.stroke();
}

// Kitchen island
ctx.fillStyle = '#2C3E50';
ctx.fillRect(250, 450, 300, 100);
// Island countertop
ctx.fillStyle = '#F5F5F5';
ctx.fillRect(240, 440, 320, 20);

// Modern pendant lights
ctx.strokeStyle = '#000000';
ctx.lineWidth = 2;
// Light 1
ctx.beginPath();
ctx.moveTo(300, 300);
ctx.lineTo(300, 350);
ctx.stroke();
ctx.fillStyle = '#FFD700';
ctx.beginPath();
ctx.arc(300, 360, 15, 0, Math.PI * 2);
ctx.fill();
ctx.stroke();

// Light 2
ctx.beginPath();
ctx.moveTo(500, 300);
ctx.lineTo(500, 350);
ctx.stroke();
ctx.fillStyle = '#FFD700';
ctx.beginPath();
ctx.arc(500, 360, 15, 0, Math.PI * 2);
ctx.fill();
ctx.stroke();

// Title
ctx.fillStyle = '#2C3E50';
ctx.font = 'bold 32px Arial';
ctx.fillText('Modern Kitchen Renovation', 50, 35);

// Subtitle
ctx.font = '18px Arial';
ctx.fillText('White Shaker Cabinets • Marble Countertops • Subway Tile', 50, 580);

// Save as PNG
const buffer = canvas.toBuffer('image/png');
fs.writeFileSync('test_kitchen.png', buffer);
console.log('Test kitchen image created: test_kitchen.png');