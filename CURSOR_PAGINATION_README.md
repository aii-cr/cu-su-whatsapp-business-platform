# Cursor-Based Message Pagination

This document describes the implementation of cursor-based pagination for chat messages with infinite scroll support.

## Overview

The cursor-based pagination system provides efficient message loading for chat interfaces with the following features:

- **Cursor-based pagination**: Uses ObjectId as cursor for consistent performance
- **Redis caching**: Caches latest messages for sub-second response times
- **Infinite scroll**: Smooth loading of older messages without page jumps
- **Bottom anchoring**: Messages appear anchored to the bottom without scroll jumps
- **Real-time updates**: WebSocket integration for new messages

## Architecture

### Backend Components

#### 1. API Endpoints

- `GET /messages` - Cursor-based pagination for messages
- `GET /messages/around` - Load messages around a specific message ID

#### 2. Services

- `CursorMessageService` - Handles cursor-based pagination logic
- `RedisService` - Manages message caching
- `WebSocketService` - Invalidates cache on new messages

#### 3. Database

- Index: `{ conversation_id: 1, _id: -1 }` for efficient cursor queries
- Query pattern: `{ conversation_id: ObjectId, _id: { $lt: cursor } }`

### Frontend Components

#### 1. API Client

- `MessagesApi.getMessagesCursor()` - Cursor-based message fetching
- `MessagesApi.getMessagesAround()` - Context loading around messages

#### 2. React Hooks

- `useMessages()` - Infinite query with cursor pagination
- Query key: `messageQueryKeys.conversationMessages(conversationId)`

#### 3. Components

- `VirtualizedMessageList` - React Virtuoso-based message list
- `MessageList` - Wrapper component for backward compatibility

## API Contract

### GET /messages

**Query Parameters:**
- `chatId` (required): Conversation ID
- `limit` (optional): Number of messages (1-100, default: 50)
- `before` (optional): Cursor for pagination (ObjectId)

**Response:**
```json
{
  "messages": [
    {
      "_id": "507f1f77bcf86cd799439011",
      "conversation_id": "507f1f77bcf86cd799439012",
      "text_content": "Hello world",
      "direction": "inbound",
      "sender_role": "customer",
      "timestamp": "2024-01-01T12:00:00Z"
    }
  ],
  "next_cursor": "507f1f77bcf86cd799439010",
  "has_more": true,
  "anchor": "desc",
  "cache_hit": false
}
```

### GET /messages/around

**Query Parameters:**
- `chatId` (required): Conversation ID
- `anchorId` (required): Message ID to center around
- `limit` (optional): Number of messages (1-50, default: 25)

**Response:** Same as `/messages` endpoint

## Caching Strategy

### Redis Cache Keys

- Pattern: `messages:last:{conversation_id}:{limit}`
- TTL: 60 seconds
- Only caches latest messages (no `before` cursor)

### Cache Invalidation

- Automatic invalidation when new messages are inserted
- WebSocket service triggers cache invalidation
- Pattern: `messages:last:{conversation_id}:*`

### Cache Headers

- `Cache-Control: private, max-age=30, must-revalidate`
- `ETag` for cache validation

## Frontend Implementation

### Infinite Scroll

```typescript
const query = useInfiniteQuery({
  queryKey: messageQueryKeys.conversationMessages(conversationId),
  queryFn: ({ pageParam }) => MessagesApi.getMessagesCursor(
    conversationId, 
    50, 
    pageParam as string | undefined
  ),
  getNextPageParam: (lastPage) => lastPage.has_more ? lastPage.next_cursor : undefined,
  initialPageParam: undefined
});
```

### Virtualized List

```typescript
<Virtuoso
  data={sortedMessages}
  itemContent={(index, message) => (
    <MessageBubble message={message} isOwn={message.direction === 'outbound'} />
  )}
  startReached={loadOlderMessages}
  followOutput="auto"
  alignToBottom
  initialTopMostItemIndex={sortedMessages.length - 1}
/>
```

## Performance Optimizations

### Database

1. **Compound Index**: `{ conversation_id: 1, _id: -1 }`
2. **Cursor Queries**: No `skip/limit`, uses `$lt` with ObjectId
3. **Projection**: Only fetch required fields

### Caching

1. **Redis TTL**: 60 seconds for freshness
2. **Cache Keys**: Only latest messages (no pagination cache)
3. **ETags**: For cache validation

### Frontend

1. **Virtualization**: React Virtuoso for large lists
2. **Infinite Query**: TanStack Query for caching
3. **Bottom Anchoring**: No scroll jumps on load

## Error Handling

### Backend Errors

- `INVALID_CURSOR`: Malformed cursor parameter
- `INVALID_ID`: Invalid conversation or message ID
- `CONVERSATION_ACCESS_DENIED`: Permission check failed

### Frontend Errors

- Network errors with retry logic
- Cache miss fallback to database
- Graceful degradation for large lists

## Testing

### Unit Tests

```bash
pytest tests/test_messages_cursor_pagination.py
```

### Test Coverage

- Cursor pagination logic
- Cache hit/miss scenarios
- Error handling
- Integration with WebSocket

## Migration

### Database Index

The required index is automatically created:

```javascript
db.messages.createIndex(
  { "conversation_id": 1, "_id": -1 }, 
  { "name": "idx_messages_conversation_id_desc" }
)
```

### Environment Variables

No new environment variables required. Uses existing Redis configuration.

## Monitoring

### Metrics

- Cache hit rate
- Response times
- Error rates
- Memory usage

### Logging

- Cache operations with emojis
- Pagination requests
- Error details with correlation IDs

## Troubleshooting

### Common Issues

1. **Slow pagination**: Check database index exists
2. **Cache misses**: Verify Redis connection
3. **Scroll jumps**: Check virtualization setup
4. **Memory leaks**: Monitor React Virtuoso usage

### Debug Commands

```bash
# Check Redis cache
redis-cli keys "messages:last:*"

# Check database index
db.messages.getIndexes()

# Monitor API requests
tail -f logs/app.log | grep "GET_MESSAGES_CURSOR"
```

## Future Enhancements

1. **Compression**: Gzip/Brotli for large responses
2. **Rate limiting**: Per-user pagination limits
3. **Search**: Full-text search with cursors
4. **Analytics**: Message view tracking
