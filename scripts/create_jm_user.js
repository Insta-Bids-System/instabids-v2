import { createClient } from '@supabase/supabase-js'

// Hardcode the values for now since we know them
const supabaseUrl = 'https://xrhgrthdcaymxuqcgrmj.supabase.co'
const supabaseServiceKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhyaGdydGhkY2F5bXh1cWNncm1qIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MzY1NzIwNiwiZXhwIjoyMDY5MjMzMjA2fQ.BH3hCDZUqUvCF0RL_50KXrNHWH7aWaZQKTqCTxLm8AI'

if (!supabaseUrl || !supabaseServiceKey) {
  console.error('Missing Supabase environment variables')
  process.exit(1)
}

const supabase = createClient(supabaseUrl, supabaseServiceKey, {
  auth: {
    autoRefreshToken: false,
    persistSession: false
  }
})

async function createJMHolidayLightingUser() {
  try {
    // Create the auth user
    const { data: authData, error: authError } = await supabase.auth.admin.createUser({
      email: 'jmholidaylighting@gmail.com',
      password: 'JMHoliday2024!',
      email_confirm: true
    })

    if (authError) {
      console.error('Error creating auth user:', authError)
      return
    }

    console.log('Auth user created:', authData.user.id)

    // Create the profile
    const { error: profileError } = await supabase
      .from('profiles')
      .insert({
        id: authData.user.id,
        email: 'jmholidaylighting@gmail.com',
        role: 'contractor',
        full_name: 'JM Holiday Lighting',
        company_name: 'JM Holiday Lighting, Inc.',
        created_at: new Date().toISOString()
      })

    if (profileError) {
      console.error('Error creating profile:', profileError)
      return
    }

    console.log('Profile created successfully!')
    console.log('\nLogin credentials:')
    console.log('Email: jmholidaylighting@gmail.com')
    console.log('Password: JMHoliday2024!')
    
  } catch (error) {
    console.error('Unexpected error:', error)
  }
}

createJMHolidayLightingUser()