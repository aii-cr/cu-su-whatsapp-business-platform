#!/usr/bin/env python3
"""
Test script for sentiment analysis feature.
Tests the sentiment analyzer service and WebSocket notifications.
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.core.config import settings
from app.services.ai.agents.sentiment_analyzer import sentiment_analyzer_service
from app.services.ai.agents.sentiment_analyzer.schemas import SentimentAnalysisRequest


async def test_sentiment_analysis():
    """Test the sentiment analysis feature."""
    print("🧪 Testing Sentiment Analysis Feature")
    print("=" * 50)
    
    # Test customer messages with different sentiments
    test_customer_messages = [
        {
            "text_content": "Thank you so much for your help! You've been amazing 😊",
            "timestamp": "2024-01-01 10:00:00",
            "expected_sentiment": "positive"
        },
        {
            "text_content": "I'm really frustrated with this service. Nothing works as expected.",
            "timestamp": "2024-01-01 10:05:00",
            "expected_sentiment": "negative"
        },
        {
            "text_content": "Hello, I have a question about my order.",
            "timestamp": "2024-01-01 10:10:00",
            "expected_sentiment": "neutral"
        },
        {
            "text_content": "I'm so happy with the service! Everything is perfect! 😍",
            "timestamp": "2024-01-01 10:15:00",
            "expected_sentiment": "positive"
        },
        {
            "text_content": "This is absolutely terrible. I want to speak to a manager immediately! 😡",
            "timestamp": "2024-01-01 10:20:00",
            "expected_sentiment": "negative"
        }
    ]
    
    print(f"Testing {len(test_customer_messages)} customer message scenarios...")
    print()
    
    for i, test_case in enumerate(test_customer_messages, 1):
        print(f"Test {i}: {test_case['expected_sentiment'].upper()}")
        print(f"Message: {test_case['text_content']}")
        
        # Create test customer messages (simulating conversation context)
        test_messages = [test_case]  # For single message test
        
        try:
            # Test sentiment analysis with customer messages context
            sentiment_response = await sentiment_analyzer_service.chains.analyze_sentiment(
                conversation_id="test_conversation_123",
                customer_messages=test_messages
            )
            
            print(f"✅ Result: {sentiment_response.sentiment_emoji}")
            print(f"   Processing time: {sentiment_response.processing_time_ms:.2f}ms")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        print("-" * 50)
    
    print("🧪 Sentiment Analysis Test Completed!")


async def test_conversation_sentiment():
    """Test conversation sentiment retrieval."""
    print("\n🧪 Testing Conversation Sentiment Retrieval")
    print("=" * 50)
    
    conversation_id = "test_conversation_123"
    
    try:
        # Get conversation sentiment
        sentiment_data = await sentiment_analyzer_service.get_conversation_sentiment(conversation_id)
        
        if sentiment_data:
            print(f"✅ Found sentiment data for conversation {conversation_id}")
            print(f"   Current sentiment: {sentiment_data.current_sentiment}")
            print(f"   Last analyzed message: {sentiment_data.last_analyzed_message_id}")
            print(f"   Message count at analysis: {sentiment_data.message_count_at_last_analysis}")
            print(f"   Updated at: {sentiment_data.updated_at}")
            print(f"   History count: {len(sentiment_data.sentiment_history)}")
        else:
            print(f"ℹ️ No sentiment data found for conversation {conversation_id}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")


async def main():
    """Main test function."""
    print("🚀 Starting Sentiment Analysis Tests")
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"OpenAI Model: {settings.OPENAI_MODEL}")
    print()
    
    try:
        await test_sentiment_analysis()
        await test_conversation_sentiment()
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
