# Quick Email Setup for Form Notifications

## Option 1: Formspree (Easiest - 2 minutes)

1. Go to https://formspree.io/
2. Sign up for free account
3. Create a new form
4. Copy your form endpoint (looks like: https://formspree.io/f/xyzabc)
5. In your index.html, find this line:
   ```html
   <form id="businessForm">
   ```
6. Add the Formspree action and method:
   ```html
   <form id="businessForm" action="https://formspree.io/f/YOUR_FORM_ID" method="POST">
   ```
7. That's it! Forms will be sent to your email.

## Option 2: Web3Forms (Also Easy - 3 minutes)

1. Go to https://web3forms.com/
2. Enter your email address
3. Get your access key
4. Add this to your form submission JavaScript:

```javascript
// Add this in the try block of the form submission handler
await fetch('https://api.web3forms.com/submit', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        access_key: 'YOUR_ACCESS_KEY_HERE',
        subject: 'New Lead from Green Lawn Pro',
        from_name: submission.data.contact_name,
        email: submission.data.email,
        message: `
Company: ${submission.data.company_name}
Contact: ${submission.data.contact_name}
Email: ${submission.data.email}
Phone: ${submission.data.phone}
Website: ${submission.data.website || 'Not provided'}
Type: ${submission.data.opportunity_type || 'Not specified'}
Message: ${submission.data.message}
        `
    })
});
```

## Option 3: Webhook to Zapier/Make (5 minutes)

1. Create account at https://zapier.com or https://make.com
2. Create new Zap/Scenario
3. Choose "Webhooks" as trigger
4. Copy the webhook URL
5. In index.html, find and uncomment this section:
   ```javascript
   await fetch('YOUR_WEBHOOK_URL_HERE', {
       method: 'POST',
       headers: {
           'Content-Type': 'application/json',
       },
       body: JSON.stringify(submission)
   });
   ```
6. Replace YOUR_WEBHOOK_URL_HERE with your webhook URL
7. In Zapier/Make, add Gmail or Email action to send you the data

## Testing Your Email Setup

1. Open index.html in your browser
2. Fill out the form with test data
3. Submit the form
4. Check your email (and spam folder)
5. Check the browser console for any errors

## Quick Test Command

Open browser console (F12) and run:
```javascript
// Quick test to see if localStorage is working
const testSubmission = {
    timestamp: new Date().toISOString(),
    data: {
        company_name: "Email Test Company",
        contact_name: "Test Person",
        email: "test@example.com",
        phone: "(555) 000-0000",
        message: "Testing email notifications"
    }
};

let subs = JSON.parse(localStorage.getItem('greenLawnProSubmissions') || '[]');
subs.push(testSubmission);
localStorage.setItem('greenLawnProSubmissions', JSON.stringify(subs));
console.log('Test submission added! Check admin.html');
```