# DALIAS — Distributed Agentic Log Intelligence and Analytics System

#### DALIAS (Distributed Agentic Log Intelligence and Analytics System), an innovative microservices architecture that integrates event-driven communication, asynchronous stream processing, and large language model- powered analysis for intelligent log management in cloud-native systems. The system addresses the critical challenge of extracting actionable insights from massive volumes of distributed logs through a combination of rule-based anomaly detection and AI-driven analysis. Our work demonstrates how modern architectural patterns - specifically event-driven microservices, containerization, and agentic AI systems - enhance three critical quality attributes: scalability, reliability, and maintainability, making DALIAS suitable for production-grade observability infrastructure.

This repository contains a minimal end-to-end implementation: ingestion -> Kafka (Redpanda) -> processing -> MongoDB -> Agent (LLM) -> Dashboard.

#### Output
<img width="915" height="837" alt="image" src="https://github.com/user-attachments/assets/74048a03-f8e3-4016-98b6-c420fbafcfed" />


## Quick start
1. Copy `.env.example` to `.env` and fill GEMINI_API_KEY
2. Build and run:
   ```bash
   docker-compose up --build
   ```
3. Visit http://localhost:8000 to view dashboard

## Notes
- Agent uses Google Gemini API; set GEMINI_API_KEY in environment.
- Replace Redpanda with an external Kafka cluster if needed.
- To read a more detailed overview, refer to the 'Report.pdf' file.
