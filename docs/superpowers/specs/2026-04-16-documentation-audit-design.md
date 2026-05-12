文档审计设计 — Bili_Insight

概述
本文件定义对仓库中项目文档进行快速审计的目标、范围、方法与产物。目标是识别哪些文档需要更新、给出具体修改建议并按优先级排序，便于后续由维护者或我方做最小修复。

审计目标
- 判定 README、docs、以及与运行/启动相关配置文件是否与源码一致
- 识别阻止本地运行或部署的文档错误（High）
- 为常见操作（启动 Java 后端、启动 python_service、前端开发运行）提供明确、可复制的步骤建议

检查范围
- 根目录 README* 文件
- docs/ 下的关键文档（尤其是 transformer_sentiment_upgrade_plan.md、项目技术文档.md）
- python_service 相关文档与启动脚本：python_service/.env、python_service/start_service.sh、python_service/app/config.py
- 后端配置：src/main/resources/application.yml、StartupDataInitializer.java
- 前端文档与配置：bili-insight-frontend/README.md、vite.config.ts
- bilibili-api/docs （检查与后端或 python_service 使用的接口是否一致）

方法与产物
- 对每个检查文件输出：现状描述、是否过时、问题类别、具体修改建议、优先级
- 产物：
  - docs/superpowers/specs/YYYY-MM-DD-documentation-audit-design.md（本文件）
  - docs/superpowers/specs/YYYY-MM-DD-documentation-audit-report.md（审计报告）

时间估计
- 预计 15–45 分钟完成快速审计并生成报告

验收标准
- 报告应能让维护者直接复制/粘贴建议更新文档或授权我做最小修复
