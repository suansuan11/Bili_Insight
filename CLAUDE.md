# Project Context & Guidelines for Bili-Insight

## 1. Project Overview
- **Name**: Bili-Insight 智能舆情分析平台
- **Description**: 一个面向UP主和品牌方的B站舆情分析SaaS平台。提供视频高光时刻定位、口碑切面分析和竞品监测功能。
- **Core Value**:
  - **交互式复盘**: 视频播放器与“情绪时间轴”联动，精确到秒定位高光/败笔 。
  - **口碑切面 (ABSA)**: 针对特定维度（如外观、性能）进行情感量化分析 。
  - **自动化监测**: 品牌方可配置项目，系统自动追踪新视频数据 。

## 2. Tech Stack & Architecture
- **Architecture**: **Java 业务后端 + Python 分析微服务** 的解耦架构 。
- **Backend (Main)**:
  - Language: Java (Spring Boot)
  - Auth: Spring Security + JWT 
  - DB Access: Spring Data JPA / MyBatis 
  - Role: 负责用户管理、任务调度、API对外暴露 。
- **Analysis Service (Microservice)**:
  - Language: Python (FastAPI) 
  - Crawler: Scrapy / Requests 
  - NLP: Jieba + SnowNLP (0-1情感打分) 
  - Role: 负责爬虫、NLP计算、**直接写入数据库** 。
- **Database**: MySQL (Shared by both services) 。

## 3. Useful Commands
*Claude, please adapt these based on the sub-project structure:*

### Java Backend
- **Build**: `mvn clean package -DskipTests`
- **Run**: `mvn spring-boot:run`
- **Test**: `mvn test`

### Python Analysis Service
- **Install Deps**: `pip install -r requirements.txt`
- **Run API**: `uvicorn main:app --reload`
- **Test NLP**: `python tests/test_sentiment.py`

## 4. Key Implementation Logic (Critical)
- **Async Task Flow**:
  1. Java receives frontend request -> Java calls Python via HTTP (Async) -> Java returns "Task Submitted" immediately .
  2. Frontend polls Java API for status updates .
- **Data Write Flow**:
  - **Distinct Rule**: Python service calculates NLP results and **writes directly to MySQL**, NOT returning huge JSONs to Java . Java reads from DB later.
- **Emotion-Time Linkage**:
  - Requires generating a JSON mapping timestamps to sentiment scores for ECharts rendering .
- **ABSA (Aspect Analysis)**:
  - Logic: Keyword Matching (classify aspect) -> Calculate SnowNLP Mean -> Store Result .

## 5. Coding Conventions
- **Module Separation**:
  - Keep business logic (User, Project, Auth) in Java.
  - Keep heavy computation/IO (Crawling, NLP) in Python.
- **API Communication**: Use clear HTTP REST patterns for Java <-> Python communication (e.g., `POST /api/analyze/video`).
- **Error Handling**: Java must handle timeouts when calling Python services.

## 6. Current Context / Memory (Update Frequently)
- [ ] **Infrastructure**: Initialize MySQL tables (Users, Projects, Videos, SentimentData).
- [ ] **Java Backend**: Setup Spring Security + JWT for "Creator" vs "Brand" roles .
- [ ] **Python Service**: Implement FastAPI endpoint to receive BVID and start Scrapy spider.
- [ ] **Integration**: Implement the RestTemplate/WebClient call from Java to Python .