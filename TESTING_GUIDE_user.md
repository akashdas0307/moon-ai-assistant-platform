# Chat UI Testing Guide

## Quick Start

### 1. Start Backend
```bash
cd backend
uvicorn main:app --reload
```

### 2. Start Frontend
```bash
cd frontend
npm run dev
```

### 3. Open Browser
Navigate to: http://localhost:5173

---

## Manual Test Checklist

### ✅ Scroll Behavior Tests

1. **Test Basic Scrolling**
   - [ ] Send 10+ messages to fill the chat
   - [ ] Verify you can scroll up through all messages
   - [ ] Verify you can scroll back down
   - [ ] No "stuck" behavior at top or bottom

2. **Test Auto-Scroll Pause**
   - [ ] Scroll to the top of the chat
   - [ ] Send a new message (using another browser tab or wait for AI response)
   - [ ] Verify chat DOES NOT auto-scroll (stays at top)
   - [ ] Scroll to bottom manually
   - [ ] Send another message
   - [ ] Verify chat DOES auto-scroll (you're at bottom)

3. **Test Scroll-to-Bottom Button**
   - [ ] Scroll up in the chat
   - [ ] Verify a blue scroll-to-bottom button appears (bottom-right)
   - [ ] Click the button
   - [ ] Verify it smoothly scrolls to bottom
   - [ ] Button should disappear when at bottom

### ✅ Message Input Tests

4. **Test Input Focus**
   - [ ] Type a message and press Enter
   - [ ] Verify message sends
   - [ ] Verify input is IMMEDIATELY ready to type again (auto-focused)
   - [ ] No need to click back into input field

5. **Test Keyboard Shortcuts**
   - [ ] Type text and press **Enter** → Should send message
   - [ ] Type text and press **Shift + Enter** → Should add new line (not send)
   - [ ] Press **Ctrl/Cmd + K** → Should focus the input field

6. **Test Input Auto-Resize**
   - [ ] Type a long message with multiple lines
   - [ ] Verify textarea expands (up to ~120px max height)
   - [ ] After sending, verify it returns to single-line height

### ✅ Animation Tests

7. **Test Message Animations**
   - [ ] Send a new message
   - [ ] Verify it fades in smoothly (no sudden pop-in)
   - [ ] Animation should feel natural (250ms duration)

8. **Test Typing Indicator**
   - [ ] Send a message
   - [ ] Verify typing indicator appears (animated dots)
   - [ ] When AI responds, typing indicator disappears

### ✅ Visual Polish Tests

9. **Test Scrollbar Styling**
   - [ ] Hover over the scrollbar
   - [ ] Verify custom styled scrollbar (8px width, gray color)
   - [ ] Hover should lighten the scrollbar thumb
   - [ ] Should match dark theme aesthetics

10. **Test Connection Status**
    - [ ] Check header shows connection status (green dot = connected)
    - [ ] If backend is stopped, verify status changes to red/yellow

11. **Test Empty State**
    - [ ] Clear browser localStorage: `localStorage.clear()`
    - [ ] Refresh page
    - [ ] Verify empty state appears with welcome message
    - [ ] Send first message, empty state should disappear

### ✅ Edge Cases

12. **Test Rapid Message Sending**
    - [ ] Send 5 messages quickly (Enter, Enter, Enter...)
    - [ ] Verify all messages appear
    - [ ] Verify input stays focused throughout
    - [ ] Verify smooth scrolling to bottom

13. **Test Long Messages**
    - [ ] Send a very long message (500+ words)
    - [ ] Verify it wraps properly in the bubble
    - [ ] Verify scrollbar appears in message area

14. **Test Code Blocks** (AI messages)
    - [ ] Ask AI to write some code
    - [ ] Verify syntax highlighting works
    - [ ] Verify copy button appears on code blocks
    - [ ] Click copy, verify "Copied!" feedback

### ✅ Responsive Tests

15. **Test Mobile View**
    - [ ] Resize browser to mobile width (< 768px)
    - [ ] Verify chat still scrolls properly
    - [ ] Verify input still works
    - [ ] Verify animations still smooth

---

## Console Checks

### Open Browser DevTools (F12)

1. **Check Console Tab**
   - [ ] No red errors
   - [ ] No warnings (minor warnings OK)
   - [ ] WebSocket connection logs should appear

2. **Check Network Tab**
   - [ ] WebSocket connection established (ws://localhost:8000/ws)
   - [ ] Status: 101 Switching Protocols (green)

---

## Build & Production Tests

### TypeScript Check
```bash
cd frontend
npm run build
```

**Expected:**
- ✅ Build succeeds
- ✅ No TypeScript errors
- ⚠️ Chunk size warning is OK (optimization, not error)

### Linting
```bash
cd frontend
npm run lint
```

**Expected:**
- ✅ No linting errors
- ⚠️ Minor warnings OK if not critical

---

## Performance Checks

### Check Animations
1. Open DevTools → Performance tab
2. Start recording
3. Send several messages
4. Stop recording
5. Verify:
   - [ ] 60fps maintained during animations
   - [ ] No long tasks blocking main thread

### Check Memory
1. Open DevTools → Memory tab
2. Take heap snapshot
3. Send 50+ messages
4. Take another snapshot
5. Verify:
   - [ ] No significant memory leaks
   - [ ] Memory usage reasonable (< 100MB for chat)

---

## Known Good Behavior

### ✅ What Should Happen
- Smooth scrolling in all directions
- Auto-scroll only when user is at bottom
- Input always ready after sending
- Messages fade in nicely
- Scrollbars themed to dark UI
- Connection status visible and accurate
- No console errors
- Build succeeds

### ❌ What Should NOT Happen
- Chat getting stuck
- Auto-scroll interrupting reading
- Input losing focus
- Sudden message pop-ins (no animation)
- Default browser scrollbars
- TypeScript errors
- Build failures

---

## Automated Testing (Future)

Current status: Manual testing only

**Recommended E2E Tests:**
```typescript
// Example Playwright test
test('should maintain scroll position when user is reading', async ({ page }) => {
  await sendMultipleMessages(10);
  await page.evaluate(() => window.scrollTo(0, 0)); // Scroll to top
  await sendMessage('New message');
  const scrollPosition = await page.evaluate(() => window.scrollY);
  expect(scrollPosition).toBe(0); // Should still be at top
});
```

---

## Troubleshooting

### Issue: Chat won't scroll
**Fix:** Hard refresh browser (Ctrl+Shift+R)

### Issue: Input not auto-focusing
**Fix:** Check browser console for errors

### Issue: Animations not smooth
**Fix:** Check if GPU acceleration is enabled in browser

### Issue: WebSocket not connecting
**Fix:** Ensure backend is running on port 8000

### Issue: Build fails
**Fix:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

---

## Success Criteria ✅

All tests should pass with:
- **No blocking bugs** - User can complete all chat workflows
- **Smooth UX** - Animations at 60fps, no janky scrolling
- **Professional feel** - Matches quality of Claude Desktop
- **No errors** - Console clean, build succeeds
- **Responsive** - Works on mobile and desktop
---
`moon.bat install`  ← one time only (or after pulling new deps)

`moon.bat run` ← starts both services (auto-installs if needed)

`moon.bat reload` ← restart everything

`moon.bat stop`  ← kill both services

---

**🎉 When all tests pass, the chat UI is production-ready!**
