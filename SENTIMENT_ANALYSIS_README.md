# 😊 Sentiment Analysis Feature

## Overview

The Sentiment Analysis feature provides real-time emotional state analysis of customer messages in WhatsApp conversations. It uses LangChain and OpenAI to analyze message sentiment and displays appropriate emojis next to customer names in the conversation interface.

## Features

- **Real-time Analysis**: Analyzes customer messages as they arrive via webhooks
- **Smart Sampling**: Analyzes first message and every 3rd message thereafter
- **Full Context Analysis**: Uses ALL customer messages in conversation for accurate sentiment
- **Emoji Indicators**: Displays sentiment emojis next to customer names
- **Optimized Prompts**: LLM responds with only the emoji for efficiency
- **WebSocket Notifications**: Real-time updates to all conversation subscribers
- **Caching**: Efficient caching to reduce API calls and improve performance

## Available Sentiment Emojis

| Emoji | Sentiment | Description |
|-------|-----------|-------------|
| 😊 | Happy | Positive, satisfied, pleased, grateful |
| 😐 | Neutral | Indifferent, matter-of-fact, balanced |
| 😞 | Sad | Disappointed, upset, frustrated, unhappy |
| 😤 | Frustrated | Annoyed, irritated, impatient, but not angry |
| 😡 | Angry | Very upset, angry, hostile, aggressive |
| 🤔 | Thinking | Confused, uncertain, questioning, contemplating |
| 😌 | Calm | Relaxed, peaceful, content, satisfied |
| 😰 | Anxious | Worried, nervous, stressed, concerned |
| 😍 | Loving | Very happy, excited, enthusiastic, delighted |
| 😔 | Melancholy | Sad, wistful, nostalgic, resigned |

## Architecture

### Backend Components

```
app/services/ai/agents/sentiment_analyzer/
├── __init__.py                    # Module initialization
├── config.py                      # Configuration settings
├── schemas.py                     # Pydantic schemas
├── sentiment_service.py           # Main service
├── chains/
│   └── sentiment_chains.py        # LangChain chains
└── prompts/
    └── sentiment_analysis.md      # Analysis prompt template
```

### Frontend Components

- **ConversationHeader.tsx**: Displays sentiment emoji next to customer name
- **WebSocket Client**: Handles real-time sentiment updates
- **Conversation Model**: Updated to include sentiment fields

## Configuration

### Environment Variables

The sentiment analysis feature uses the following configuration from `app/services/ai/agents/sentiment_analyzer/config.py`:

```python
# Analysis Settings
analysis_interval_messages: int = 3        # Analyze every N messages
max_message_length: int = 1000            # Maximum message length
min_message_length: int = 5               # Minimum message length

# Model Configuration
model_name: str = "gpt-4o-mini"          # OpenAI model for analysis
temperature: float = 0.1                  # Analysis temperature
max_tokens: int = 50                      # Maximum response tokens

# Processing Settings
enable_async_processing: bool = True      # Background processing
cache_duration_minutes: int = 30          # Cache duration
max_retries: int = 2                      # Maximum retries
timeout_seconds: int = 10                 # Analysis timeout
```

### Database Collections

- **conversations**: Updated with sentiment fields
  - `current_sentiment_emoji`: Current sentiment emoji
  - `sentiment_confidence`: Confidence score (0-1)
  - `last_sentiment_analysis_at`: Last analysis timestamp

- **conversation_sentiments**: Dedicated sentiment collection
  - Stores sentiment history and analysis data
  - Indexed for efficient querying

## Usage

### Automatic Analysis

Sentiment analysis is automatically triggered when customer messages arrive via WhatsApp webhooks:

1. **Message Reception**: Customer message received via webhook
2. **Analysis Check**: System determines if analysis should be performed
3. **Context Loading**: All customer messages in conversation are loaded
4. **LangChain Processing**: Full conversation context analyzed for sentiment
5. **Database Update**: Sentiment data stored in both collections
6. **WebSocket Notification**: Real-time update sent to frontend
7. **UI Update**: Sentiment emoji displayed next to customer name

### Analysis Flow

- **First Message**: Always analyzed when customer starts conversation
- **Every 3rd Message**: Analyzed at message counts 3, 6, 9, 12, etc.
- **Full Context**: Each analysis considers ALL customer messages in the conversation

### Manual Analysis

You can manually trigger sentiment analysis via the service:

```python
from app.services import sentiment_analyzer_service

# Analyze a specific message
result = await sentiment_analyzer_service.analyze_message_sentiment(
    request=SentimentAnalysisRequest(
        conversation_id="conv_123",
        message_id="msg_456",
        message_text="Thank you for your help!",
        customer_phone="+1234567890",
        message_count=5,
        is_first_message=False
    )
)

# Update sentiment manually
success = await sentiment_analyzer_service.update_conversation_sentiment(
    conversation_id="conv_123",
    sentiment_emoji="😊",
    confidence=0.85,
    message_id="msg_456"
)
```

### Frontend Integration

The sentiment emoji is automatically displayed in the conversation header:

```tsx
// ConversationHeader.tsx
{conversation.current_sentiment_emoji && (
  <span 
    className="text-xl flex-shrink-0 cursor-default"
    title={`Sentiment: ${conversation.current_sentiment_emoji} (Confidence: ${(conversation.sentiment_confidence || 0) * 100:.0f}%)`}
  >
    {conversation.current_sentiment_emoji}
  </span>
)}
```

## WebSocket Events

### Sentiment Update Event

```typescript
interface SentimentUpdateEvent {
  type: "sentiment_update";
  conversation_id: string;
  sentiment_emoji: string;
  confidence: number;
  message_id: string;
  timestamp: string;
}
```

### Frontend Event Handling

```typescript
// Listen for sentiment updates
window.addEventListener('sentiment-update', (event) => {
  const { conversationId, sentimentEmoji, confidence } = event.detail;
  console.log(`Sentiment updated for ${conversationId}: ${sentimentEmoji}`);
});
```

## Performance Optimization

### Smart Sampling

- **Interval Analysis**: Only analyzes every 3rd message by default
- **First Message**: Always analyzes the first message in a conversation
- **Age-based Updates**: Re-analyzes if sentiment is older than 10 messages
- **Message Validation**: Skips very short or acknowledgment messages

### Caching

- **In-Memory Cache**: 30-minute cache for conversation sentiment data
- **Database Indexing**: Optimized indexes for sentiment queries
- **WebSocket Optimization**: Efficient real-time updates

### Cost Management

- **Token Limits**: Maximum 50 tokens per analysis response
- **Batch Processing**: Processes multiple messages efficiently
- **Timeout Protection**: 10-second timeout prevents hanging requests
- **Retry Logic**: Limited retries to prevent excessive API calls

## Testing

### Run the Test Script

```bash
# Activate virtual environment
source .venv/bin/activate

# Run sentiment analysis tests
python test_sentiment_analysis.py
```

### Test Coverage

The test script validates:
- ✅ Sentiment analysis accuracy
- ✅ Confidence scoring
- ✅ Language detection
- ✅ Processing time optimization
- ✅ Conversation sentiment retrieval
- ✅ Error handling

## Monitoring

### Logs

Sentiment analysis activities are logged with emoji prefixes:

```
😊 [SENTIMENT] Triggering sentiment analysis for conversation 123
✅ [SENTIMENT] Sentiment analysis completed: 😊 (confidence: 0.85)
🔔 [WS] Broadcasted sentiment update for conversation 123: 😊 (confidence: 0.85)
```

### Metrics

Key metrics to monitor:
- **Analysis Success Rate**: Percentage of successful analyses
- **Average Processing Time**: Time taken for sentiment analysis
- **Confidence Distribution**: Distribution of confidence scores
- **API Usage**: OpenAI API calls and token consumption
- **Cache Hit Rate**: Effectiveness of sentiment caching

## Troubleshooting

### Common Issues

1. **Analysis Skipped**
   - Check if message meets minimum length requirements
   - Verify analysis interval configuration
   - Ensure sentiment analysis is enabled

2. **Low Confidence Scores**
   - Review message content for clarity
   - Check language detection accuracy
   - Consider adjusting model temperature

3. **WebSocket Notifications Not Received**
   - Verify WebSocket connection status
   - Check conversation subscription
   - Review browser console for errors

### Debug Commands

```python
# Check sentiment configuration
from app.services.ai.agents.sentiment_analyzer.config import sentiment_config
print(sentiment_config.dict())

# Test sentiment analysis directly
from app.services import sentiment_analyzer_service
result = await sentiment_analyzer_service.analyze_message_sentiment(request)
print(result.dict())
```

## Future Enhancements

### Planned Features

- **Sentiment Trends**: Track sentiment changes over time
- **Agent Alerts**: Notify agents of negative sentiment
- **Response Suggestions**: Suggest responses based on sentiment
- **Multi-modal Analysis**: Analyze images and voice messages
- **Custom Emojis**: Allow custom sentiment emoji sets
- **Sentiment Analytics**: Dashboard for sentiment insights

### Integration Opportunities

- **CRM Integration**: Sync sentiment with customer profiles
- **Escalation Rules**: Auto-escalate based on sentiment
- **Quality Metrics**: Include sentiment in conversation quality scores
- **Training Data**: Use sentiment data for AI model training

## Contributing

When contributing to the sentiment analysis feature:

1. **Follow LangChain Best Practices**: Use structured output and proper error handling
2. **Test Thoroughly**: Run the test script and verify WebSocket functionality
3. **Update Documentation**: Keep this README current with any changes
4. **Monitor Performance**: Ensure changes don't impact analysis speed or accuracy
5. **Consider Costs**: Be mindful of OpenAI API usage and token consumption

## Support

For issues or questions about the sentiment analysis feature:

1. Check the logs for error messages
2. Run the test script to verify functionality
3. Review the configuration settings
4. Check WebSocket connection status
5. Consult the troubleshooting section above
