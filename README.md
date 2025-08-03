# CERT CHALLENGE

Made by Steve Arce \:D

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

* **RAGAS (Synthetic Data & Evaluation):** Chosen to generate synthetic training data and evaluate the performance of our RAG pipeline, ensuring accuracy, robustness, and continuous improvement of AI responses.

* **LangSmith (Monitoring & Testing):** Used for tracking, testing, and debugging AI workflows in production, ensuring high-quality, reliable, and observable LLM-powered applications.


## ✅ Proposal for AI Agent Usage in Our App

The platform will leverage an AI agent built with LangGraph to handle multi-step, automated workflows. The agent will have access to internal APIs to perform key tasks such as checking available installation dates, retrieving and presenting internet service options to customers, and generating payment links for selected services. This agentic reasoning approach allows the system to dynamically plan and execute these steps in real time, significantly automating the onboarding process for new customers and reducing the workload on human agents.


## ✅ Data Sources and External API Integrations 


The data sources for the Retrieval-Augmented Generation (RAG) system will include the company’s public information, frequently asked questions and answers, and detailed data about all internet service plans, including pricing, speeds, and features. This information will enable the AI to provide accurate, context-aware responses to customer inquiries.

For external APIs, the platform will integrate with the existing internal API to retrieve available installation and reservation dates for online purchases. This will allow customers to select a convenient time to receive technicians. Once the service and appointment are confirmed, another internal API will be used to generate a secure payment link based on the selected plan, enabling the AI agent to complete the checkout process and guide the customer through finalizing their purchase.

## ✅ Default Chunking Strategy

My default chunking strategy will use a semantic chunking approach, where sentences in the company’s documentation and FAQs are embedded and grouped based on semantic similarity. This ensures that related information about a single internet plan (such as price, speed, and additional details) is kept together as one chunk, rather than being split arbitrarily by character count. This method improves retrieval accuracy because customers typically ask for very specific details (e.g., “What are the available 200 Mbps plans with installation times?”), and semantic chunking ensures all relevant information is retrieved in context.

I chose this approach over simple fixed-size chunking (e.g., 1,000 characters with 200-character overlap) because the corpus contains well-structured sections (plans, pricing tables, FAQs) with clear semantic boundaries. Using semantic chunking will reduce noise in retrieval, improve MB25 or hybrid search results, and lead to more precise AI answers for customers.

