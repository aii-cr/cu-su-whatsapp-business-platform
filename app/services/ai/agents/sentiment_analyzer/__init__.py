"""
Sentiment analyzer agent for WhatsApp conversations.
Analyzes customer messages and provides sentiment emoji indicators.
"""

from .sentiment_service import SentimentAnalyzerService

# Global service instance
sentiment_analyzer_service = SentimentAnalyzerService()

__all__ = ["sentiment_analyzer_service", "SentimentAnalyzerService"]
