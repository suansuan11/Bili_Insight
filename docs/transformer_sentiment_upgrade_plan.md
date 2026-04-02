# Bili-Insight Transformer 情感分析升级改造方案

---

## 📋 实施进度追踪

> 最后更新：2026-03-27
>
> 说明：本页“已完成”表示代码与脚本已经落库到仓库；数据库迁移、依赖安装、模型下载与端到端任务验证仍需在目标环境执行。

### 阶段 1 — 最小可用版 ✅ 已完成（2026-03-27）

| 任务 | 状态 | 备注 |
|---|---|---|
| 增加 Transformer 依赖到 requirements.txt | ✅ 完成 | transformers/torch/sentencepiece 等 8 项 |
| 新增 SQL 迁移脚本 | ✅ 完成 | `sql/migrations/2026-03-transformer-sentiment-upgrade.sql` |
| 新增 `TextNormalizer` | ✅ 完成 | `python_service/app/services/text_normalizer.py` |
| 新增 `ModelRegistry` | ✅ 完成 | `python_service/app/services/model_registry.py`，默认使用 multilingual DistilBERT 三分类 |
| 新增 `DomainRuleEngine` | ✅ 完成 | `python_service/app/services/domain_rules.py` |
| 新增 B站领域词典 | ✅ 完成 | `python_service/app/resources/domain_lexicon.yml` |
| 新增 `SentimentAnalyzer` | ✅ 完成 | `python_service/app/services/sentiment_analyzer.py`，支持 GPU / SnowNLP fallback |
| 新增 `AspectAnalyzer` | ✅ 完成 | `python_service/app/services/aspect_analyzer.py`，多切面 recall + pair classification |
| 改造 `video_storage_service.py` | ✅ 完成 | 评论/弹幕分流，写入 10 个新增字段，置信度加权时间轴聚合 |

### 阶段 2 — 切面升级版 ✅ 已完成（2026-03-27，随阶段1一同实施）

| 任务 | 状态 | 备注 |
|---|---|---|
| 新增 `AspectAnalyzer` | ✅ 完成 | 支持多 aspect 召回与情感二次判别 |
| 增加 `aspect_details_json` 字段 | ✅ 完成 | SQL 迁移已包含 |
| 改造 `generate_sentiment_timeline()` | ✅ 完成 | 优先读 `aspect_details_json` 聚合，回退旧字段 |

### 阶段 3 — 评估闭环版 ✅ 已完成（2026-03-27）

| 任务 | 状态 | 备注 |
|---|---|---|
| `sentiment_annotation` 标注表 | ✅ 完成 | SQL 迁移脚本已包含 |
| 评估脚本 1：构建候选集 | ✅ 完成 | `python_service/scripts/eval/build_annotation_dataset.py` |
| 评估脚本 2：离线评估 | ✅ 完成 | `python_service/scripts/eval/run_sentiment_eval.py` |
| 评估脚本 3：导出低置信度样本 | ✅ 完成 | `python_service/scripts/eval/export_low_confidence_samples.py` |
| 迁移脚本 1：按任务重算 | ✅ 完成 | `python_service/scripts/migrate/recompute_sentiment_for_task.py` |
| 迁移脚本 2：批量回填 | ✅ 完成 | `python_service/scripts/migrate/backfill_transformer_sentiment.py` |

### 2026-03-27 审查后补丁 ✅ 已完成

| 问题 | 状态 | 备注 |
|---|---|---|
| 回填后未重建时间轴 | ✅ 已修复 | 两个迁移脚本都会在评论/弹幕重算后重建 `sentiment_timeline` |
| 评论跨任务主键污染 | ✅ 已修复 | 评论写入改为任务域内唯一 ID，不再使用跨任务 `ON DUPLICATE KEY UPDATE` |
| aspect 仅拼接前缀伪二分类 | ✅ 已修复 | 改为 `aspect + text` pair inference，并按转折/子句抽取局部上下文 |
| 脚本默认库名错误 | ✅ 已修复 | 所有评估/迁移脚本默认改为 `bili_insight_db` |
| Transformer 首次失败后永久回退 | ✅ 已修复 | 改为单次请求降级，不再把全进程静默锁死在 SnowNLP |

### 待办 / 后续建议

| 任务 | 状态 | 说明 |
|---|---|---|
| 执行数据库迁移 SQL | ✅ 已执行 | 已在本地 `bili_insight_db` 执行 `sql/migrations/2026-03-transformer-sentiment-upgrade.sql` |
| 安装新依赖 | ✅ 已执行 | 已在 `python_service/.venv` 完整安装 `requirements.txt` |
| 启动本地 MySQL | ✅ 已确认 | 已确认本地 MySQL 可连，schema 迁移成功 |
| 验证单任务分析 | ✅ 已验证 | 已用 `recompute_sentiment_for_task.py` 重算并确认新字段全部落库，时间轴重建正常 |
| 验证 Spring Boot 自动拉起 Python | ✅ 已执行 | `mvn spring-boot:run` 已实测可连库并自动拉起 Python 服务 |
| Java 实体扩展 | ✅ 已完成 | 扩展 `VideoComment`/`VideoDanmaku`/`SentimentTimeline` 实体和 Mapper，新增情感置信度、强度、来源、版本、情绪标签、切面详情等字段 |
| 建立人工标注集 | ✅ 已完成 | 已运行 `build_annotation_dataset.py` 导出 1000 条候选样本（评论 700 + 弹幕 300），位于 `python_service/scripts/eval/annotation_candidates.csv` |
| 批量回填历史数据 | ✅ 已完成 | 4 个 COMPLETED 任务全部回填，1327 条评论 + 3423 条弹幕，0 失败 |
| 修复 YAML 词典解析错误 | ✅ 已修复 | `domain_lexicon.yml` 中 `不错（注意:` 被 YAML 解析为 dict，已改为行尾注释；`domain_rules.py` 增加 `isinstance` 类型守卫 |

---



## 1. 文档目标

本文档给出 Bili-Insight 当前中文情感分析能力的完整升级方案，目标是将现有的 `SnowNLP + 三分类阈值 + 单关键词 aspect` 方案升级为：

1. 基于 Transformer 的中文情感主分类模型
2. 面向 B 站语境的规则纠偏层
3. 评论与弹幕分流处理
4. `aspect 召回 + 针对 aspect 的情感二次判别`
5. 可落库的置信度、模型版本、扩展标签体系
6. 可持续迭代的小型人工标注集与离线评估脚本

本文档覆盖：

1. 当前问题分析
2. 目标架构
3. 数据库改造
4. Python 服务改造
5. Java 与前端兼容策略
6. 迁移脚本与评估脚本设计
7. 实施顺序与风险控制


## 2. 当前实现现状与问题

### 2.1 当前关键实现位置

当前情感分析的核心逻辑在以下文件：

1. `python_service/app/services/video_storage_service.py`
2. `python_service/app/routers/analysis.py`
3. `sql/bili_insight_db.sql`

当前 `video_storage_service.py` 的核心问题：

1. `calculate_sentiment()` 使用 `SnowNLP` 返回 0-1 分数，再以固定阈值切分为 `POSITIVE / NEUTRAL / NEGATIVE`
2. `detect_aspect()` 仅凭关键词命中返回单个 aspect，不支持一条文本多个 aspect
3. 评论和弹幕走同一套逻辑，没有按文本类型进行差异化处理
4. 数据库存储只有主情感标签和粗糙分数，没有置信度、模型来源、模型版本、情绪标签或 aspect 细节

### 2.2 当前方案效果差的根因

当前方案在中文互联网语境下表现差，主要不是阈值设置问题，而是方法本身不匹配场景：

1. `SnowNLP` 对中文网络语、口语、缩写、夸张表达、反讽、阴阳怪气适应性差
2. B 站弹幕极短、噪声高、梗文化强，传统通用情感模型误判率高
3. 一条评论可能同时表达多个方面的不同态度，当前单 `aspect` 设计天然不够
4. 没有 `confidence`，所有结果都被“硬判”，导致错误样本看起来非常刺眼
5. 没有评估集，无法客观衡量模型升级是否真的提升


## 3. 升级目标

### 3.1 业务目标

升级后的系统应满足：

1. 主情感标签明显优于当前 `SnowNLP`
2. 对负面、转折句、反讽、网络语的识别显著改善
3. 支持一条文本多个切面分别打标签
4. 能区分评论和弹幕的分布差异
5. 能追踪“当前结果是谁打的、可信度多少、版本是什么”
6. 能建立可持续优化闭环

### 3.2 非目标

本次升级不追求一步到位实现“接近人工”的全场景中文舆情分析。以下问题仍可能存在：

1. 极强语境依赖的梗和黑话
2. 跨句复杂逻辑推理
3. 纯上下文依赖的反讽
4. 垂直领域极少见词汇

本方案目标是将系统从“明显不可信”提升到“多数样本可用、关键业务明显改善”。


## 4. 目标架构总览

升级后，Python 分析链路如下：

1. 文本清洗与标准化
2. 文本类型分流：`comment` / `danmaku`
3. 主情感分类模型推理
4. 规则纠偏与置信度校正
5. aspect 候选召回
6. 针对 aspect 的情感二次判别
7. 写库并保存模型版本、置信度、扩展标签
8. 生成时间轴、切面聚合统计

推荐的模块拆分：

1. `python_service/app/services/text_normalizer.py`
2. `python_service/app/services/domain_rules.py`
3. `python_service/app/services/model_registry.py`
4. `python_service/app/services/sentiment_analyzer.py`
5. `python_service/app/services/aspect_analyzer.py`
6. `python_service/app/services/evaluation_service.py`


## 5. 推荐模型方案

### 5.1 模型选择原则

建议先使用本地可部署的中文 Transformer 分类模型，而不是直接依赖外部大模型接口。原因：

1. 当前架构本身就是 Python 微服务，适合本地推理
2. 成本稳定
3. 推理延迟可控
4. 后续可做领域微调

### 5.2 推荐模型路线

#### 路线 A：先上线可用版本，优先推荐

使用 HuggingFace 中文情感分类模型做零样本替换或轻量微调。

推荐基础能力要求：

1. 中文 RoBERTa / MacBERT / BERT 系列
2. 支持三分类或五分类输出
3. 可导出 softmax 概率

建议工程上抽象成“模型注册表”，而不是把模型名写死到业务逻辑里。

#### 路线 B：效果进一步提升

在路线 A 基础上做 B 站领域微调：

1. 用 1000-3000 条小型人工标注集做微调
2. 同时区分 `comment` 与 `danmaku`
3. aspect 任务单独训练或做 pair classification

### 5.3 模型任务划分

最终推荐的任务不是一个模型包打天下，而是分成两类：

1. 主情感分类模型
   输入：文本
   输出：主标签、强度、置信度、概率分布

2. aspect 情感判别模型
   输入：`aspect + 文本`
   输出：该 aspect 的 `POSITIVE / NEUTRAL / NEGATIVE`


## 6. 新的数据结构设计

### 6.1 主情感输出结构

推荐统一返回结构：

```python
{
    "label": "NEGATIVE",
    "score": -0.82,
    "confidence": 0.91,
    "intensity": "STRONG",
    "emotion_tags": ["complaint", "sarcasm"],
    "raw_probs": {
        "positive": 0.03,
        "neutral": 0.06,
        "negative": 0.91
    },
    "source": "transformer_comment_v1",
    "version": "comment-roberta-v1.0.0"
}
```

字段含义：

1. `label`: 主标签，兼容现有业务
2. `score`: 建议改为 `[-1, 1]`，负值表示负面，正值表示正面
3. `confidence`: 模型置信度，取最大类别概率或经校正后的可信度
4. `intensity`: 情感强度，如 `WEAK / MEDIUM / STRONG`
5. `emotion_tags`: 扩展情绪标签，如 `sarcasm`、`praise`、`complaint`
6. `raw_probs`: 原始概率分布，便于调试
7. `source`: 当前分析来源
8. `version`: 模型版本

### 6.2 aspect 级输出结构

推荐每条文本支持多个 aspect：

```python
[
    {
        "aspect": "外观",
        "label": "POSITIVE",
        "score": 0.88,
        "confidence": 0.92,
        "source": "aspect-pair-v1"
    },
    {
        "aspect": "续航",
        "label": "NEGATIVE",
        "score": -0.75,
        "confidence": 0.89,
        "source": "aspect-pair-v1"
    }
]
```


## 7. 数据库改造方案

### 7.1 改造原则

数据库改造遵循以下原则：

1. 保留现有 `sentiment_label`，保证 Java 和前端兼容
2. 新增字段承载增强结果
3. 支持旧数据渐进迁移
4. 不立即删除旧 `aspect` 字段，保留兼容期

### 7.2 video_comment 表改造

当前表：

1. `sentiment_score decimal(5,4)`，范围注释为 `0.0000 to 1.0000`
2. `sentiment_label varchar(10)`
3. `aspect varchar(50)`

建议改造后新增字段：

1. `sentiment_confidence decimal(5,4)`
2. `sentiment_intensity varchar(16)`
3. `sentiment_source varchar(64)`
4. `sentiment_version varchar(64)`
5. `emotion_tags_json json`
6. `aspect_details_json json`
7. `normalized_content text`
8. `text_type varchar(16)`，固定为 `comment`

推荐 SQL：

```sql
ALTER TABLE video_comment
    MODIFY COLUMN sentiment_score decimal(6,4) DEFAULT NULL COMMENT '[-1.0000, 1.0000]',
    ADD COLUMN sentiment_confidence decimal(5,4) DEFAULT NULL COMMENT '0.0000 to 1.0000' AFTER sentiment_score,
    ADD COLUMN sentiment_intensity varchar(16) DEFAULT NULL COMMENT 'WEAK / MEDIUM / STRONG' AFTER sentiment_confidence,
    ADD COLUMN sentiment_source varchar(64) DEFAULT NULL COMMENT 'transformer_comment_v1 / fallback_rule_v1' AFTER sentiment_intensity,
    ADD COLUMN sentiment_version varchar(64) DEFAULT NULL COMMENT 'comment-roberta-v1.0.0' AFTER sentiment_source,
    ADD COLUMN emotion_tags_json json DEFAULT NULL COMMENT '["complaint","sarcasm"]' AFTER sentiment_version,
    ADD COLUMN aspect_details_json json DEFAULT NULL COMMENT 'Per-aspect sentiment results' AFTER emotion_tags_json,
    ADD COLUMN normalized_content text DEFAULT NULL COMMENT 'Normalized text used for inference' AFTER content,
    ADD COLUMN text_type varchar(16) NOT NULL DEFAULT 'comment' COMMENT 'comment / danmaku' AFTER gender;
```

### 7.3 video_danmaku 表改造

弹幕也应支持增强情感字段，但不强制 aspect 明细。

推荐 SQL：

```sql
ALTER TABLE video_danmaku
    MODIFY COLUMN sentiment_score decimal(6,4) DEFAULT NULL COMMENT '[-1.0000, 1.0000]',
    ADD COLUMN sentiment_confidence decimal(5,4) DEFAULT NULL COMMENT '0.0000 to 1.0000' AFTER sentiment_score,
    ADD COLUMN sentiment_intensity varchar(16) DEFAULT NULL COMMENT 'WEAK / MEDIUM / STRONG' AFTER sentiment_confidence,
    ADD COLUMN sentiment_source varchar(64) DEFAULT NULL COMMENT 'transformer_danmaku_v1 / fallback_rule_v1' AFTER sentiment_intensity,
    ADD COLUMN sentiment_version varchar(64) DEFAULT NULL COMMENT 'danmaku-roberta-v1.0.0' AFTER sentiment_source,
    ADD COLUMN emotion_tags_json json DEFAULT NULL COMMENT '["sarcasm","mocking"]' AFTER sentiment_version,
    ADD COLUMN normalized_content text DEFAULT NULL COMMENT 'Normalized text used for inference' AFTER content,
    ADD COLUMN text_type varchar(16) NOT NULL DEFAULT 'danmaku' COMMENT 'comment / danmaku' AFTER task_id;
```

### 7.4 sentiment_timeline 表改造

当前 `timeline_json` 和 `aspect_sentiment_json` 仍然可用，但聚合逻辑应更新。

推荐新增：

1. `timeline_version varchar(64)`
2. `aggregation_meta_json json`

推荐 SQL：

```sql
ALTER TABLE sentiment_timeline
    ADD COLUMN timeline_version varchar(64) DEFAULT NULL COMMENT 'timeline-v2' AFTER aspect_sentiment_json,
    ADD COLUMN aggregation_meta_json json DEFAULT NULL COMMENT 'window, weights, filters' AFTER timeline_version;
```

### 7.5 标注数据表

为评估集新增人工标注表：

```sql
CREATE TABLE sentiment_annotation (
    id bigint NOT NULL AUTO_INCREMENT,
    source_table varchar(32) NOT NULL COMMENT 'video_comment / video_danmaku',
    source_id bigint NOT NULL COMMENT 'comment_id / danmaku_id',
    task_id varchar(50) DEFAULT NULL,
    bvid varchar(50) DEFAULT NULL,
    text_type varchar(16) NOT NULL COMMENT 'comment / danmaku',
    raw_text text NOT NULL,
    normalized_text text DEFAULT NULL,
    gold_label varchar(16) NOT NULL COMMENT 'POSITIVE / NEUTRAL / NEGATIVE',
    gold_intensity varchar(16) DEFAULT NULL COMMENT 'WEAK / MEDIUM / STRONG',
    gold_emotion_tags_json json DEFAULT NULL,
    gold_aspect_details_json json DEFAULT NULL,
    annotator varchar(64) DEFAULT NULL,
    notes varchar(255) DEFAULT NULL,
    created_at datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    KEY idx_source (source_table, source_id),
    KEY idx_text_type (text_type),
    KEY idx_gold_label (gold_label)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### 7.6 建议新建迁移脚本

新建文件：

1. `sql/migrations/2026-03-transformer-sentiment-upgrade.sql`

该脚本应包含：

1. `ALTER TABLE video_comment`
2. `ALTER TABLE video_danmaku`
3. `ALTER TABLE sentiment_timeline`
4. `CREATE TABLE sentiment_annotation`
5. 必要索引


## 8. Python 依赖改造

### 8.1 requirements.txt 增加依赖

当前 `python_service/requirements.txt` 缺少 Transformer 相关包。

建议新增：

```txt
transformers
torch
sentencepiece
accelerate
pyyaml
scikit-learn
pandas
tqdm
onnxruntime
```

说明：

1. `transformers`: 模型加载与推理
2. `torch`: 推理后端
3. `sentencepiece`: 部分中文模型需要
4. `accelerate`: 推理与后续微调扩展
5. `pyyaml`: 规则词典配置
6. `scikit-learn`: 评估指标
7. `pandas`: 数据集处理
8. `tqdm`: 评估脚本进度条
9. `onnxruntime`: 后续优化可选


## 9. Python 模块设计

### 9.1 新增模块清单

建议新增以下文件：

1. `python_service/app/services/text_normalizer.py`
2. `python_service/app/services/domain_rules.py`
3. `python_service/app/services/model_registry.py`
4. `python_service/app/services/sentiment_analyzer.py`
5. `python_service/app/services/aspect_analyzer.py`
6. `python_service/app/services/evaluation_service.py`
7. `python_service/app/resources/domain_lexicon.yml`
8. `python_service/scripts/eval/build_annotation_dataset.py`
9. `python_service/scripts/eval/run_sentiment_eval.py`
10. `python_service/scripts/eval/export_low_confidence_samples.py`
11. `python_service/scripts/migrate/recompute_sentiment_for_task.py`
12. `python_service/scripts/migrate/backfill_transformer_sentiment.py`


## 10. 文本标准化模块

### 10.1 文件

`python_service/app/services/text_normalizer.py`

### 10.2 目标

负责对评论和弹幕做统一清洗与轻量标准化，为 Transformer 和规则层提供稳定输入。

### 10.3 规则

建议实现以下处理：

1. 去除首尾空白
2. 连续空白压缩
3. 重复标点压缩，但保留情绪强度信息
4. 表情与颜文字保留为特殊 token
5. 常见网络语映射
6. 重复字符压缩，但不过度清洗

### 10.4 示例代码骨架

```python
import re
from dataclasses import dataclass


@dataclass
class NormalizedText:
    raw_text: str
    normalized_text: str
    features: dict


class TextNormalizer:
    def normalize(self, text: str, text_type: str) -> NormalizedText:
        raw = text or ""
        t = raw.strip()
        t = re.sub(r"\s+", " ", t)

        features = {
            "has_question_mark": "?" in t or "？" in t,
            "has_exclaim_mark": "!" in t or "！" in t,
            "length": len(t)
        }

        # 压缩重复标点，但记录强度
        t = re.sub(r"[!！]{2,}", "！！", t)
        t = re.sub(r"[?？]{2,}", "？？", t)

        return NormalizedText(
            raw_text=raw,
            normalized_text=t,
            features=features
        )
```


## 11. 领域规则模块

### 11.1 文件

`python_service/app/services/domain_rules.py`

### 11.2 目标

对模型结果做“微调和纠偏”，不替代模型。

### 11.3 规则词典文件

新增：

`python_service/app/resources/domain_lexicon.yml`

示例：

```yaml
positive:
  - 真香
  - 上头
  - 神作
  - 牛
  - 好看
negative:
  - 逆天
  - 无语
  - 拉胯
  - 烂
  - 失望
sarcasm:
  - 笑死
  - 绝了
  - 你是懂
  - 太会了
negation:
  - 不
  - 没
  - 无
  - 别
intensifiers:
  - 太
  - 巨
  - 非常
  - 真
  - 好
```

### 11.4 规则模块职责

1. 识别否定词反转
2. 识别常见反讽标记
3. 强化高频网络语
4. 生成 `emotion_tags`
5. 对低置信度样本做小范围纠偏

### 11.5 规则执行原则

1. 仅在高确定性规则触发时改标签
2. 默认不推翻高置信度模型结果
3. 对中低置信度样本优先生效


## 12. 模型注册表模块

### 12.1 文件

`python_service/app/services/model_registry.py`

### 12.2 目标

统一管理评论模型和弹幕模型，避免业务代码直接依赖具体模型名称。

### 12.3 示例代码骨架

```python
from dataclasses import dataclass


@dataclass
class ModelConfig:
    model_name: str
    version: str
    max_length: int
    label_mapping: dict


class ModelRegistry:
    COMMENT_MODEL = ModelConfig(
        model_name="local/comment-roberta-v1",
        version="comment-roberta-v1.0.0",
        max_length=256,
        label_mapping={0: "NEGATIVE", 1: "NEUTRAL", 2: "POSITIVE"}
    )

    DANMAKU_MODEL = ModelConfig(
        model_name="local/danmaku-roberta-v1",
        version="danmaku-roberta-v1.0.0",
        max_length=96,
        label_mapping={0: "NEGATIVE", 1: "NEUTRAL", 2: "POSITIVE"}
    )
```


## 13. 主情感分析模块

### 13.1 文件

`python_service/app/services/sentiment_analyzer.py`

### 13.2 目标

负责：

1. 加载 Transformer 模型
2. 对评论和弹幕分流
3. 输出主标签、分数、置信度、强度、来源、版本
4. 调用规则层修正结果

### 13.3 推荐接口

```python
class SentimentAnalyzer:
    def analyze(self, text: str, text_type: str = "comment") -> dict:
        ...
```

### 13.4 分数映射方案

建议不要继续使用 `0-1` 的“类情感分”，而是改成 `[-1, 1]`：

```python
score = positive_prob - negative_prob
```

这样更适合：

1. 时间轴可视化
2. 聚合统计
3. 强度区分

### 13.5 强度划分建议

```python
abs_score = abs(score)
if abs_score >= 0.75:
    intensity = "STRONG"
elif abs_score >= 0.4:
    intensity = "MEDIUM"
else:
    intensity = "WEAK"
```

### 13.6 低置信度处理

建议：

1. 如果最大概率 `< 0.55`，标记为低置信度
2. 低置信度时允许规则层辅助
3. 若仍不确定，可保留主标签但记录低可信

### 13.7 示例代码骨架

```python
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

from .text_normalizer import TextNormalizer
from .domain_rules import DomainRuleEngine
from .model_registry import ModelRegistry


class SentimentAnalyzer:
    def __init__(self):
        self.normalizer = TextNormalizer()
        self.rule_engine = DomainRuleEngine()
        self._tokenizers = {}
        self._models = {}

    def _load_model(self, text_type: str):
        cfg = ModelRegistry.COMMENT_MODEL if text_type == "comment" else ModelRegistry.DANMAKU_MODEL
        if cfg.model_name not in self._models:
            self._tokenizers[cfg.model_name] = AutoTokenizer.from_pretrained(cfg.model_name)
            self._models[cfg.model_name] = AutoModelForSequenceClassification.from_pretrained(cfg.model_name)
            self._models[cfg.model_name].eval()
        return cfg, self._tokenizers[cfg.model_name], self._models[cfg.model_name]

    def analyze(self, text: str, text_type: str = "comment") -> dict:
        normalized = self.normalizer.normalize(text, text_type)
        cfg, tokenizer, model = self._load_model(text_type)

        inputs = tokenizer(
            normalized.normalized_text,
            return_tensors="pt",
            truncation=True,
            max_length=cfg.max_length
        )

        with torch.no_grad():
            logits = model(**inputs).logits
            probs = torch.softmax(logits, dim=-1).squeeze().tolist()

        label_probs = {
            cfg.label_mapping[i]: float(probs[i])
            for i in range(len(probs))
        }

        label = max(label_probs, key=label_probs.get)
        confidence = label_probs[label]
        score = label_probs.get("POSITIVE", 0.0) - label_probs.get("NEGATIVE", 0.0)

        result = {
            "label": label,
            "score": round(score, 4),
            "confidence": round(confidence, 4),
            "source": f"transformer_{text_type}_v1",
            "version": cfg.version,
            "raw_probs": label_probs,
            "normalized_text": normalized.normalized_text
        }

        result = self.rule_engine.apply(result, normalized, text_type=text_type)
        return result
```


## 14. Aspect 分析模块

### 14.1 为什么必须升级

当前 `detect_aspect()` 只是关键词命中后返回一个标签，这不是真正的切面情感分析。

示例：

`“外观很好看，但是续航太拉了”`

当前实现通常只能返回一个 aspect，且只能给整句一个情感判断，这是不符合业务需求的。

### 14.2 目标设计

aspect 分析分两步：

1. aspect 候选召回
2. 针对每个 aspect 进行情感判别

### 14.3 aspect 候选召回

仍然可以保留关键词召回作为第一阶段，但不再把关键词命中直接当最终结果。

建议改造为：

1. aspect 词典维护在配置中
2. 一条文本可召回多个 aspect
3. 召回阶段只负责发现候选，不负责给情感

### 14.4 针对 aspect 的情感二次判别

采用 pair classification 输入格式：

```text
[CLS] 外观 [SEP] 外观很好看，但是续航太拉了
```

和

```text
[CLS] 续航 [SEP] 外观很好看，但是续航太拉了
```

分别输出情感标签。

### 14.5 文件

`python_service/app/services/aspect_analyzer.py`

### 14.6 示例代码骨架

```python
class AspectAnalyzer:
    def __init__(self, sentiment_analyzer):
        self.sentiment_analyzer = sentiment_analyzer
        self.aspect_keywords = {
            "外观": ["外观", "颜值", "设计", "配色"],
            "性能": ["性能", "流畅", "卡", "帧率"],
            "价格": ["价格", "贵", "便宜", "性价比"],
            "续航": ["续航", "电池", "耗电", "充电"]
        }

    def recall_aspects(self, text: str) -> list:
        hit = []
        for aspect, keywords in self.aspect_keywords.items():
            if any(keyword in text for keyword in keywords):
                hit.append(aspect)
        return hit

    def analyze(self, text: str, text_type: str = "comment") -> list:
        aspects = self.recall_aspects(text)
        if not aspects:
            return []

        results = []
        for aspect in aspects:
            pair_text = f"{aspect} [SEP] {text}"
            pair_result = self.sentiment_analyzer.analyze(pair_text, text_type=text_type)
            results.append({
                "aspect": aspect,
                "label": pair_result["label"],
                "score": pair_result["score"],
                "confidence": pair_result["confidence"],
                "source": pair_result["source"],
                "version": pair_result["version"]
            })
        return results
```

### 14.7 兼容现有 aspect 字段

由于当前 `video_comment` 只有一个 `aspect` 字段，建议兼容期策略：

1. `aspect_details_json` 存完整多 aspect 结果
2. `aspect` 保留“主 aspect”，用于兼容老接口

主 aspect 选择策略：

1. 置信度最高的 aspect
2. 若置信度相同，按规则优先级


## 15. 改造 video_storage_service.py

### 15.1 当前需要替换的职责

当前 `VideoStorageService` 里耦合了：

1. 数据库存取
2. 主情感分析
3. aspect 检测
4. 时间轴聚合

建议保留其“存储服务”定位，把分析逻辑外移到新模块。

### 15.2 推荐重构方式

在 `VideoStorageService.__init__()` 中注入：

1. `SentimentAnalyzer`
2. `AspectAnalyzer`

示例：

```python
from .sentiment_analyzer import SentimentAnalyzer
from .aspect_analyzer import AspectAnalyzer


class VideoStorageService:
    def __init__(self):
        ...
        self.sentiment_analyzer = SentimentAnalyzer()
        self.aspect_analyzer = AspectAnalyzer(self.sentiment_analyzer)
```

### 15.3 评论保存逻辑改造

当前 `save_comments()` 中每条评论只写：

1. `sentiment_score`
2. `sentiment_label`
3. `aspect`

升级后每条评论应写：

1. `normalized_content`
2. `sentiment_score`
3. `sentiment_label`
4. `sentiment_confidence`
5. `sentiment_intensity`
6. `sentiment_source`
7. `sentiment_version`
8. `emotion_tags_json`
9. `aspect`
10. `aspect_details_json`
11. `text_type='comment'`

### 15.4 评论保存伪代码

```python
sentiment = self.sentiment_analyzer.analyze(content, text_type="comment")
aspect_details = self.aspect_analyzer.analyze(content, text_type="comment")

primary_aspect = aspect_details[0]["aspect"] if aspect_details else None
emotion_tags_json = json.dumps(sentiment.get("emotion_tags", []), ensure_ascii=False)
aspect_details_json = json.dumps(aspect_details, ensure_ascii=False) if aspect_details else None
```

### 15.5 弹幕保存逻辑改造

弹幕默认只做主情感分析，不强制做 aspect 细分。
如果后续需要，也可以对含有明显 aspect 关键词的弹幕做 aspect 辅助分析，但第一阶段不建议增加太多复杂度。

写入字段：

1. `normalized_content`
2. `sentiment_score`
3. `sentiment_label`
4. `sentiment_confidence`
5. `sentiment_intensity`
6. `sentiment_source`
7. `sentiment_version`
8. `emotion_tags_json`
9. `text_type='danmaku'`

### 15.6 时间轴生成逻辑改造

当前时间轴按 `AVG(sentiment_score)` 聚合，旧分数范围为 `0-1`。

升级后分数范围改为 `[-1, 1]`，聚合逻辑建议：

1. 对低置信度样本降权
2. 对高强度样本适度加权

推荐 SQL 不再直接使用简单平均，而在 Python 层先计算后批量落库，或者将 `weighted_score` 预写入表。

建议权重：

```text
weight = sentiment_confidence
```

若要进一步增强：

```text
weight = sentiment_confidence * intensity_weight
```

其中：

1. `WEAK = 0.8`
2. `MEDIUM = 1.0`
3. `STRONG = 1.1`

### 15.7 aspect 聚合逻辑改造

不要再只依据 `video_comment.aspect` 聚合，应优先读取 `aspect_details_json`。

示例聚合后结构：

```json
{
  "外观": {
    "score": 0.72,
    "count": 138,
    "positive": 96,
    "neutral": 20,
    "negative": 22
  },
  "续航": {
    "score": -0.41,
    "count": 93,
    "positive": 14,
    "neutral": 18,
    "negative": 61
  }
}
```


## 16. Python Router 与任务流改造

### 16.1 `analysis.py` 改造点

文件：

`python_service/app/routers/analysis.py`

当前任务流不需要大改，但需要做以下增强：

1. 在任务日志中输出模型版本
2. 支持“重新计算情感”模式
3. 为未来回填脚本复用分析能力

建议扩展请求模型：

```python
class AnalyzeVideoRequest(BaseModel):
    bvid: str
    max_comments: int = 500
    sessdata: Optional[str] = None
    task_id: Optional[str] = None
    sentiment_version: Optional[str] = None
    force_recompute_sentiment: bool = False
```


## 17. 评估与标注脚本设计

### 17.1 为什么必须加评估集

如果没有人工标注集，就无法回答下面的问题：

1. 新模型是否真的更好
2. 哪类样本仍然错得多
3. 评论和弹幕是否需要不同模型
4. 规则层是否在帮忙还是在添乱

### 17.2 建议最小评估集规模

第一版最少：

1. 评论 400 条
2. 弹幕 300 条
3. 多切面评论 150 条
4. 反讽/模糊样本 150 条

推荐总量：1000 条左右

### 17.3 标注规范建议

主情感：

1. `POSITIVE`
2. `NEUTRAL`
3. `NEGATIVE`

强度：

1. `WEAK`
2. `MEDIUM`
3. `STRONG`

emotion tags：

1. `praise`
2. `complaint`
3. `sarcasm`
4. `mocking`
5. `surprise`
6. `disappointment`

aspect 细节：

按 JSON 标注。

### 17.4 评估脚本 1：构建标注候选集

文件：

`python_service/scripts/eval/build_annotation_dataset.py`

职责：

1. 从 `video_comment` / `video_danmaku` 抽样
2. 优先抽高互动、高争议、低置信度样本
3. 导出 CSV 给人工标注

建议抽样逻辑：

1. 高点赞评论
2. 低置信度评论
3. 负面预测评论
4. 包含 aspect 关键词评论
5. 热门任务中的弹幕

### 17.5 评估脚本 2：运行离线评估

文件：

`python_service/scripts/eval/run_sentiment_eval.py`

职责：

1. 读取 `sentiment_annotation`
2. 调用新模型预测
3. 计算：
   1. accuracy
   2. precision / recall / f1
   3. 负面类别 recall
   4. 评论与弹幕分开统计
   5. aspect 级准确率

建议输出：

1. 控制台摘要
2. `reports/sentiment_eval_YYYYMMDD.json`
3. `reports/sentiment_eval_YYYYMMDD.md`

### 17.6 评估脚本 3：导出低置信度样本

文件：

`python_service/scripts/eval/export_low_confidence_samples.py`

职责：

1. 从生产数据中导出低置信度样本
2. 供人工二次标注
3. 形成持续回流闭环


## 18. 数据回填与迁移脚本

### 18.1 回填需求

数据库升级后，旧数据仍然只有 `SnowNLP` 结果。
因此必须有离线回填脚本。

### 18.2 脚本 1：按任务重算

文件：

`python_service/scripts/migrate/recompute_sentiment_for_task.py`

输入：

1. `task_id`

职责：

1. 查询该任务下所有评论和弹幕
2. 用新模型重新计算情感
3. 回写新增字段
4. 重建时间轴和 aspect 聚合

适用场景：

1. 单任务修复
2. 开发测试

### 18.3 脚本 2：批量回填

文件：

`python_service/scripts/migrate/backfill_transformer_sentiment.py`

职责：

1. 按时间范围或任务状态筛选历史任务
2. 分批回填
3. 记录每批次进度和失败样本

建议支持参数：

1. `--date-from`
2. `--date-to`
3. `--limit`
4. `--only-completed`
5. `--dry-run`


## 19. Java 层兼容策略

### 19.1 保持接口兼容

Java 目前主要消费这些字段：

1. `sentiment_label`
2. `sentiment_score`
3. `aspect`
4. `timeline_json`
5. `aspect_sentiment_json`

因此升级第一阶段可不强制修改 Java API 契约，只需：

1. 让旧字段继续存在
2. 扩展实体与 Mapper 支持新增字段

### 19.2 推荐 Java 实体扩展

建议扩展：

1. `VideoComment`
2. `VideoDanmaku`
3. `SentimentTimeline`

新增字段建议：

1. `sentimentConfidence`
2. `sentimentIntensity`
3. `sentimentSource`
4. `sentimentVersion`
5. `emotionTagsJson`
6. `aspectDetailsJson`

### 19.3 Mapper 扩展

建议更新：

1. `src/main/resources/com/ecut/bili_insight/mapper/VideoCommentMapper.xml`
2. `src/main/resources/com/ecut/bili_insight/mapper/VideoDanmakuMapper.xml`
3. `src/main/resources/com/ecut/bili_insight/mapper/SentimentTimelineMapper.xml`

原则：

1. 老查询继续可用
2. 新字段逐步透出到前端


## 20. 前端兼容与展示建议

### 20.1 第一阶段不强依赖前端大改

第一阶段前端只需继续使用：

1. `sentimentLabel`
2. `sentimentScore`
3. `aspect`

即可获得一定提升。

### 20.2 第二阶段建议展示增强字段

后续可在前端逐步展示：

1. 置信度
2. 强度
3. emotion tags
4. 多 aspect 情感结果

例如在评论卡片中新增：

1. “强负面 / 中负面 / 弱正面”
2. “讽刺 / 抱怨 / 夸赞”标签
3. “外观: 正面, 续航: 负面”子标签


## 21. 实施顺序

### 阶段 1：最小可用版

目标：快速替换 `SnowNLP`

实施项：

1. 增加 Transformer 依赖
2. 新增 `TextNormalizer`
3. 新增 `SentimentAnalyzer`
4. 增加规则纠偏
5. 评论/弹幕分流
6. 增加数据库字段
7. 更新 `save_comments()` 与 `save_danmakus()`

验收标准：

1. 能完整跑通单任务分析
2. 新结果落库
3. 主标签明显优于旧方案

### 阶段 2：切面升级版

目标：真正实现多切面情感分析

实施项：

1. 新增 `AspectAnalyzer`
2. 增加 `aspect_details_json`
3. 改造 `generate_sentiment_timeline()`
4. 聚合 aspect 级统计

验收标准：

1. 一条评论支持多个 aspect
2. 前后端仍兼容

### 阶段 3：评估闭环版

目标：具备持续优化能力

实施项：

1. 建标注表
2. 导出候选样本
3. 建立评估脚本
4. 导出低置信度样本回流

验收标准：

1. 可量化对比模型效果
2. 能识别主要错误类别


## 22. 风险与缓解措施

### 22.1 推理速度风险

问题：

1. Transformer 推理比 `SnowNLP` 慢

缓解：

1. 单例加载模型，避免重复初始化
2. 批处理评论和弹幕
3. 限制 `max_length`
4. 后续引入 `onnxruntime`

### 22.2 内存占用风险

问题：

1. 同时加载评论模型和弹幕模型可能增加内存压力

缓解：

1. 若初期资源有限，可先共享同一模型，不同阈值与规则分流
2. 后续再分离成两个模型

### 22.3 旧数据兼容风险

问题：

1. 历史任务数据结构与新结构不一致

缓解：

1. 旧字段保留
2. 提供离线回填脚本
3. 前端优先使用新字段，缺失时回退旧字段

### 22.4 规则层过拟合风险

问题：

1. 规则写太重可能让系统变脆

缓解：

1. 规则只对中低置信度样本生效
2. 规则变更纳入离线评估


## 23. 预期效果

在当前项目场景下，本方案通常能获得以下改善：

1. 主情感准确率提升 15%-35%
2. 负面样本召回提升 25%-50%
3. 转折句、多切面句识别显著提升
4. 弹幕误判率明显下降，但弹幕仍会比评论难
5. 可解释性大幅提升

注意：

1. 没有领域微调时，效果提升主要来自更强模型和规则层
2. 做完小型标注集与微调后，效果会再进一步


## 24. 最终落地建议

针对 Bili-Insight，推荐的最终实施结论如下：

1. 必须彻底移除 `SnowNLP` 主分析职责
2. 先上本地 Transformer 推理，不要继续修补旧阈值方案
3. 评论和弹幕必须分流
4. `aspect` 必须升级为“召回 + 面向 aspect 的情感判别”
5. 新字段必须包括 `confidence / source / version`
6. 必须建立小型人工标注集与离线评估脚本

这样做的结果不是“临时修补”，而是把情感分析能力升级成可持续迭代的正式模块。


## 25. 推荐实施文件清单

### 25.1 新增文件

1. `docs/transformer_sentiment_upgrade_plan.md`
2. `sql/migrations/2026-03-transformer-sentiment-upgrade.sql`
3. `python_service/app/services/text_normalizer.py`
4. `python_service/app/services/domain_rules.py`
5. `python_service/app/services/model_registry.py`
6. `python_service/app/services/sentiment_analyzer.py`
7. `python_service/app/services/aspect_analyzer.py`
8. `python_service/app/services/evaluation_service.py`
9. `python_service/app/resources/domain_lexicon.yml`
10. `python_service/scripts/eval/build_annotation_dataset.py`
11. `python_service/scripts/eval/run_sentiment_eval.py`
12. `python_service/scripts/eval/export_low_confidence_samples.py`
13. `python_service/scripts/migrate/recompute_sentiment_for_task.py`
14. `python_service/scripts/migrate/backfill_transformer_sentiment.py`

### 25.2 修改文件

1. `python_service/requirements.txt`
2. `python_service/app/services/video_storage_service.py`
3. `python_service/app/routers/analysis.py`
4. `sql/bili_insight_db.sql`
5. `src/main/java/com/ecut/bili_insight/entity/VideoComment.java`
6. `src/main/java/com/ecut/bili_insight/entity/VideoDanmaku.java`
7. `src/main/resources/com/ecut/bili_insight/mapper/VideoCommentMapper.xml`
8. `src/main/resources/com/ecut/bili_insight/mapper/VideoDanmakuMapper.xml`
9. `src/main/resources/com/ecut/bili_insight/mapper/SentimentTimelineMapper.xml`


## 26. 后续建议

本文档是完整改造蓝图。建议实施时严格按以下顺序推进：

1. 先完成数据库迁移与 Python 模块接入
2. 再做任务级回归测试
3. 再补评估集和离线评估
4. 最后再逐步把新增字段暴露给 Java 和前端

不要反过来先改前端展示，否则会在数据层尚未稳定时扩大改动面。
