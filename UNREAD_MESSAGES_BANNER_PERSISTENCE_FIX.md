# Unread Messages Banner Persistence Fix

## Problem Description

The chat interface was showing a banner for unread messages, similar to WhatsApp, but it had a bug. When an agent was not actively viewing the chat (not subscribed to the websocket for real-time messages or on a different page) and the customer sent a new message, the agent should see a banner above the new messages with the count of unread messages (e.g., "1 unread message") when they return to the chat.

**The Issue:** The banner appeared but only for a fraction of a second because as soon as the frontend detected the agent had viewed the messages, it sent a "mark as read" signal through the websocket to the backend. This backend update triggered the banner to disappear immediately, which was not the desired behavior.

**Desired Behavior:** The banner should remain visible until either:
1. The agent sends a reply to the unread messages, or
2. The agent reloads the page

## Root Cause Analysis

The problem was in the frontend logic in `useUnreadMessages` hook. The banner visibility was directly tied to the database read status of messages. When messages were marked as read in the database (which happens when the agent views the conversation), the `calculateUnreadCount` function would return 0, causing the banner to disappear immediately.

The issue was that the frontend was conflating two different concepts:
1. **Database read status** - Whether messages are marked as read in the database
2. **Banner visibility** - Whether the banner should be shown to the agent

## Solution Implemented

### 1. Separated Banner Logic from Database Read Status

**Key Changes in `frontend/src/features/conversations/hooks/useUnreadMessages.ts`:**

- Added a new state `bannerUnreadCount` to track unread messages specifically for banner display
- This count persists independently of the database read status
- The banner visibility is now controlled by `bannerUnreadCount > 0 && !hasRepliedToUnread`

```typescript
const [bannerUnreadCount, setBannerUnreadCount] = useState(0); // Separate count for banner display
```

### 2. Updated Banner Visibility Logic

**Before:**
```typescript
const shouldShowBanner = count > 0 && !hasRepliedToUnread;
```

**After:**
```typescript
const shouldShowBanner = bannerUnreadCount > 0 && !hasRepliedToUnread;
```

### 3. Banner Count Management

- **Increment on new inbound messages:** When a new inbound message arrives, increment `bannerUnreadCount`
- **Reset on agent reply:** When the agent sends an outbound message, reset `bannerUnreadCount` to 0 and set `hasRepliedToUnread` to true
- **Initialize on conversation load:** Set initial `bannerUnreadCount` based on existing unread messages

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

### 5. Updated Conversation Page

**Changes in `frontend/src/app/(dashboard)/conversations/[id]/page.tsx`:**

- Updated to use `bannerUnreadCount` instead of `unreadCount` for banner display
- Added debugging information to show both counts
- Updated inline unread markers to use `bannerUnreadCount`

```typescript
// Unread messages management
const {
  unreadCount,
  isVisible: isUnreadBannerVisible,
  hasMarkedAsRead,
  isCurrentlyViewing,
  hasRepliedToUnread,
  bannerUnreadCount, // New field
  markMessagesAsRead
} = useUnreadMessages({...});

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

### 4. Page Reload
- All state resets
- If there are still unread messages, banner will show again
- This provides the second condition for hiding the banner

## Testing

Created comprehensive tests in `tests/test_unread_messages_banner_persistence.py`:

1. **`test_banner_remains_visible_after_viewing_messages`** - Core test for the fix
2. **`test_banner_hidden_after_agent_reply`** - Tests banner hiding on reply
3. **`test_banner_persistence_with_multiple_unread_messages`** - Tests with multiple messages
4. **`test_banner_behavior_with_new_messages_after_viewing`** - Tests new messages after viewing
5. **`test_banner_reset_on_page_reload`** - Tests page reload behavior

## Benefits

1. **WhatsApp-like Behavior:** Banner persists until agent replies, just like WhatsApp
2. **Backward Compatible:** Database read status behavior unchanged
3. **Real-time Updates:** WebSocket integration maintained
4. **Debugging Support:** Added comprehensive logging and debug information
5. **Test Coverage:** Comprehensive test suite for the new behavior

## Files Modified

### Frontend
- `frontend/src/features/conversations/hooks/useUnreadMessages.ts` - Core logic fix
- `frontend/src/app/(dashboard)/conversations/[id]/page.tsx` - Updated to use new banner count

### Tests
- `tests/test_unread_messages_banner_persistence.py` - New test suite

## Debug Information

The implementation includes comprehensive debug information in development mode:
- `Unread: X` - Database unread count
- `Banner Unread: Y` - Banner-specific unread count
- `Banner: Visible/Hidden` - Banner visibility state
- `Marked: Yes/No` - Whether messages are marked as read
- `WS: Connected/Disconnected` - WebSocket connection status
- `Viewing: Yes/No` - Whether agent is currently viewing
- `Replied: Yes/No` - Whether agent has replied to unread messages

## Conclusion

This fix successfully addresses the banner persistence issue by separating the banner display logic from the database read status. The banner now behaves exactly like WhatsApp - it remains visible until the agent sends a reply or reloads the page, while maintaining all existing functionality for message read status tracking and WebSocket integration.

The solution is robust, well-tested, and maintains backward compatibility with existing features.
