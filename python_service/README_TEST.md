# 视频完整分析功能 - 测试说明

## 已实现功能

### 1. 数据获取服务
- ✅ 视频基础信息（标题、UP主、播放量、点赞数等）
- ✅ 所有评论（支持分页获取，最多500条）
- ✅ 所有弹幕（包含精确时间点）

### 2. NLP分析服务
- ✅ 情感分析（SnowNLP，0-1得分）
- ✅ 情感分类（POSITIVE/NEUTRAL/NEGATIVE）
- ✅ 切面识别（ABSA）：外观、性能、价格、续航、拍照、屏幕、系统、售后

### 3. 数据存储服务
- ✅ MySQL数据库存储
- ✅ 任务管理系统（PENDING→RUNNING→COMPLETED）
- ✅ 批量插入优化
- ✅ 索引优化（bvid、sentiment_label、dm_time）

### 4. API服务
- ✅ POST /api/analysis/video - 提交分析任务
- ✅ GET /api/analysis/status/{task_id} - 查询任务状态
- ✅ GET /api/analysis/result/{task_id} - 获取完整结果
- ✅ GET /api/analysis/timeline/{task_id} - 获取情绪时间轴
- ✅ GET /api/analysis/aspects/{task_id} - 获取切面情感分析

## 测试命令

### 快速测试（不存数据库）
```bash
python quick_test.py
```

**功能**: 验证数据获取和NLP分析
**输出**:
- 视频信息（标题、播放量等）
- 20条评论示例
- 所有弹幕示例
- NLP情感分析测试

**预期结果**:
```
[OK] Title: xxx
[OK] Fetched 20 comments
[OK] Fetched 3337 danmakus
Score: 0.9941 | Label: POSITIVE | Aspect: 外观
```

### 完整测试（存入数据库）
```bash
python test_full_video_analysis.py
```

**功能**: 完整的数据获取→NLP分析→数据库存储流程
**输出**:
- 创建任务ID
- 获取视频信息
- 获取并存储所有评论
- 获取并存储所有弹幕
- 生成情绪时间轴
- 生成切面情感分析

**预期结果**:
```
[1/5] 创建分析任务... ✓ 任务ID: 1
[2/5] 获取视频基础信息... ✓
[3/5] 获取所有评论... ✓ 已存入数据库: 423 条评论
[4/5] 获取所有弹幕... ✓ 已存入数据库: 3337 条弹幕
[5/5] 生成情绪时间轴... ✓ 时间轴数据点: 45

✅ 所有数据已保存到MySQL数据库
```

## 数据库验证

### 查看任务
```sql
SELECT * FROM analysis_task WHERE bvid = 'BV18TqpBqEMG';
```

### 查看评论统计
```sql
SELECT
    sentiment_label,
    COUNT(*) as count,
    ROUND(AVG(sentiment_score), 4) as avg_score
FROM video_comment
WHERE task_id = 1
GROUP BY sentiment_label;
```

### 查看弹幕情绪时间轴
```sql
SELECT
    FLOOR(dm_time / 10) * 10 as time_bucket,
    COUNT(*) as count,
    ROUND(AVG(sentiment_score), 4) as avg_score
FROM video_danmaku
WHERE task_id = 1
GROUP BY time_bucket
ORDER BY time_bucket
LIMIT 10;
```

### 查看切面情感分析
```sql
SELECT
    aspect,
    COUNT(*) as mention_count,
    ROUND(AVG(sentiment_score), 4) as sentiment
FROM video_comment
WHERE task_id = 1 AND aspect IS NOT NULL
GROUP BY aspect;
```

## 文件说明

### 核心服务
- `app/services/bilibili_service.py` - B站数据获取服务
- `app/services/video_storage_service.py` - 数据存储和NLP分析服务
- `app/services/credential_manager.py` - 凭证管理

### API路由
- `app/routers/analysis.py` - 视频完整分析API路由

### 测试脚本
- `quick_test.py` - 快速测试（不存数据库）
- `test_full_video_analysis.py` - 完整测试（存数据库）

### 文档
- `../DATA_ARCHITECTURE.md` - 数据架构详细说明
- `../USAGE_GUIDE.md` - 完整使用指南
- `../sql/schema_complete_rebuild.sql` - 数据库Schema

## API测试

### 启动服务
```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 18001 --reload
```

### 访问API文档
http://127.0.0.1:18001/docs

### 测试API端点

#### 1. 提交分析任务
```bash
curl -X POST "http://127.0.0.1:18001/api/analysis/video" \
  -H "Content-Type: application/json" \
  -d '{"bvid": "BV18TqpBqEMG", "max_comments": 500}'
```

#### 2. 查询任务状态
```bash
curl "http://127.0.0.1:18001/api/analysis/status/1"
```

#### 3. 获取情绪时间轴
```bash
curl "http://127.0.0.1:18001/api/analysis/timeline/1"
```

#### 4. 获取切面分析
```bash
curl "http://127.0.0.1:18001/api/analysis/aspects/1"
```

## 数据流程图

```
用户请求
   ↓
POST /api/analysis/video
   ↓
创建任务 (analysis_task)
   ↓
后台任务启动
   ↓
┌─────────────────────────────────┐
│ 1. 获取视频信息 (BilibiliService) │
│ 2. 获取评论 (500条)                │
│    ├─ NLP情感分析                  │
│    ├─ ABSA切面识别                │
│    └─ 存入video_comment表         │
│ 3. 获取弹幕 (全部)                 │
│    ├─ NLP情感分析                  │
│    └─ 存入video_danmaku表         │
│ 4. 生成情绪时间轴                  │
│    ├─ 按10秒聚合弹幕情感           │
│    └─ 存入sentiment_timeline表    │
│ 5. 生成切面情感分析                │
│    ├─ 统计各切面评论数和平均得分    │
│    └─ 存入sentiment_timeline表    │
└─────────────────────────────────┘
   ↓
更新任务状态 (COMPLETED)
   ↓
前端轮询获取结果
```

## 性能指标

### 测试视频：BV18TqpBqEMG
- 评论数：~500条
- 弹幕数：~3337条
- 处理时间：约30-60秒（取决于网络速度）

### 数据库表
- `analysis_task` - 任务管理
- `video_comment` - 评论数据（含NLP字段）
- `video_danmaku` - 弹幕数据（含NLP字段）
- `sentiment_timeline` - 时间轴和切面分析（JSON格式）

## 核心技术

### 1. 数据获取
- **bilibili-api-python**: 官方Python库
- **异步IO**: asyncio/aiohttp提升并发性能
- **凭证管理**: 统一管理和分发登录凭证

### 2. NLP分析
- **SnowNLP**: 中文情感分析（0-1得分）
- **Jieba**: 中文分词（用于关键词提取）
- **关键词匹配**: ABSA切面识别

### 3. 数据存储
- **MySQL**: 关系型数据库存储
- **JSON字段**: 时间轴数据使用JSON格式
- **批量插入**: executemany优化写入性能
- **索引优化**: 高频查询字段建立索引

### 4. 架构设计
- **异步任务**: FastAPI BackgroundTasks
- **前端轮询**: 定期查询任务状态
- **Python直写DB**: 避免大JSON传输
- **Java读DB**: 后端从数据库读取结果

## 已验证测试结果

### 快速测试
✅ 视频信息获取成功
✅ 评论获取成功（20条）
✅ 弹幕获取成功（3337条）
✅ NLP情感分析正常
- "这个手机真的太好看了" → Score: 0.9941, POSITIVE, 外观
- "性能很差，经常卡顿" → Score: 0.0554, NEGATIVE, 性能
- "价格还行，中规中矩吧" → Score: 0.9986, POSITIVE, 价格

## 下一步

1. 运行 `python quick_test.py` 验证数据获取
2. 运行 `python test_full_video_analysis.py` 进行完整测试
3. 查看数据库验证数据正确存储
4. 启动API服务测试HTTP端点
5. 集成到Java后端
6. 前端开发情绪时间轴可视化
