"""
Test script for email integration functionality.
"""

import asyncio
import json
import pytest
from unittest.mock import Mock, patch
from app.services.ai.agents.whatsapp_agent.tools.emailer import (
    send_confirmation_email,
    send_confirmation_email_with_auto_number,
    generate_confirmation_number,
    validate_email,
    validate_date_format,
    validate_time_slot,
)
from app.services.ai.agents.whatsapp_agent.services.email_client import EmailClient

class TestEmailValidation:
    """Test email validation functions."""
    
    def test_validate_email_valid(self):
        """Test valid email addresses."""
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "user+tag@example.org",
            "123@test.com"
        ]
        for email in valid_emails:
            assert validate_email(email) == True
    
    def test_validate_email_invalid(self):
        """Test invalid email addresses."""
        invalid_emails = [
            "invalid-email",
            "@example.com",
            "user@",
            "user@.com",
            "user..name@example.com"
        ]
        for email in invalid_emails:
            assert validate_email(email) == False
    
    def test_validate_date_format_valid(self):
        """Test valid date formats."""
        valid_dates = [
            "2024-02-15",
            "2024-12-31",
            "2025-01-01"
        ]
        for date in valid_dates:
            assert validate_date_format(date) == True
    
    def test_validate_date_format_invalid(self):
        """Test invalid date formats."""
        invalid_dates = [
            "2024/02/15",
            "15-02-2024",
            "2024-2-15",
            "2024-02-5",
            "invalid-date"
        ]
        for date in invalid_dates:
            assert validate_date_format(date) == False
    
    def test_validate_time_slot_valid(self):
        """Test valid time slots."""
        assert validate_time_slot("08:00") == True
        assert validate_time_slot("13:00") == True
    
    def test_validate_time_slot_invalid(self):
        """Test invalid time slots."""
        invalid_slots = [
            "09:00",
            "14:00",
            "8:00",
            "13:30",
            "invalid-time"
        ]
        for slot in invalid_slots:
            assert validate_time_slot(slot) == False

class TestEmailClient:
    """Test EmailClient functionality."""
    
    def test_generate_confirmation_number(self):
        """Test confirmation number generation."""
        client = EmailClient()
        confirmation_number = client.generate_confirmation_number()
        
        # Check format: ADN-XXXX-XXXX
        assert confirmation_number.startswith("ADN-")
        assert len(confirmation_number) == 12  # ADN-XXXX-XXXX
        assert confirmation_number.count("-") == 2
        
        # Generate another to ensure uniqueness
        confirmation_number2 = client.generate_confirmation_number()
        assert confirmation_number != confirmation_number2

@pytest.mark.asyncio
class TestEmailTools:
    """Test email tools functionality."""
    
    @patch('app.services.ai.agents.whatsapp_agent.services.email_client.email_client')
    async def test_generate_confirmation_number_tool(self, mock_email_client):
        """Test generate_confirmation_number tool."""
        # Mock the email client
        mock_email_client.generate_confirmation_number.return_value = "ADN-TEST-1234"
        
        result = await generate_confirmation_number.ainvoke({})
        result_dict = json.loads(result)
        
        assert result_dict["ok"] == True
        assert result_dict["confirmation_number"] == "ADN-TEST-1234"
    
    @patch('app.services.ai.agents.whatsapp_agent.services.email_client.email_client')
    async def test_send_confirmation_email_success(self, mock_email_client):
        """Test successful email sending."""
        # Mock the email client
        mock_email_client.send.return_value = True
        
        result = await send_confirmation_email.ainvoke({
            "email": "test@example.com",
            "full_name": "Test User",
            "plan_name": "Premium Plan",
            "iptv_count": 2,
            "telefonia": True,
            "date": "2024-02-15",
            "time_slot": "08:00",
            "confirmation_number": "ADN-TEST-1234"
        })
        
        result_dict = json.loads(result)
        assert result_dict["ok"] == True
        assert "successfully" in result_dict["message"]
        assert result_dict["confirmation_number"] == "ADN-TEST-1234"
    
    @patch('app.services.ai.agents.whatsapp_agent.services.email_client.email_client')
    async def test_send_confirmation_email_failure(self, mock_email_client):
        """Test email sending failure."""
        # Mock the email client to return False
        mock_email_client.send.return_value = False
        
        result = await send_confirmation_email.ainvoke({
            "email": "test@example.com",
            "full_name": "Test User",
            "plan_name": "Premium Plan",
            "iptv_count": 2,
            "telefonia": True,
            "date": "2024-02-15",
            "time_slot": "08:00",
            "confirmation_number": "ADN-TEST-1234"
        })
        
        result_dict = json.loads(result)
        assert result_dict["ok"] == False
        assert "Failed to send email" in result_dict["error"]
    
    async def test_send_confirmation_email_invalid_email(self):
        """Test email sending with invalid email."""
        result = await send_confirmation_email.ainvoke({
            "email": "invalid-email",
            "full_name": "Test User",
            "plan_name": "Premium Plan",
            "iptv_count": 2,
            "telefonia": True,
            "date": "2024-02-15",
            "time_slot": "08:00",
            "confirmation_number": "ADN-TEST-1234"
        })
        
        result_dict = json.loads(result)
        assert result_dict["ok"] == False
        assert "Invalid email format" in result_dict["error"]
    
    async def test_send_confirmation_email_invalid_date(self):
        """Test email sending with invalid date."""
        result = await send_confirmation_email.ainvoke({
            "email": "test@example.com",
            "full_name": "Test User",
            "plan_name": "Premium Plan",
            "iptv_count": 2,
            "telefonia": True,
            "date": "2024/02/15",  # Invalid format
            "time_slot": "08:00",
            "confirmation_number": "ADN-TEST-1234"
        })
        
        result_dict = json.loads(result)
        assert result_dict["ok"] == False
        assert "Invalid date format" in result_dict["error"]
    
    async def test_send_confirmation_email_invalid_time_slot(self):
        """Test email sending with invalid time slot."""
        result = await send_confirmation_email.ainvoke({
            "email": "test@example.com",
            "full_name": "Test User",
            "plan_name": "Premium Plan",
            "iptv_count": 2,
            "telefonia": True,
            "date": "2024-02-15",
            "time_slot": "09:00",  # Invalid time
            "confirmation_number": "ADN-TEST-1234"
        })
        
        result_dict = json.loads(result)
        assert result_dict["ok"] == False
        assert "Invalid time slot" in result_dict["error"]
    
    @patch('app.services.ai.agents.whatsapp_agent.services.email_client.email_client')
    async def test_send_confirmation_email_with_auto_number(self, mock_email_client):
        """Test email sending with auto-generated confirmation number."""
        # Mock the email client
        mock_email_client.generate_confirmation_number.return_value = "ADN-AUTO-5678"
        mock_email_client.send.return_value = True
        
        result = await send_confirmation_email_with_auto_number.ainvoke({
            "email": "test@example.com",
            "full_name": "Test User",
            "plan_name": "Premium Plan",
            "iptv_count": 2,
            "telefonia": True,
            "date": "2024-02-15",
            "time_slot": "08:00"
        })
        
        result_dict = json.loads(result)
        assert result_dict["ok"] == True
        assert result_dict["confirmation_number"] == "ADN-AUTO-5678"
        assert "auto-generated confirmation number" in result_dict["message"]

async def run_integration_test():
    """Run a simple integration test."""
    print("🧪 Running Email Integration Tests")
    print("=" * 50)
    
    # Test 1: Generate confirmation number
    print("\n1. Testing confirmation number generation...")
    result1 = await generate_confirmation_number.ainvoke({})
    print(f"Result: {result1}")
    
    # Test 2: Validate email format
    print("\n2. Testing email validation...")
    test_emails = ["test@example.com", "invalid-email", "user@domain.co.uk"]
    for email in test_emails:
        is_valid = validate_email(email)
        print(f"  {email}: {'✓' if is_valid else '✗'}")
    
    # Test 3: Validate date format
    print("\n3. Testing date validation...")
    test_dates = ["2024-02-15", "2024/02/15", "15-02-2024"]
    for date in test_dates:
        is_valid = validate_date_format(date)
        print(f"  {date}: {'✓' if is_valid else '✗'}")
    
    # Test 4: Validate time slots
    print("\n4. Testing time slot validation...")
    test_times = ["08:00", "13:00", "09:00", "14:00"]
    for time in test_times:
        is_valid = validate_time_slot(time)
        print(f"  {time}: {'✓' if is_valid else '✗'}")
    
    print("\n✅ Integration tests completed!")

if __name__ == "__main__":
    asyncio.run(run_integration_test())
