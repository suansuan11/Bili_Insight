# Gemini 审核提示词：Bili-Insight 定向扩充标注集

请审核我上传的 `targeted_expansion_prelabeled.csv`。这是为了补齐 Bili-Insight 情感分析数据集中 `NEGATIVE` 和 `POSITIVE` 样本不足的问题而定向抽取的 400 条 Bilibili 评论/弹幕。

你的任务是审核并修正 CSV 中已有的 AI 预标注。不要新增、删除、重排行，不要改变列名和列顺序。

## 需要重点审核/修改的列

- `gold_label`
- `gold_intensity`
- `gold_emotion_tags`
- `gold_aspect_details`
- `annotator`
- `notes`

## 必须保持不变的列

- `source_table`
- `source_id`
- `task_id`
- `bvid`
- `text_type`
- `raw_text`
- `normalized_text`
- `model_label`
- `model_score`
- `model_confidence`

## gold_label 规则

只能填写：

- `POSITIVE`
- `NEUTRAL`
- `NEGATIVE`

判断标准：

- `POSITIVE`：明确称赞、喜欢、推荐、支持、期待、认可、感动、正向玩梗。
- `NEUTRAL`：提问、事实陈述、配置/抽卡/站位咨询、打卡、前排、省流、无明显态度、信息不足。
- `NEGATIVE`：明确吐槽、失望、抱怨、避雷、嘲讽、反讽、质量差、体验差、价格贵、标题党、硬广、攻击性负面表达。

转折句通常以后半句为主：

- “前面还行但是后面太水了” -> `NEGATIVE`
- “价格有点贵，但是质量不错” -> 视整体语气标 `POSITIVE` 或 `NEUTRAL`

## B 站语境

- “前排”“打卡”“来了”“省流”“插眼”通常为 `NEUTRAL`。
- “哈哈”“笑死”不一定负面，要看是否嘲讽。
- “就这？”“这也叫？”“真有你的”“你是懂的”通常偏 `NEGATIVE`，可加 `sarcasm`。
- “牛”“封神”“好看”“舒服”“泪目”“吹爆”通常偏 `POSITIVE`。
- 单纯提问、求配队、问配置、问抽卡建议，通常 `NEUTRAL`。
- “差评”“看不下去”“尴尬”“难用”“不推荐”“避雷”“标题党”“硬广”“割韭菜”通常 `NEGATIVE`。

## gold_intensity

只能填写：

- `WEAK`
- `MEDIUM`
- `STRONG`

建议：

- `WEAK`：轻微倾向，如“还行”“一般”“有点贵”。
- `MEDIUM`：明确态度，如“好看”“难用”“不推荐”。
- `STRONG`：强烈态度，如“封神”“垃圾”“避雷”“太烂了”“看不下去”。

## gold_emotion_tags

填写合法 JSON 数组字符串。没有明显情绪时填 `[]`。

可用标签：

- `praise`
- `complaint`
- `sarcasm`
- `amused`
- `moved`
- `disappointment`
- `surprised`

示例：

```json
["praise"]
```

```json
["complaint", "sarcasm"]
```

```json
[]
```

## gold_aspect_details

如果文本没有明确切面，填 `[]`。

如果已有内容不合理，请修正或清空为 `[]`。

格式必须是合法 JSON 数组字符串：

```json
[{"aspect": "剪辑", "label": "NEGATIVE"}]
```

常用切面：

- `整体`
- `内容`
- `情绪`
- `互动`
- `表演`
- `剪辑`
- `画面`
- `配乐`
- `主播`
- `剧情`
- `专业度`
- `标题封面`
- `商业化`
- `性能`
- `价格`
- `系统`
- `玩法`
- `优化`
- `氪金`

## annotator 和 notes

把所有已审核行的 `annotator` 改为：

```text
gemini_reviewed
```

在 `notes` 末尾追加：

```text
gemini_reviewed=true
```

如果修改了原来的 `gold_label`，再追加：

```text
label_corrected=true
```

如果没有修改原来的 `gold_label`，追加：

```text
label_corrected=false
```

## 输出要求

1. 输出完整 CSV 内容。
2. 保持原始列名和列顺序。
3. 不要输出 Markdown 表格。
4. 不要解释每一行。
5. 不要省略任何行。
6. 确保结果可以被 Python `csv.DictReader` 正确读取。
7. 所有 JSON 字段必须是合法 JSON 字符串。
