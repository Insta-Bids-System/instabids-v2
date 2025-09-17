require('dotenv').config();
const { createClient } = require('@supabase/supabase-js');

const supabaseUrl = process.env.VITE_SUPABASE_URL;
const supabaseServiceKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

console.log('Checking boards for demo user...');

async function checkBoards() {
  const supabase = createClient(supabaseUrl, supabaseServiceKey);
  
  const { data, error } = await supabase
    .from('inspiration_boards')
    .select('*')
    .eq('user_id', '550e8400-e29b-41d4-a716-446655440001')
    .order('created_at', { ascending: false });
  
  if (error) {
    console.error('Error:', error);
  } else {
    console.log(`Found ${data.length} boards:`);
    data.forEach(board => {
      console.log(`- ${board.title} (${board.id}) - Status: ${board.status}`);
    });
  }
}

checkBoards();