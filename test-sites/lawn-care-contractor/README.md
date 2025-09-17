# Green Lawn Pro Test Website

This is a test website for the Instabids AI agents to practice filling out contractor lead forms.

## Features

1. **Working Lead Form** - Fully functional form that captures and stores submissions
2. **Local Storage** - All submissions are saved in browser localStorage
3. **Admin Panel** - View all submissions at `/admin.html`
4. **Test Capabilities** - Can verify AI agents are successfully submitting forms

## Files

- `index.html` - Main contractor website with lead form
- `admin.html` - Admin panel to view all form submissions
- `test-form.html` - Automated form testing page

## How Form Submission Works

1. When a form is submitted, it's stored in localStorage under the key `greenLawnProSubmissions`
2. Each submission includes:
   - Timestamp
   - All form data (company name, contact, email, phone, etc.)
   - User agent information
   - Referrer information

## Viewing Submissions

### Option 1: Admin Panel
Open `admin.html` in your browser to see:
- Total submission count
- Today's submissions
- This week's submissions
- Full details of each submission
- Search/filter functionality
- Export to JSON

### Option 2: Browser Console
```javascript
// View all submissions in console
JSON.parse(localStorage.getItem('greenLawnProSubmissions'))

// Clear all submissions
localStorage.removeItem('greenLawnProSubmissions')
```

### Option 3: Submission Panel
The main page includes a testing panel at the bottom showing all submissions.

## Setting Up Email Notifications (Optional)

### Method 1: Using EmailJS (Free tier available)
1. Sign up at https://www.emailjs.com/
2. Create an email service
3. Create an email template
4. Add to the HTML before closing </body>:
```html
<script src="https://cdn.jsdelivr.net/npm/@emailjs/browser@3/dist/email.min.js"></script>
<script>
    emailjs.init("YOUR_PUBLIC_KEY");
</script>
```
5. Uncomment the EmailJS section in the form submission handler

### Method 2: Using a Webhook
1. Set up a webhook endpoint (e.g., using Zapier, Make.com, or your own server)
2. Replace `YOUR_WEBHOOK_URL_HERE` in the code with your webhook URL
3. Uncomment the webhook section in the form submission handler

### Method 3: Using Formspree (Easiest)
Replace the form action with:
```html
<form id="businessForm" action="https://formspree.io/f/YOUR_FORM_ID" method="POST">
```

## Testing AI Agent Form Submission

1. Have your AI agent navigate to the website
2. Fill out the form fields:
   - Company Name (required)
   - Contact Person (required)
   - Business Email (required)
   - Phone Number (required)
   - Company Website (optional)
   - Opportunity Type (optional dropdown)
   - Message (required)
3. Click "Submit Business Opportunity"
4. Check submissions in:
   - The submission panel on the same page
   - The admin panel (`admin.html`)
   - Browser console
   - Your email (if configured)

## Success Indicators

When a form is successfully submitted:
1. A green success message appears
2. The form is cleared
3. The submission appears in the submissions panel
4. The submission is stored in localStorage
5. Console shows: "Form submitted successfully: {submission data}"

## Troubleshooting

- **Submissions not showing**: Check browser console for errors
- **localStorage full**: Clear old submissions using the "Clear All" button
- **Form not submitting**: Ensure all required fields are filled
- **Email not working**: Check EmailJS configuration or webhook URL

## Security Note

This is a TEST website only. Do not use for production as:
- Data is stored in browser localStorage (not secure)
- No server-side validation
- No spam protection
- Admin panel has no authentication