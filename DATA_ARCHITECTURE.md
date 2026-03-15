# Bili-Insight 数据架构方案

## 1. 数据流转与核心架构
本方案采用解耦的多语言微服务架构。
- **Python直接写入MySQL**: Python服务计算完毕大量 NLP 和图表构建数据后直接入库，拒绝巨大的 JSON 通过 HTTP 返回。
- **Java后端调度读取**: Java 负责管理权限，接收前端请求，触发 Python 任务及后续展示时的结果读取查询。
- **通信方式更新**: Java 和 Python 之间通过纯 HTTP REST 接口交互 (`PythonApiClient`)，完全淘汰了低效易错的 Subprocess 执行模式。

## 2. 数据库表结构

所有数据库敏感配置（如账号、密码）均移至 `.env` 文件中管理，消除代码级别硬编码。

### 2.1 user & project（核心业务关联表）- *新增*
```sql
CREATE TABLE user (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) DEFAULT 'USER',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE project (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id)
);
```

### 2.2 analysis_task（分析任务表）
负责串联前后端异步轮询状态（`status`, `progress`）。任务与具体的视频 (`bvid`) 绑定。

### 2.3 popular_videos（热门视频）- *已修复 Schema*
记录B站不同分区的实时热门视频信息，Java 端通过定时任务调度 Python 服务抓取回填。

### 2.4 video_comment & video_danmaku - *已修复 Schema*
`video_danmaku` 与 `video_comment` 修复了相应的类型定义，支持存储：
- 基础文本与时间（`dm_time` 用于联动）。
- NLP分析字段 (`sentiment_score`, `sentiment_label`, `aspect`)。

### 2.5 sentiment_timeline（情绪时间轴表）
储存预处理好的 ECharts 图表数据（`timeline_json`, `aspect_sentiment_json`），提升前端页面加载效率。

## 3. 服务端点与安全
- **鉴权**: 前端必须在 Header 中携带 `Bearer JWT_TOKEN` 才能访问 Java 控制器的内部接口。
- **Java 调用 Python**: Java 的 `PythonApiClient` 根据任务需要调用 Python `FastAPI`，Python 端点使用基于协程的长任务非阻塞机制完成数据库写入。
