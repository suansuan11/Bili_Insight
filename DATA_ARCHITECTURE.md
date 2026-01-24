# Bili-Insight 数据架构方案

## 1. 数据存储架构

### 核心设计原则
- **Python直接写入MySQL**: Python分析服务完成NLP计算后直接写入数据库，避免大JSON传输
- **Java读取DB**: Java后端从MySQL读取分析结果，对外提供API
- **异步任务模式**: Java提交任务→Python后台处理→前端轮询状态

### 数据流转
```
前端请求 → Java API → 调用Python服务 → 返回task_id
                                ↓
                        Python后台处理（爬虫+NLP）
                                ↓
                        直接写入MySQL
                                ↓
前端轮询 → Java API → 查询MySQL → 返回结果
```

## 2. 数据库表结构

### 2.1 analysis_task（分析任务表）
```sql
CREATE TABLE analysis_task (
    task_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    bvid VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL,  -- PENDING/RUNNING/COMPLETED/FAILED
    task_type VARCHAR(20),         -- VIDEO_REVIEW/COMPETITOR_MONITOR
    progress INT DEFAULT 0,        -- 0-100
    current_step VARCHAR(100),     -- 当前步骤描述
    error_message TEXT,
    created_at TIMESTAMP,
    completed_at TIMESTAMP
);
```

**字段说明**:
- `task_id`: 任务唯一标识，前端轮询依据
- `status`: 任务状态，前端根据此判断是否完成
- `progress`: 进度百分比，用于前端进度条展示
- `current_step`: 当前步骤，如"正在获取评论"

### 2.2 video_comment（视频评论表）
```sql
CREATE TABLE video_comment (
    comment_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    task_id BIGINT NOT NULL,
    bvid VARCHAR(20) NOT NULL,
    author VARCHAR(100),           -- 评论作者
    author_mid BIGINT,             -- 用户UID
    content TEXT NOT NULL,         -- 评论内容
    post_time TIMESTAMP,           -- 发布时间

    -- NLP分析字段
    sentiment_score DECIMAL(5,4),  -- 情感得分 0-1
    sentiment_label VARCHAR(20),   -- POSITIVE/NEUTRAL/NEGATIVE
    aspect VARCHAR(50),            -- ABSA切面标签（外观/性能/价格等）

    like_count INT DEFAULT 0,
    FOREIGN KEY (task_id) REFERENCES analysis_task(task_id)
);
```

**NLP字段说明**:
- `sentiment_score`: SnowNLP情感得分（0=负面，1=正面）
- `sentiment_label`: 分类标签（>0.6正面，<0.4负面，中间中性）
- `aspect`: 切面维度，通过关键词匹配识别（如"外观好看"→外观）

### 2.3 video_danmaku（视频弹幕表）
```sql
CREATE TABLE video_danmaku (
    danmaku_id BIGINT PRIMARY KEY AUTO_INCREMENT,
    task_id BIGINT NOT NULL,
    bvid VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,         -- 弹幕内容
    dm_time DECIMAL(10,3),         -- 弹幕时间点（秒）

    -- NLP分析字段
    sentiment_score DECIMAL(5,4),  -- 情感得分
    sentiment_label VARCHAR(20),   -- 情感标签

    FOREIGN KEY (task_id) REFERENCES analysis_task(task_id)
);
```

**关键点**:
- `dm_time`: 弹幕出现的视频时间点（如120.5秒），用于情绪时间轴
- 每条弹幕独立计算情感得分

### 2.4 sentiment_timeline（情绪时间轴表）
```sql
CREATE TABLE sentiment_timeline (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    task_id BIGINT NOT NULL,
    timeline_json TEXT,            -- 时间轴JSON数据
    aspect_sentiment_json TEXT,    -- 切面情感JSON数据
    UNIQUE KEY uk_task (task_id),
    FOREIGN KEY (task_id) REFERENCES analysis_task(task_id)
);
```

**JSON格式示例**:
```json
// timeline_json
[
  {"time": 0, "score": 0.7, "count": 15},
  {"time": 10, "score": 0.85, "count": 23},
  {"time": 20, "score": 0.6, "count": 18}
]

// aspect_sentiment_json
{
  "外观": {"score": 0.82, "count": 45},
  "性能": {"score": 0.71, "count": 38},
  "价格": {"score": 0.55, "count": 22}
}
```

## 3. NLP分析流程

### 3.1 情感分析（Sentiment Analysis）
```python
from snownlp import SnowNLP

def calculate_sentiment(text):
    s = SnowNLP(text)
    score = s.sentiments  # 0-1之间

    if score >= 0.6:
        label = 'POSITIVE'
    elif score <= 0.4:
        label = 'NEGATIVE'
    else:
        label = 'NEUTRAL'

    return score, label
```

### 3.2 切面识别（ABSA - Aspect-Based Sentiment Analysis）
```python
aspect_keywords = {
    '外观': ['外观', '颜值', '设计', '好看'],
    '性能': ['性能', '速度', '快', '卡顿'],
    '价格': ['价格', '贵', '便宜', '性价比']
}

def detect_aspect(text):
    for aspect, keywords in aspect_keywords.items():
        for keyword in keywords:
            if keyword in text:
                return aspect
    return None
```

### 3.3 情绪时间轴生成
```sql
-- 按10秒间隔聚合弹幕情感
SELECT
    FLOOR(dm_time / 10) * 10 as time_bucket,
    AVG(sentiment_score) as avg_score,
    COUNT(*) as count
FROM video_danmaku
WHERE task_id = ?
GROUP BY time_bucket
ORDER BY time_bucket;
```

## 4. API接口设计

### 4.1 Python服务端点

#### POST /api/analysis/video
**功能**: 启动视频完整分析任务

**请求**:
```json
{
  "bvid": "BV18TqpBqEMG",
  "max_comments": 500,
  "sessdata": "可选，用户凭证"
}
```

**响应**:
```json
{
  "task_id": 1234,
  "message": "分析任务已提交，任务ID: 1234"
}
```

#### GET /api/analysis/status/{task_id}
**功能**: 查询任务状态（前端轮询）

**响应**:
```json
{
  "task_id": 1234,
  "status": "RUNNING",
  "progress": 60,
  "current_step": "正在获取弹幕"
}
```

#### GET /api/analysis/result/{task_id}
**功能**: 获取完整分析结果

**响应**:
```json
{
  "task_id": 1234,
  "status": "COMPLETED",
  "bvid": "BV18TqpBqEMG",
  "comment_count": 423,
  "danmaku_count": 8765,
  "timeline_points": 45,
  "aspects": {
    "外观": {"score": 0.82, "count": 45},
    "性能": {"score": 0.71, "count": 38}
  }
}
```

#### GET /api/analysis/timeline/{task_id}
**功能**: 获取情绪时间轴数据（用于ECharts）

**响应**:
```json
{
  "timeline": [
    {"time": 0, "score": 0.7, "count": 15},
    {"time": 10, "score": 0.85, "count": 23}
  ]
}
```

#### GET /api/analysis/aspects/{task_id}
**功能**: 获取切面情感数据（用于雷达图）

**响应**:
```json
{
  "aspects": {
    "外观": {"score": 0.82, "count": 45},
    "性能": {"score": 0.71, "count": 38},
    "价格": {"score": 0.55, "count": 22}
  }
}
```

### 4.2 Java后端集成示例

```java
@Service
public class VideoAnalysisService {
    private static final String PYTHON_API = "http://localhost:18001/api/analysis";

    @Autowired
    private RestTemplate restTemplate;

    @Autowired
    private AnalysisTaskRepository taskRepository;

    // 提交分析任务
    public Long submitAnalysisTask(String bvid) {
        String url = PYTHON_API + "/video";

        Map<String, Object> request = new HashMap<>();
        request.put("bvid", bvid);
        request.put("max_comments", 500);

        ResponseEntity<Map> response = restTemplate.postForEntity(url, request, Map.class);
        Long taskId = ((Number) response.getBody().get("task_id")).longValue();

        return taskId;
    }

    // 查询任务状态
    public TaskStatusDTO getTaskStatus(Long taskId) {
        String url = PYTHON_API + "/status/" + taskId;
        ResponseEntity<TaskStatusDTO> response = restTemplate.getForEntity(url, TaskStatusDTO.class);
        return response.getBody();
    }

    // 从数据库读取评论（带分页）
    public Page<VideoComment> getComments(Long taskId, Pageable pageable) {
        return commentRepository.findByTaskId(taskId, pageable);
    }

    // 从数据库读取情绪时间轴
    public SentimentTimelineDTO getTimeline(Long taskId) {
        SentimentTimeline entity = timelineRepository.findByTaskId(taskId)
            .orElseThrow(() -> new ResourceNotFoundException("时间轴不存在"));

        ObjectMapper mapper = new ObjectMapper();
        List<TimelinePoint> timeline = mapper.readValue(
            entity.getTimelineJson(),
            new TypeReference<List<TimelinePoint>>() {}
        );

        return new SentimentTimelineDTO(timeline);
    }
}
```

## 5. 前端集成示例

### 5.1 提交分析任务
```javascript
async function analyzeVideo(bvid) {
    // 1. 调用Java后端接口
    const response = await fetch(`/api/video/analyze`, {
        method: 'POST',
        body: JSON.stringify({ bvid }),
        headers: { 'Content-Type': 'application/json' }
    });

    const { taskId } = await response.json();

    // 2. 开始轮询任务状态
    startPolling(taskId);
}

function startPolling(taskId) {
    const interval = setInterval(async () => {
        const status = await fetch(`/api/video/status/${taskId}`);
        const data = await status.json();

        // 更新进度条
        updateProgress(data.progress, data.currentStep);

        if (data.status === 'COMPLETED') {
            clearInterval(interval);
            loadResults(taskId);  // 加载结果
        } else if (data.status === 'FAILED') {
            clearInterval(interval);
            showError(data.errorMessage);
        }
    }, 2000);  // 每2秒轮询一次
}
```

### 5.2 渲染情绪时间轴（ECharts）
```javascript
async function renderTimeline(taskId) {
    const response = await fetch(`/api/video/timeline/${taskId}`);
    const { timeline } = await response.json();

    const chart = echarts.init(document.getElementById('timeline-chart'));

    chart.setOption({
        xAxis: {
            type: 'value',
            name: '时间(秒)'
        },
        yAxis: {
            type: 'value',
            name: '情感得分',
            min: 0,
            max: 1
        },
        series: [{
            type: 'line',
            data: timeline.map(p => [p.time, p.score]),
            smooth: true
        }]
    });
}
```

## 6. 数据优势

### 6.1 支持核心功能
- ✅ **交互式复盘**: `dm_time` + `sentiment_score` 支持视频播放器与情绪时间轴联动
- ✅ **口碑切面**: `aspect` + `sentiment_score` 支持雷达图展示各维度评价
- ✅ **自动化监测**: `analysis_task` 表支持定时任务和批量分析

### 6.2 性能优化
- **索引优化**: 为高频查询字段建立索引（bvid, task_id, sentiment_label）
- **JSON存储**: 时间轴数据用JSON存储，减少查询次数
- **批量插入**: 评论和弹幕使用批量INSERT提升写入速度

### 6.3 扩展性
- 可轻松添加新切面维度（如音质、包装等）
- 支持多种NLP模型替换（BERT、ChatGLM等）
- 可添加用户标签、热词提取等高级功能

## 7. 测试建议

### 运行完整测试
```bash
cd python_service
python test_full_video_analysis.py
```

### 预期结果
```
[1/5] 创建分析任务... ✓ 任务ID: 123
[2/5] 获取视频基础信息... ✓ 标题: xxx
[3/5] 获取所有评论... ✓ 已存入数据库: 423 条
[4/5] 获取所有弹幕... ✓ 已存入数据库: 8765 条
[5/5] 生成情绪时间轴... ✓ 时间轴数据点: 45

✅ 所有数据已保存到MySQL数据库
✅ 可通过任务ID(123)查询分析结果
```

### 数据库验证
```sql
-- 查看任务
SELECT * FROM analysis_task WHERE task_id = 123;

-- 查看评论统计
SELECT sentiment_label, COUNT(*)
FROM video_comment
WHERE task_id = 123
GROUP BY sentiment_label;

-- 查看情绪时间轴
SELECT timeline_json FROM sentiment_timeline WHERE task_id = 123;
```
