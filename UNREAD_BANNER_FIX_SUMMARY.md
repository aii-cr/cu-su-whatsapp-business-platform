# Unread Messages Banner Persistence Fix - Implementation Summary

## Problem Fixed

The unread message banner in the chat interface was disappearing immediately after the backend marked messages as read, instead of persisting until the agent sends a reply or reloads the page. This was not the desired WhatsApp-like behavior.

## Root Cause

The frontend was conflating two different concepts:
1. **Database read status** - Whether messages are marked as read in the database
2. **Banner visibility** - Whether the banner should be shown to the agent

When the agent viewed a conversation, messages were marked as read in the database (which is correct), but this immediately caused the banner to disappear.

## Solution Implemented

### 1. Separated Banner Logic from Database Read Status

**Key Changes in `frontend/src/features/conversations/hooks/useUnreadMessages.ts`:**

- Added a new state `bannerUnreadCount` to track unread messages specifically for banner display
- Added `hasRepliedToUnread` state to track if the agent has replied to unread messages
- The banner visibility is now controlled by `bannerUnreadCount > 0 && !hasRepliedToUnread`

### 2. Updated Banner Visibility Logic

**Before:**
```typescript
const shouldShowBanner = count > 0 && !hasMarkedAsRead && !isCurrentlyViewing;
```

**After:**
```typescript
const shouldShowBanner = bannerUnreadCount > 0 && !hasRepliedToUnread;
```

### 3. Banner Count Management

- **Increment on new inbound messages:** When a new inbound message arrives, increment `bannerUnreadCount`
- **Reset on agent reply:** When the agent sends an outbound message, reset `bannerUnreadCount` to 0 and set `hasRepliedToUnread` to true
- **Initialize on conversation load:** Set initial `bannerUnreadCount` based on existing unread messages
- **Reset on page reload:** All state resets when conversation changes (simulating page reload)

### 4. WebSocket Message Handling

**New inbound messages:**
```typescript
// Increment banner unread count for new inbound messages
setBannerUnreadCount(prev => prev + 1);
```

**Agent replies:**
```typescript
// If it's an outbound message from agent (reply), hide the banner
if (message.message?.direction === 'outbound' && message.message?.sender_role === 'agent') {
  console.log('📤 [UNREAD] Agent sent a reply, hiding banner');
  setHasRepliedToUnread(true);
  setBannerUnreadCount(0); // Reset banner unread count
  setIsVisible(false);
}
```

**Messages read confirmation (backend update):**
```typescript
// Note: We do NOT reset bannerUnreadCount or hide banner here
// Banner should only be hidden when agent replies or page reloads
console.log('📊 [UNREAD] Messages marked as read in backend, but banner remains visible until agent replies');
```

### 5. Updated Conversation Page

**Changes in `frontend/src/app/(dashboard)/conversations/[id]/page.tsx`:**

- Updated to use `bannerUnreadCount` instead of `unreadCount` for banner display
- Added debugging information to show both counts
- Updated inline unread markers to use `bannerUnreadCount`

```typescript
// Use bannerUnreadCount for banner display
<UnreadMessagesBanner
  unreadCount={bannerUnreadCount}
  onScrollToUnread={scrollToUnread}
  isVisible={isUnreadBannerVisible}
/>
```

## How It Works Now

### 1. Agent Not Viewing Conversation
- Customer sends message → `bannerUnreadCount` increments
- Banner shows with correct count
- Messages remain unread in database

### 2. Agent Views Conversation
- Agent subscribes to conversation
- Messages are marked as read in database (backend behavior unchanged)
- **Banner remains visible** because `bannerUnreadCount` is still > 0
- `hasRepliedToUnread` is still false

### 3. Agent Sends Reply
- Agent sends outbound message
- `bannerUnreadCount` resets to 0
- `hasRepliedToUnread` set to true
- Banner disappears

### 4. Page Reload (or Conversation Change)
- All state resets
- If there are still unread messages, banner will show again
- This provides the second condition for hiding the banner

## Debugging

The implementation includes comprehensive debug information in development mode:
- Shows both database unread count and banner unread count
- Displays banner visibility state and reply status
- Logs all banner-related events with clear emojis for easy identification

## Benefits

1. **WhatsApp-like Behavior:** Banner persists until agent replies, just like WhatsApp
2. **Backward Compatible:** Database read status behavior unchanged
3. **Real-time Updates:** WebSocket integration maintained
4. **Debugging Support:** Added comprehensive logging and debug information
5. **Clean Separation:** Clear separation between database state and UI state

## Files Modified

### Frontend
- `frontend/src/features/conversations/hooks/useUnreadMessages.ts` - Core logic fix
- `frontend/src/app/(dashboard)/conversations/[id]/page.tsx` - Updated to use new banner count

The banner now behaves exactly like WhatsApp: it remains visible when the agent views the conversation but only disappears when they send a reply or reload the page.
