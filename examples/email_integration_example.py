"""
Example: Email Integration with WhatsApp Agent

This example demonstrates how to use the email tools in a LangChain agent
for sending confirmation emails to customers.
"""

import asyncio
import json
from typing import List
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from app.services.ai.agents.whatsapp_agent.tools.emailer import (
    send_confirmation_email,
    send_confirmation_email_with_auto_number,
    generate_confirmation_number,
)
from app.core.config import settings

# Set up the LLM
llm = ChatOpenAI(
    model=settings.OPENAI_MODEL,
    temperature=0,
    api_key=settings.OPENAI_API_KEY
)

# Define the tools
tools: List[BaseTool] = [
    send_confirmation_email,
    send_confirmation_email_with_auto_number,
    generate_confirmation_number,
]

# Create the prompt template
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

# Create the agent
agent = create_openai_tools_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

async def example_conversation():
    """Example conversation flow with email integration."""
    
    print("🤖 ADN Customer Service Agent")
    print("=" * 50)
    
    # Example 1: Customer provides complete information
    print("\n📧 Example 1: Complete customer information")
    print("-" * 40)
    
    response1 = await agent_executor.ainvoke({
        "input": "Hi, I want to book an installation. My name is John Smith, email is john.smith@example.com, I want the Premium plan with 2 IPTV devices and VoIP phone service. Can you install it on 2024-02-15 at 08:00?",
        "chat_history": []
    })
    
    print(f"Agent: {response1['output']}")
    
    # Example 2: Customer with incomplete information
    print("\n📧 Example 2: Incomplete information")
    print("-" * 40)
    
    response2 = await agent_executor.ainvoke({
        "input": "I need installation but I don't have a confirmation number. My email is jane.doe@example.com, name is Jane Doe, Basic plan, 1 IPTV device, no phone service, for 2024-02-20 at 13:00.",
        "chat_history": []
    })
    
    print(f"Agent: {response2['output']}")
    
    # Example 3: Just generate a confirmation number
    print("\n📧 Example 3: Generate confirmation number only")
    print("-" * 40)
    
    response3 = await agent_executor.ainvoke({
        "input": "Can you generate a confirmation number for me?",
        "chat_history": []
    })
    
    print(f"Agent: {response3['output']}")

async def test_email_tools_directly():
    """Test the email tools directly without the agent."""
    
    print("\n🧪 Direct Tool Testing")
    print("=" * 50)
    
    # Test 1: Generate confirmation number
    print("\n1. Testing generate_confirmation_number:")
    result1 = await generate_confirmation_number.ainvoke({})
    print(f"Result: {result1}")
    
    # Test 2: Send email with auto-generated number
    print("\n2. Testing send_confirmation_email_with_auto_number:")
    result2 = await send_confirmation_email_with_auto_number.ainvoke({
        "email": "test@example.com",
        "full_name": "Test Customer",
        "plan_name": "Premium Plan",
        "iptv_count": 2,
        "telefonia": True,
        "date": "2024-02-15",
        "time_slot": "08:00"
    })
    print(f"Result: {result2}")
    
    # Test 3: Send email with specific confirmation number
    print("\n3. Testing send_confirmation_email:")
    result3 = await send_confirmation_email.ainvoke({
        "email": "test2@example.com",
        "full_name": "Another Customer",
        "plan_name": "Basic Plan",
        "iptv_count": 1,
        "telefonia": False,
        "date": "2024-02-20",
        "time_slot": "13:00",
        "confirmation_number": "ADN-TEST-1234"
    })
    print(f"Result: {result3}")

if __name__ == "__main__":
    print("🚀 Starting Email Integration Example")
    print("Make sure your .env file has the correct SMTP settings:")
    print("- SMTP_PAY_SERVER")
    print("- SMTP_PAY_PORT") 
    print("- SMTP_PAY_USERNAME")
    print("- SMTP_PAY_PASSWORD")
    print()
    
    # Run the examples
    asyncio.run(example_conversation())
    asyncio.run(test_email_tools_directly())
    
    print("\n✅ Example completed!")
