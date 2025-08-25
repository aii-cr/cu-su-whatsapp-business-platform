# Email Integration for WhatsApp Agent

This document explains how to use the email integration features in the WhatsApp Business Platform backend.

## Overview

The email integration allows the AI agent to send confirmation emails to customers using the `EmailSender` service with SMTP configuration. The system provides three main tools:

1. **Generate Confirmation Number** - Creates unique booking confirmation numbers
2. **Send Confirmation Email** - Sends emails with a provided confirmation number
3. **Send Confirmation Email with Auto Number** - Sends emails with an automatically generated confirmation number

## Configuration

### Environment Variables

Make sure your `.env` file contains the following SMTP settings:

```env
# Email settings for payment/confirmation emails
SMTP_PAY_SERVER=your-smtp-server.com
SMTP_PAY_PORT=587
SMTP_PAY_USERNAME=your-email@domain.com
SMTP_PAY_PASSWORD=your-email-password
```

### Email Sender Configuration

The system uses the `EmailSender` class from `app/services/email/email_sender.py` with the following configuration:

- **SMTP Server**: Configured via `SMTP_PAY_SERVER`
- **Port**: Configured via `SMTP_PAY_PORT` (default: 587)
- **Authentication**: Username/password from config
- **Security**: TLS enabled by default
- **Custom Hostname**: Set to "mail.local" for compatibility

## Available Tools

### 1. `generate_confirmation_number`

Generates a unique confirmation number in the format `ADN-XXXX-XXXX`.

**Usage:**
```python
from app.services.ai.agents.whatsapp_agent.tools.emailer import generate_confirmation_number

result = await generate_confirmation_number.ainvoke({})
# Returns: {"ok": true, "confirmation_number": "ADN-A1B2-C3D4"}
```

### 2. `send_confirmation_email`

Sends a confirmation email with a provided confirmation number.

**Parameters:**
- `email` (str): Destination email address
- `full_name` (str): Customer full name
- `plan_name` (str): Plan name
- `iptv_count` (int): Number of IPTV devices
- `telefonia` (bool): Has VoIP phone service
- `date` (str): Installation date (YYYY-MM-DD format)
- `time_slot` (str): Installation time (08:00 or 13:00)
- `confirmation_number` (str): Booking confirmation number

**Usage:**
```python
from app.services.ai.agents.whatsapp_agent.tools.emailer import send_confirmation_email

result = await send_confirmation_email.ainvoke({
    "email": "customer@example.com",
    "full_name": "John Smith",
    "plan_name": "Premium Plan",
    "iptv_count": 2,
    "telefonia": True,
    "date": "2024-02-15",
    "time_slot": "08:00",
    "confirmation_number": "ADN-A1B2-C3D4"
})
```

### 3. `send_confirmation_email_with_auto_number`

Sends a confirmation email with an automatically generated confirmation number.

**Parameters:**
- `email` (str): Destination email address
- `full_name` (str): Customer full name
- `plan_name` (str): Plan name
- `iptv_count` (int): Number of IPTV devices
- `telefonia` (bool): Has VoIP phone service
- `date` (str): Installation date (YYYY-MM-DD format)
- `time_slot` (str): Installation time (08:00 or 13:00)

**Usage:**
```python
from app.services.ai.agents.whatsapp_agent.tools.emailer import send_confirmation_email_with_auto_number

result = await send_confirmation_email_with_auto_number.ainvoke({
    "email": "customer@example.com",
    "full_name": "John Smith",
    "plan_name": "Premium Plan",
    "iptv_count": 2,
    "telefonia": True,
    "date": "2024-02-15",
    "time_slot": "08:00"
})
```

## Email Template

The confirmation email uses the following template:

```
Hi {full_name},

Your American Data Networks installation is confirmed.

Service:
- Plan: {plan_name}
- IPTV devices: {iptv_count}
- VoIP Phone: {telefonia}

Installation:
- Date: {date}
- Time: {time_slot}

Billing:
- First month pre-charge on installation day.
- Installation cost: $0
- Second month: FREE

Confirmation Number: {confirmation_number}

If you need any changes, just reply to this message.
Thanks for choosing American Data Networks!
```

## Integration with LangChain Agent

### Adding Tools to Agent

```python
from langchain.agents import AgentExecutor, create_openai_tools_agent
from app.services.ai.agents.whatsapp_agent.tools.emailer import (
    send_confirmation_email,
    send_confirmation_email_with_auto_number,
    generate_confirmation_number,
)

# Define tools
tools = [
    send_confirmation_email,
    send_confirmation_email_with_auto_number,
    generate_confirmation_number,
]

# Create agent
agent = create_openai_tools_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
```

### Example Agent Prompt

```python
prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a helpful customer service agent for American Data Networks (ADN).
    
Your role is to help customers with their installation bookings and send confirmation emails.

When a customer provides their information for installation, you should:
1. Collect all necessary information (email, name, plan, IPTV count, phone service, date, time)
2. Generate a confirmation number
3. Send a confirmation email with all the details

Available tools:
- generate_confirmation_number: Generate a unique confirmation number
- send_confirmation_email: Send confirmation email with provided confirmation number
- send_confirmation_email_with_auto_number: Send confirmation email with auto-generated confirmation number

Always validate the information before sending emails. Return clear, helpful responses to customers.
"""),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])
```

## Error Handling

The tools include comprehensive error handling:

- **Email Validation**: Checks for valid email format
- **Date Validation**: Ensures YYYY-MM-DD format
- **Time Slot Validation**: Only allows 08:00 or 13:00
- **Input Validation**: Checks for empty or invalid values
- **SMTP Error Handling**: Catches and logs SMTP errors

All tools return JSON responses with:
- `ok`: Boolean indicating success/failure
- `message`: Success message (if ok=true)
- `error`: Error message (if ok=false)
- `confirmation_number`: Generated confirmation number (if applicable)

## Testing

Run the example script to test the email integration:

```bash
# Activate virtual environment
source .venv/bin/activate

# Run the example
python examples/email_integration_example.py
```

## Troubleshooting

### Common Issues

1. **SMTP Connection Failed**
   - Check SMTP server and port settings
   - Verify username and password
   - Ensure firewall allows SMTP traffic

2. **Authentication Failed**
   - Verify email credentials
   - Check if 2FA is enabled (may need app password)
   - Ensure account allows SMTP access

3. **Email Not Received**
   - Check spam/junk folder
   - Verify recipient email address
   - Check SMTP server logs

### Debugging

Enable debug logging by setting `LOG_LEVEL=DEBUG` in your `.env` file:

```env
LOG_LEVEL=DEBUG
```

The system logs all email operations with detailed information for troubleshooting.

## Security Considerations

- Store SMTP credentials securely in environment variables
- Use TLS/SSL for email transmission
- Validate all email addresses before sending
- Implement rate limiting for email sending
- Monitor email sending logs for suspicious activity
