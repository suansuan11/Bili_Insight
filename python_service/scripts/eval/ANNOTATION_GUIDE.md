# Bili-Insight 情感标注规范

## 主情感 gold_label

只填写三类之一：

- `POSITIVE`：明确称赞、喜欢、推荐、感动、期待、正向调侃。
- `NEUTRAL`：提问、事实陈述、前排打卡、省流、无明显态度、语义不足。
- `NEGATIVE`：明确吐槽、失望、避雷、反讽、抱怨、质量/价格/体验负向评价。

优先按“整条文本最终态度”标注。转折句通常以后半句为准，例如“前面还行但是后面太水了”标 `NEGATIVE`。

## 强度 gold_intensity

可留空；如填写，只填：

- `WEAK`：轻微倾向，例如“还行”“一般”。
- `MEDIUM`：明确态度，例如“好看”“难用”。
- `STRONG`：强烈态度，例如“封神”“避雷”“垃圾”。

## 情绪标签 gold_emotion_tags

可留空。填写时用 JSON 数组或逗号分隔均可：

```json
["praise", "moved"]
```

常用值：`praise`、`complaint`、`sarcasm`、`amused`、`moved`、`disappointment`、`surprised`。

## 切面 gold_aspect_details

第一轮可留空。若填写，用 JSON 数组：

```json
[
  {"aspect": "剪辑", "label": "NEGATIVE"},
  {"aspect": "配乐", "label": "POSITIVE"}
]
```

切面标签同样只用 `POSITIVE`、`NEUTRAL`、`NEGATIVE`。

## 质量控制

- 不确定样本优先标 `NEUTRAL`，并在 `notes` 写原因。
- 梗、反讽如果明显表达嘲讽，标 `NEGATIVE` 并可加 `sarcasm`。
- 单纯表情、无语义占位、提问求助一般标 `NEUTRAL`。
- 建议至少两名标注者交叉复核 100 条，先统一口径再批量标注。
