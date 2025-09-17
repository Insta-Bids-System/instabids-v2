# Iris AI System - Manual Testing Guide
**Last Updated**: January 31, 2025

## 🧪 Complete Test Procedure

### Prerequisites
1. **Backend Running**: `cd ai-agents && python main.py` (port 8008)
2. **Frontend Running**: `cd web && npm run dev` (port 5181)
3. **Test Images**: Any home/backyard photos on your computer

### Step-by-Step Test Flow

#### 1. Access the System
1. Open browser to http://localhost:5181
2. Login with test credentials
3. Navigate to Dashboard → Inspiration Board tab

#### 2. Create a New Board
1. Click "Create New Board"
2. Name it "Backyard Transformation Test"
3. Select room type: "Backyard/Outdoor"

#### 3. Start Iris Chat
1. Click the AI Assistant (sparkles) button
2. You should see "Hi! I'm Iris, your design assistant"
3. Type: "I want to transform my backyard with artificial turf"
4. Verify Iris responds with helpful questions

#### 4. Test Image Upload & Categorization
1. **Upload Current Space**:
   - Click camera icon in chat
   - Select "Current Space" category
   - Upload a photo of existing backyard
   - Verify: Image appears with "Current Space" label

2. **Upload Inspiration**:
   - Upload another image
   - Select "Inspiration" category (default)
   - Upload turf/lawn inspiration photo
   - Verify: Image appears in middle column

3. **Test New Categorizer UI**:
   - Go to board view (exit chat)
   - Toggle to three-column view
   - Hover over any image
   - Verify: Three buttons appear (Home/Sparkles/Target)
   - Click buttons to move images between columns

#### 5. Test AI Analysis
1. Return to Iris chat
2. Ask: "What do you see in my current backyard?"
3. Verify: Iris describes the uploaded images
4. Ask: "What elements from the inspiration should we incorporate?"
5. Verify: Iris identifies specific design elements

#### 6. Test Dream Space Generation
1. In chat, type: "Can you show me what my backyard would look like with artificial turf?"
2. Wait for Iris to acknowledge
3. Verify: "Generate Dream Space" button appears
4. Click the button
5. Wait 10-15 seconds for generation
6. Verify: New AI-generated image appears showing transformed space

#### 7. Test Feedback Loop
1. If generated image appears, type feedback:
   "Make the turf a brighter green color"
2. Verify: Regeneration option appears
3. Test regeneration with feedback

#### 8. Test Three-Column Organization
1. Exit chat and go to board view
2. Toggle to three-column view
3. Verify columns show:
   - **Current Space**: Your original photos
   - **Inspiration**: Reference images
   - **My Vision**: Generated dream spaces
4. Test drag & drop between columns (if implemented)

#### 9. Test Missing Features
1. Look for "Start Project" button in vision column ❌ NOT FOUND
2. Try to access project detail page ❌ 404 ERROR
3. Look for bid cards ❌ NOT IMPLEMENTED
4. Try contractor messaging ❌ NOT AVAILABLE

### Expected Results

#### ✅ What Should Work
- [x] Iris chat conversation
- [x] Board creation
- [x] Image upload with categories
- [x] Three-column view
- [x] Image categorization UI
- [x] AI image analysis (backend)
- [x] Dream space generation
- [x] Conversation persistence

#### ❌ What Won't Work
- [ ] "Start Project from Vision" button
- [ ] Project detail pages (404 error)
- [ ] Bid card viewing
- [ ] Contractor messaging
- [ ] Dashboard project cards
- [ ] Mobile optimization

### Common Issues & Solutions

**Issue**: "Invalid API key" error
**Solution**: Backend needs correct Supabase credentials in .env

**Issue**: Images don't categorize
**Solution**: Check browser console for errors, verify Supabase connection

**Issue**: Dream generation fails  
**Solution**: Verify OPENAI_API_KEY is set in backend .env

**Issue**: Can't see AI analysis
**Solution**: Analysis is stored but UI doesn't display it yet

### Test Data Verification

After testing, verify in browser DevTools:
```javascript
// Check board data
const boards = await supabase.from('inspiration_boards').select('*')
console.log(boards)

// Check images with analysis
const images = await supabase.from('inspiration_images').select('*')
console.log(images.data[0].ai_analysis) // Should contain Claude's analysis

// Check dream spaces
const dreams = await supabase.from('generated_dream_spaces').select('*')
console.log(dreams)
```

### Performance Checks
- Image upload: Should be < 2 seconds
- AI analysis: Should be < 5 seconds
- Dream generation: Should be < 15 seconds
- Column switching: Should be instant

## 📊 Test Coverage Summary

| Feature | Frontend | Backend | Integration |
|---------|----------|---------|-------------|
| Iris Chat | ✅ | ✅ | ✅ |
| Image Upload | ✅ | ✅ | ✅ |
| Categorization | ✅ | ✅ | ✅ |
| AI Analysis | ❌ Display | ✅ | 🟡 Partial |
| Dream Generation | 🟡 Basic | ✅ | ✅ |
| Project Creation | ❌ | ❌ | ❌ |
| CIA Handoff | ❌ | ❌ | ❌ |