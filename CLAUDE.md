# Project Context & Guidelines for Bili-Insight

## 1. Project Overview
- **Name**: Bili-Insight 智能舆情分析平台
- **Description**: 一个面向UP主和品牌方的B站舆情分析SaaS平台。提供视频高光时刻定位、口碑切面分析和竞品监测功能。
- **Core Value**:
  - **交互式复盘**: 视频播放器与“情绪时间轴”联动，精确到秒定位高光/败笔。
  - **口碑切面 (ABSA)**: 针对特定维度（如外观、性能）进行情感量化分析。
  - **自动化监测**: 品牌方可配置项目，系统自动追踪新视频数据。

## 2. Tech Stack & Architecture
- **Architecture**: **Vue 前端 + Java 业务后端 + Python 分析微服务**
- **Frontend**: Vue 3 + Vue Router + Axios (拦截器处理JWT) + ECharts。
- **Backend (Java)**:
  - Spring Boot + Spring Security + JWT 认证体系。
  - 使用 `PythonApiClient` 进行基于 HTTP REST 的服务通讯。
- **Analysis Service (Python)**:
  - FastAPI (修复了异步阻塞与重复路由)。
  - Scrapy / Requests 爬虫引擎。
  - Jieba + SnowNLP 情感评分与 ABSA 处理。
  - 直接写入 MySQL 数据库，配置读取 `.env` 保证安全。

## 3. Useful Commands
*根据不同子工程*

### Java Backend
- **Build**: `mvn clean package -DskipTests`
- **Run**: `mvn spring-boot:run`

### Python Analysis Service
- **Install Deps**: `pip install -r requirements.txt`
- **Configure Env**: 拷贝 `.env.example` 为 `.env` 并设置数据库密码。
- **Run API**: `uvicorn app.main:app --reload`

## 4. Key Implementation Logic (Critical)
- **Security & User Flow**: 用户注册登录换取 JWT，前端统一拦截并通过 Axios 发送。
- **Async Task Flow**:
  1. Java 接收请求 -> Java 调用 Python HTTP API -> 立刻返回任务ID。
  2. Python 异步执行爬取及 NLP 计算，直接将结果写入相关 DB 表。
  3. 前后端通过状态接口轮询结果。
- **Frontend Interaction**:
  - `VideoReviewView` 中 iframe 与情绪时间线严格对齐同步。
  - `CommentList` 依据 DB 里的 `sentiment_label` 和 `aspect` 进行双向筛选过滤。

## 5. Coding Conventions
- **Module Separation**:
  - 不要在 Python 里写复杂的鉴权管理；不要在 Java 里写 NLP。
  - 弃用所有的 Subprocess / CMD 调用机制，全部走 HTTP REST 通信。
- **Security First**: 密码与敏感数据禁止硬编码。

## 6. Current Context / Memory (Update Frequently)
- [x] **Infrastructure**: 修复 `popular_videos` / `danmaku` schema，新增 `user` 与 `project` 库表。
- [x] **Python Service**: 修复后台异步阻塞，清理冗余路由，环境配置剥离至 `.env`。
- [x] **Java Backend**: 集成 Spring Security + JWT，使用 `PythonApiClient` 重构与 Python 的跨应用通信。
- [x] **Frontend UX**: 实现了拦截器鉴权通信，完成了 `VideoReviewView` 联动视图和 `CommentList` 切面情感筛选组件。
