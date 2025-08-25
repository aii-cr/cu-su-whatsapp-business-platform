# Whisper Chat | AI-Powered Whatsapp Business Platform

Created by Steve Arce


## Table of Contents

- [Description of the Problem](#-description-of-the-problem)
- [Specific User Problematic](#-specific-user-problematic)
- [Proposed Solution](#-proposed-solution)
- [Technology Stack and Tooling Choices](#-technology-stack-and-tooling-choices)
- [Proposal for AI Agent Usage in Our App](#-proposal-for-ai-agent-usage-in-our-app)
- [Data Sources and External API Integrations](#-data-sources-and-external-api-integrations)
- [Chunking Strategy Implementation](#-chunking-strategy-implementation)
- [Build an end-to-end prototype and deploy to local host with a front end](#-build-an-end-to-end-prototype-and-deploy-to-local-host-with-a-front-end-vercel-deployment-not-required)
- [RAG Pipeline Performance & Production Deployment](#-rag-pipeline-performance--production-deployment)
- [AI Implementation Architecture](#-ai-implementation-architecture)

## ✅ Description of the Problem

Develop an AI-powered WhatsApp Business platform designed to provide a cost-effective solution for companies seeking to enhance customer support.

## ✅ Specific User Problematic

Our Internet Service Provider business currently relies on an expensive WhatsApp Business platform that lacks key features our company needs. For example, it lacks the ability to smoothly transfer or escalate conversations between agents internally without notifying or disrupting the customer. The platform also lacks conversation tagging for better classification and organization, and it does not provide an AI-powered chatbot to handle basic customer inquiries or automate processes such as acquiring a new service, generating payment links, and scheduling installation appointments in real time based on both customer and technician availability.

This limited functionality not only creates operational inefficiencies but also leads to high annual costs for the company. A new AI-powered solution would significantly reduce expenses while introducing advanced features such as automated conversation summarization, mood-based emoji tagging, AI-generated responses, and real-time assistance for employees on how to better handle customer interactions.


## ✅ Proposed Solution

Our solution is to build a next-generation, AI-powered WhatsApp Business platform using the official WhatsApp Cloud API, transforming customer support into a smart, automated experience. Unlike current costly tools, this platform will enable businesses to deliver faster, more personalized service while drastically cutting operational expenses.

Powered by advanced AI agents and Retrieval-Augmented Generation (RAG), customers will be able to purchase services, receive instant payment links, and book installation appointments seamlessly—all without human intervention. The platform will feature intelligent capabilities such as mood detection, automatic escalation to the right agents or departments, real-time conversation summarization, and AI-guided response suggestions. By automating frequent inquiries and proactively detecting service outages in customer areas, this solution will not only reduce employee workload but also set a new standard for customer satisfaction and operational efficiency.


## ✅ Technology Stack and Tooling Choices

* **Next.js (Frontend):** Selected for its ability to deliver a modern, responsive, and SEO-friendly frontend with excellent developer experience, supporting scalable and fast-loading applications.

* **FastAPI (Backend):** Chosen for its high performance, asynchronous capabilities, and seamless integration with the WhatsApp Business API and AI services, making it ideal for building scalable, secure backends.

* **LangChain (AI Orchestration):** Used to design complex AI workflows, chain multiple AI tasks, and implement Retrieval-Augmented Generation (RAG) efficiently, enabling more advanced conversational capabilities.

* **LangGraph (Agentic AI System):** Enables building structured, multi-step AI agents capable of automating tasks like service acquisition and installation booking with improved reliability and flexibility.

* **Qdrant Cloud (Vector Database):** Provides a highly performant, cloud-based vector storage solution optimized for semantic search and retrieval, essential for powering accurate and fast RAG queries.

* **Performance Monitoring:** Real-time metrics tracking and optimization for the RAG pipeline, ensuring accuracy, robustness, and continuous improvement of AI responses.

* **LangSmith (Monitoring & Testing):** Used for tracking, testing, and debugging AI workflows in production, ensuring high-quality, reliable, and observable LLM-powered applications.


## ✅ Proposal for AI Agent Usage in Our App

The platform will leverage an AI agent built with LangGraph to handle multi-step, automated workflows. The agent will have access to internal APIs to perform key tasks such as checking available installation dates, retrieving and presenting internet service options to customers, and generating payment links for selected services. This agentic reasoning approach allows the system to dynamically plan and execute these steps in real time, significantly automating the onboarding process for new customers and reducing the workload on human agents.


## ✅ Data Sources and External API Integrations 


The data sources for the Retrieval-Augmented Generation (RAG) system will include the company’s public information, frequently asked questions and answers, and detailed data about all internet service plans, including pricing, speeds, and features. This information will enable the AI to provide accurate, context-aware responses to customer inquiries.

For external APIs, the platform will integrate with the existing internal API to retrieve available installation and reservation dates for online purchases. This will allow customers to select a convenient time to receive technicians. Once the service and appointment are confirmed, another internal API will be used to generate a secure payment link based on the selected plan, enabling the AI agent to complete the checkout process and guide the customer through finalizing their purchase.

## ✅ Chunking Strategy Implementation

The RAG system implements a **RecursiveCharacterTextSplitter** approach optimized for the company's documentation structure. Located in `/app/services/ai/shared/tools/rag/ingest.py`, the chunking strategy uses a 800-character chunk size with 120-character overlap, which has proven effective for maintaining context while ensuring optimal retrieval performance.

This chunking approach was specifically chosen to handle the structured nature of internet service documentation, where information about plans, pricing, and technical specifications needs to be kept coherent. The recursive splitting method intelligently attempts to break documents at natural boundaries like sentences and paragraphs, rather than arbitrary character limits.

The implementation enhances each chunk with comprehensive metadata including source information, language indicators, and content versioning. This metadata-rich approach enables the RAG system to perform more targeted retrieval based on document type, language, and content freshness. The 120-character overlap ensures that context isn't lost at chunk boundaries, which is particularly important for technical specifications that might span multiple chunks.

When customers ask specific questions about service plans or technical details, this chunking strategy ensures that relevant information is retrieved as complete, contextual units rather than fragmented text pieces.


## ✅ Build an end-to-end prototype and deploy to local host with a front end (Vercel deployment not required).

The WhatsApp Business platform prototype has been developed with a sophisticated AI system integrated throughout the application stack. The backend (`/app/`) leverages FastAPI with WebSocket support for real-time messaging, while the comprehensive AI agent system (`/app/services/ai/`) provides intelligent automation capabilities. The MongoDB database handles data persistence, and RESTful APIs manage conversation workflows seamlessly.

The frontend (`/frontend/`) showcases a modern interface built with Next.js 15+ and Tailwind CSS, featuring an intuitive chat interface, comprehensive agent dashboard, and service plan selection system. What makes this prototype unique is the deep integration of AI capabilities that go far beyond simple chatbot functionality.

At the heart of the system lies a hybrid RAG pipeline that combines multiple retrieval strategies for optimal performance. The WhatsApp Agent, powered by LangGraph, orchestrates complex multi-step workflows that can guide customers through entire service acquisition processes. Meanwhile, the Writer Agent assists human agents by analyzing conversation context and generating intelligent response suggestions using the company's knowledge base.

The platform includes sophisticated features like real-time sentiment monitoring and automated conversation summarization, implemented as LangChain-powered services that enhance the overall customer experience. WebSocket integration ensures that sentiment updates and notifications flow seamlessly between the backend and frontend, creating a responsive and engaging user interface.

Local deployment can be achieved by running `uvicorn main:app --reload` for the backend and `npm run dev` for the frontend, providing a complete environment for testing and development of the AI-powered customer service automation capabilities.


## ✅ RAG Pipeline Performance & Production Deployment

The advanced RAG system has been successfully implemented and deployed in production within `/app/services/ai/shared/tools/rag/`. The system utilizes a hybrid approach combining multiple retrieval strategies for optimal performance across different query types.

### Production Implementation

**🔍 Retrieval Strategy Selection:**
- **Fast Retrieval**: Basic dense vector search for real-time responses
- **Comprehensive Retrieval**: Multi-query expansion + compression + Cohere re-ranking for complex queries
- **Adaptive Selection**: Automatic strategy selection based on query complexity and context requirements

**📊 Performance Optimizations:**
- **Semantic Chunking**: Context-preserving document splitting for improved accuracy
- **Cohere Re-ranking**: Advanced relevance optimization for better result quality  
- **Redis Caching**: High-performance caching layer for frequently accessed information
- **Performance Monitoring**: Real-time metrics tracking and optimization

**🎯 Production Impact**: The hybrid RAG system provides reliable, accurate responses for the WhatsApp Business platform with optimal balance of speed, accuracy, and relevance for automated customer service.



## ✅ AI Implementation Architecture

The WhatsApp Business platform showcases a sophisticated AI ecosystem that transforms traditional customer service into an intelligent, automated experience. At its core, the system features **2 specialized AI agents** working alongside **advanced LangChain-powered services** to create a seamless customer support environment.

### **🤖 Core AI Agents**

#### **WhatsApp Agent: The Conversational Orchestrator**

The WhatsApp Agent represents the pinnacle of conversational AI implementation, built on LangGraph's state machine architecture. This agent doesn't just respond to customer queries—it actively guides customers through complex, multi-step processes like service acquisition and installation booking. 

What makes this agent exceptional is its arsenal of **7 specialized tools** that enable it to handle everything from catalog browsing to final email confirmations. The agent can seamlessly switch between English and Spanish, maintaining conversation context across multiple interactions while ensuring each response meets quality standards through built-in helpfulness validation.

The agent's state management capabilities allow it to remember where customers are in their journey, whether they're comparing internet plans, providing personal information, or scheduling installation appointments. This persistent memory creates a natural, human-like conversation flow that customers find intuitive and helpful.

#### **Writer Agent: The Human Agent Assistant**

The Writer Agent serves as an intelligent co-pilot for human customer service representatives. Rather than replacing human agents, this AI system amplifies their capabilities by providing contextual response suggestions based on comprehensive conversation analysis.

When a human agent needs to respond to a complex customer inquiry, the Writer Agent analyzes the entire conversation history, retrieves relevant information from the company's knowledge base, and generates well-crafted response suggestions. The agent presents both customer-facing responses and internal reasoning, helping human agents understand the context and make informed decisions about their communications.

### **🔧 LangChain-Powered AI Services**

#### **Intelligent Sentiment Monitoring**

The sentiment analysis system goes beyond simple positive/negative classification, implementing a nuanced emotional intelligence framework with **10 distinct sentiment emojis** that capture the full spectrum of customer emotions. This service analyzes conversation patterns across all customer messages, tracking emotional progression and providing real-time insights to human agents through WebSocket notifications.

#### **Automated Conversation Summarization**

The conversation summarization service leverages advanced LangChain capabilities to generate professional summaries that facilitate smooth agent handoffs. When human agents need to take over conversations, they receive comprehensive summaries that include participant identification, interaction metrics, and current sentiment context, ensuring continuity of service.

### **🔍 Advanced Hybrid RAG System**

The Retrieval-Augmented Generation system forms the knowledge backbone of the entire platform, enabling both AI agents to provide accurate, contextual responses grounded in the company's documentation. This isn't a simple keyword search system—it's a sophisticated information retrieval pipeline that combines multiple strategies to ensure optimal performance across different query types.

#### **Intelligent Retrieval Pipeline**

At the foundation lies a dense vector search system powered by OpenAI embeddings and Qdrant vector database, providing semantic understanding that goes far beyond keyword matching. The system implements an adaptive approach that automatically selects the most appropriate retrieval strategy based on query characteristics.

For simple queries like "precio" or "plan básico," the system employs **fast retrieval** mode, utilizing basic dense vector search with extended caching for immediate responses. More complex customer inquiries trigger **comprehensive retrieval** mode, which combines multi-query expansion with advanced Cohere re-ranking to ensure the most relevant information surfaces first.

The multi-query expansion feature is particularly clever—it automatically generates query variations to capture different ways customers might express the same need, dramatically improving recall without sacrificing precision. Meanwhile, the Cohere re-ranking system provides a final quality filter, ensuring that the most contextually relevant information reaches the customer.

#### **Performance and Reliability Features**

The system includes robust performance monitoring that tracks retrieval metrics in real-time, enabling continuous optimization of response quality and speed. A Redis-based caching layer provides high-performance storage for frequently accessed information, reducing latency for common customer inquiries.

The architecture supports multi-tenant deployments with isolated data per organization, content versioning with hash-based updates, and seamless bilingual processing for both Spanish and English content. Rich metadata enhancement enables sophisticated filtering and retrieval based on document type, content freshness, and relevance scores.

**🎯 Real-World Impact**: This hybrid RAG system enables the WhatsApp Business platform to provide instant, accurate responses to customer inquiries while supporting human agents with comprehensive information retrieval capabilities, creating a truly intelligent customer service ecosystem.

