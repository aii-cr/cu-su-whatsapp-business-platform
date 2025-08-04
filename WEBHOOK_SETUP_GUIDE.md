# WhatsApp Webhook Setup Guide

## Current Issue: Invalid Webhook Signature

The logs show `Invalid webhook signature` errors. This is because the `WHATSAPP_APP_SECRET` is not properly configured.

## Step-by-Step Fix

### 1. Get Your Meta App Secret

1. Go to [Meta Developer Console](https://developers.facebook.com/apps/)
2. Select your WhatsApp Business app
3. Go to **Settings** > **Basic**
4. Copy the **App Secret** (not the App ID)

### 2. Update Your Environment Variables

Add this to your `.env` file:

```env
# Replace with your actual Meta App Secret
WHATSAPP_APP_SECRET="your-actual-app-secret-here"
```

**Important**: The current value `"development-app-secret"` is a placeholder and won't work with real webhooks.

### 3. Update Webhook URL

Make sure your webhook URL points to your ngrok URL:

```env
# Update this to your ngrok URL
WHATSAPP_WEBHOOK_URL="https://your-ngrok-url.ngrok.io/api/v1/whatsapp"
```

### 4. Configure Webhook in Meta Developer Console

1. Go to your app's **WhatsApp** > **Configuration**
2. Set **Callback URL**: `https://your-ngrok-url.ngrok.io/api/v1/whatsapp/webhook`
3. Set **Verify Token**: Same as your `WHATSAPP_VERIFY_TOKEN`
4. Click **Verify and Save**
5. Go to **Manage** and subscribe to:
   - ✅ `messages` (already done)
   - 🔄 `message_echoes` (recommended)

### 5. Test the Webhook

1. Restart your backend server
2. Send a message from your personal WhatsApp to your business number
3. Check the logs - you should see successful webhook processing

## WebSocket Integration

The backend now includes WebSocket support for real-time updates:

### WebSocket Endpoints

- **Connect**: `ws://localhost:8000/api/v1/ws/chat/{user_id}`
- **Status**: `GET /api/v1/ws/status/{user_id}`
- **Stats**: `GET /api/v1/ws/stats`

### Frontend Integration

```javascript
// Connect to WebSocket
const ws = new WebSocket(`ws://localhost:8000/api/v1/ws/chat/${userId}`);

// Subscribe to a conversation
ws.send(JSON.stringify({
  type: "subscribe_conversation",
  conversation_id: "conversation_id_here"
}));

// Listen for new messages
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === "new_message") {
    // Handle new message
    console.log("New message:", data.message);
  }
};
```

## Message Flow

1. **Customer sends message** → WhatsApp → Your webhook
2. **Webhook processes message** → Saves to database → Notifies via WebSocket
3. **Frontend receives notification** → Updates UI in real-time
4. **Agent responds** → API call → WhatsApp → WebSocket notification
5. **Frontend updates** → Shows sent message immediately

## Troubleshooting

### Webhook Still Failing?

1. **Check App Secret**: Ensure `WHATSAPP_APP_SECRET` is correct
2. **Check ngrok URL**: Make sure it's accessible and matches your webhook URL
3. **Check Meta Console**: Verify webhook is properly configured
4. **Check Logs**: Look for specific error messages

### WebSocket Not Working?

1. **Check Connection**: Ensure WebSocket endpoint is accessible
2. **Check User ID**: Make sure user_id is valid
3. **Check Subscriptions**: Verify conversation subscriptions

## Security Notes

- **Development Mode**: Webhook signature verification is bypassed if app secret is not properly configured
- **Production**: Always use proper app secret for signature verification
- **HTTPS**: Use HTTPS in production for webhook URLs

## Next Steps

1. ✅ Fix webhook signature verification
2. ✅ Test incoming messages
3. ✅ Test WebSocket notifications
4. ✅ Integrate with frontend
5. ✅ Test end-to-end messaging flow

## API Endpoints Summary

### Webhook
- `GET /api/v1/whatsapp/webhook` - Webhook verification
- `POST /api/v1/whatsapp/webhook` - Webhook processing
- `GET /api/v1/whatsapp/webhook/test` - Webhook test

### WebSocket
- `WS /api/v1/ws/chat/{user_id}` - WebSocket connection
- `GET /api/v1/ws/status/{user_id}` - Connection status
- `GET /api/v1/ws/stats` - WebSocket statistics

### Messages
- `POST /api/v1/messages/send` - Send message
- `GET /api/v1/conversations/{id}/messages` - Get messages

This setup provides a complete real-time messaging system with proper webhook handling and WebSocket notifications. 