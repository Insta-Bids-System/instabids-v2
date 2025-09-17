# Personal InstaBids Account Setup Guide
**Date**: January 13, 2025
**Purpose**: Set up your personal account for real house testing

## 🏠 Quick Setup for Your House

### Step 1: Start the System
```bash
# Navigate to your InstaBids project
cd C:\Users\Not John Or Justin\Documents\instabids

# Start the development environment
docker-compose up -d

# Verify services are running
docker-compose ps
```

### Step 2: Create Your Personal Account
1. **Open browser**: http://localhost:5173
2. **Click "Sign Up"** (no more demo buttons!)
3. **Enter YOUR details**:
   - Email: `your-email@example.com` (your real email)
   - Full Name: `Your Real Name`  
   - Role: `Homeowner`
   - Password: Choose a secure password

### Step 3: Test IRIS with Your House
1. **Login** with your new account
2. **Go to Dashboard** → My Property tab
3. **Add Property**: Create a property record for your house
4. **Upload Real Photos**: Take photos of rooms in your house
5. **Chat with IRIS**: Start conversations about your real property needs

## 🔧 What's Been Fixed

### ✅ Authentication System
- **REMOVED**: All demo user buttons and hardcoded UUIDs
- **ADDED**: Real Supabase authentication with user registration
- **FIXED**: Properties and photos now linked to authenticated users only

### ✅ Property System  
- **REMOVED**: Hardcoded user ID fallbacks (`550e8400-e29b-41d4-a716-446655440001`)
- **FIXED**: Properties require real user authentication
- **SECURED**: No more "show all data" fallbacks

### ✅ API Security
- **REMOVED**: Dangerous fallbacks that showed all bid cards
- **ADDED**: Proper error handling that respects user boundaries
- **SECURED**: All API calls now require authenticated user context

## 🏡 Your Real Testing Journey

### Phase 1: Account & Property Setup
1. Create your personal account ✅
2. Add your house as a property ✅  
3. Take photos of different rooms ✅

### Phase 2: IRIS Interaction
1. Upload photos from your house ✅
2. Chat with IRIS about renovations/repairs ✅
3. Test inspiration board functionality ✅
4. Generate bid cards from conversations ✅

### Phase 3: Full Workflow
1. Complete homeowner project workflow ✅
2. Test property management features ✅
3. Verify data persistence across sessions ✅

## 🚨 Important Notes

### **No More Hardcoded Data**
- System now requires real user authentication
- All data is properly linked to your account
- Photos uploaded from your house will be saved to your profile

### **Real User Experience**
- Registration creates actual database records
- Login sessions persist properly  
- All IRIS conversations linked to your account
- Property data separated by user

### **Clean Demo Environment**
- No more demo buttons cluttering the interface
- Professional login/signup flow
- Real authentication with password requirements
- Proper error handling for unauthenticated access

## 🔧 Troubleshooting

### If you see login issues:
1. Make sure Docker containers are running: `docker-compose ps`
2. Check backend is accessible: `curl http://localhost:8008`
3. Clear browser localStorage: F12 → Application → Local Storage → Clear All

### If IRIS doesn't respond:
1. Verify you're logged in with a real account (not demo)
2. Make sure property is created and linked to your user
3. Check that photos have your user_id in the database

### If data doesn't persist:
1. Confirm you created a real account (not using demo buttons)
2. Check that you're always logged in with the same account
3. Verify property ownership in the database

## 🎯 Success Criteria

**You'll know it's working when**:
✅ You register with your real email and see confirmation
✅ You can create property records for your actual house  
✅ Photos upload successfully and show in your property dashboard
✅ IRIS remembers your conversations between sessions
✅ All data is isolated to your account (no sharing with demo users)

**Ready to test with your house**: Start with Step 1 above!