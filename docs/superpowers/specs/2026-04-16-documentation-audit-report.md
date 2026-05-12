项目文档快速审计报告 — 2026-04-16

执行摘要
- 范围：仓库根、docs/、python_service、后端配置（application.yml）、前端（bili-insight-frontend）及关键启动脚本与调度代码。基于最近提交（2026-03~04、2026-04 中有多次模型与前端改动）。
- 结论（优先级统计）：
  - High: 3 项（硬编码凭据 / secrets、Python 服务自动启动与启动命令说明不一致、README 缺少端到端运行步骤）
  - Medium: 4 项（.env 示例缺失、前端代理说明不够详细、docs/transformer 升级计划缺少执行命令示例、AGENTS.md 中的注意项需同步）
  - Low: 若干（可改进的表达与示例代码片段）

主要高优先级问题概要（需要立刻关注）
1) 敏感信息硬编码（High）
   - 文件：src/main/resources/application.yml, python_service/.env
   - 问题：application.yml 中存在默认 DB 密码（DB_PASSWORD: Liuyi325）、JWT 秘钥、默认 python api key 等；python_service/.env 中也包含 DB_PASSWORD 与 API_KEY。这些文件作为仓库默认配置不应包含真实凭据。
   - 建议：把这些值替换为占位符/环境变量引用，并在仓库根添加或更新 .gitignore 与 docs 提示。提供 .env.example 并将真实 .env 从版本控制中移除（若已提交，考虑变更历史处理）。

2) Java 启动器会尝试自动拉起 Python 服务且启动命令在 docs 与配置中不一致（High）
   - 文件：src/main/java/com/ecut/bili_insight/task/StartupDataInitializer.java, src/main/resources/application.yml, python_service/start_service.sh
   - 问题：StartupDataInitializer 会在 Java 启动时自动尝试拉起 Python 服务（如果 health 不通），但 application.yml 默认的 python.service.start-command 指向 .venv/bin/uvicorn（AGENTS.md 提示仓库中存在 python_service/venv，而 application.yml 使用 .venv）。这可能导致自动启动失败或误拉起错误环境。
   - 建议：在 README 与 docs 中明确描述 Java 自动启动 Python 的行为与风险（如何禁用 / 如何配置 python.service.start-command）；推荐把 start-command 设为注释示例或明确使用 python_service/start_service.sh。并在 application.yml 中说明默认值仅用于本地开发，生产必须覆盖。

3) 根 README 缺少端到端快速运行步骤（High）
   - 文件：仓库根 README 缺失（未检测到 README.md），仅有子模块 README（前端）和 docs/ 文档。
   - 问题：没有集中、简洁的“如何在开发机上跑通整个系统”说明；对新加入的贡献者或本地试用者不友好。
   - 建议：新增仓库根 README.md，包含：依赖（MySQL）、数据库初始化（sql/bili_insight_db.sql）、python_service 启动（.env 示例、venv、uvicorn 命令）、Java 后端运行（mvn spring-boot:run）、前端运行（npm install && npm run dev）、以及如何禁用 Java 自动启动 Python 的说明。

逐文件审计要点（按优先级排序）

1) src/main/resources/application.yml
   - 现状：包含开发默认值：DB_PASSWORD、JWT_SECRET、PYTHON_API_KEY、python.service.start-command 指向 .venv/bin/uvicorn。
   - 问题：包含真实样例密码，重复的 long JDBC query 参数串，start-command 默认值可能与仓库的 venv 路径不一致。
   - 影响：泄露凭据风险；新环境可能因路径不一致而无法自动启动 Python 服务。
   - 建议修改（High）：
     - 将密码与密钥替换为占位符或引用环境变量。例如：
       - password: ${DB_PASSWORD:change_me}
       - jwt.secret: ${JWT_SECRET:change_me}
       - python.service.start-command: ${PYTHON_START_CMD:}
     - 在 README 或 docs 中增加说明：必须通过环境变量覆盖这些值；不要在公共仓库提交真实凭据。

2) python_service/.env
   - 现状：包含 DB_PASSWORD、API_KEY、模型路径等设置。
   - 问题：真实密码与 API_KEY 被提交到仓库（High）。没有 .env.example 做为安全模板（Medium）。
   - 建议：
     - 移除真实凭据并将 .env 加入 .gitignore（如果尚未）。添加 docs/.env.example 或 python_service/.env.example 并填入占位符。
     - 在 docs 中说明如何生成 venv、如何安装依赖（pip install -r requirements.txt）、如何运行 start_service.sh 或 uvicorn 命令。

3) StartupDataInitializer.java（src/main/java/.../task/StartupDataInitializer.java）
   - 现状：Java 在启动阶段检查 Python 服务健康，不在运行时会尝试用配置的 start-command 启动它；并在 JVM 退出时 kill 子进程。
   - 问题：自动拉起行为未在项目 README 中突出说明，且 start-command 的默认值可能失败（见 application.yml 与现实 venv 目录）。默认自动拉起在开发机有用，但在生产或 CI 环境可能不可取。
   - 建议（High）：
     - 在根 README 中增加“Java 将尝试自动启动 Python 服务”的段落，说明如何禁用（通过 settings 覆盖，或把 python.service.start-command 清空）和如何在本地正确配置 start-command。例子：
       - 禁用自动启动：在 application.yml 或环境变量中把 python.service.start-command 设置为空字符串。
       - 推荐的本地 start-command 示例："./python_service/start_service.sh"（并确保脚本可执行且虚拟环境路径正确）。

4) python_service/requirements.txt
   - 现状：已包含 transformer 相关包（transformers, torch, sentencepiece, accelerate 等）。
   - 问题：无（与设计建议一致）。但建议在 docs 中明确指出可能需要 GPU 或特定版本，并给出可选的 lightweight 依赖集合或 conda 环境说明（Medium）。
   - 建议：在 docs/ 中增加一小节：CPU-only 安装建议与 GPU 加速说明（pip install -r requirements.txt 时的注意事项）。

5) python_service/start_service.sh
   - 现状：存在并支持 .venv 或 venv 两种激活路径，执行 uvicorn 并把日志写到 logs/service.log。
   - 问题：脚本执行前需要虚拟环境存在；application.yml 默认 start-command 使用 .venv/bin/uvicorn，脚本更稳健但未在 README 推荐（Medium）。
   - 建议：在 README 中把 start_service.sh 作为推荐本地启动方式的示例，并建议在 CI/生产环境使用 systemd 或 docker 描述。

6) python_service/app/config.py
   - 现状：Pydantic 从 python_service/.env 加载配置，默认有一些阈值与路径。
   - 问题：config.py 读取 .env 的行为和 repository 中实际 .env 内容应在 docs 中明确（Low）。
   - 建议：在 docs 中说明配置优先级（环境变量 > .env > defaults），并加入 .env.example 示例。

7) bili-insight-frontend/README.md 与 vite.config.ts
   - 现状：前端 README 是一个模板，包含基本命令；vite.config.ts 已配置 proxy 将 /insight 转发到 http://localhost:8080，但注释中提到 changeOrigin 与 rewrite 的条件。
   - 问题：前端 README 未明确说明后端代理的期望（/insight 前缀必须存在）以及如何配置后端端点或在非代理环境下配置 baseURL（Medium）。
   - 建议：在前端 README 中补充：
     - 期望后端运行在 http://localhost:8080 并提供 /insight/* 路由；开发时用 npm run dev（Vite 将代理到 8080）。
     - 如果需要直连后端（无代理），说明如何修改 src/utils/request.ts 中的 base URL 或调整 vite.config.ts 的 rewrite 规则。

8) docs/transformer_sentiment_upgrade_plan.md
   - 现状：文档详尽，列出迁移步骤、sql 迁移脚本、脚本路径与实现细节（文件已存在且详实）。
   - 问题：缺少“如何运行迁移脚本”的具体命令示例（例如 mysql 执行 sql 文件的命令、Python 脚本运行示例和需要的 env 变量）；也缺少回滚策略描述（Medium）。
   - 建议：补充命令示例：
     - 数据库迁移：mysql -u${DB_USER} -p${DB_PASSWORD} bili_insight_db < sql/migrations/2026-03-transformer-sentiment-upgrade.sql
     - 依赖安装与启动（示例）：python3 -m venv .venv && source .venv/bin/activate && pip install -r python_service/requirements.txt
     - 迁移回滚策略与备份建议：备份数据库前先导出：mysqldump -u... -p... bili_insight_db > backup.sql

9) sql/bili_insight_db.sql
   - 现状：存在 schema 与种子数据（审阅建议略）。
   - 问题：若要运行迁移，需要在 README 中说明如何应用（见上文）。
   - 建议：在 README 的“数据库初始化”部分给出具体命令。

其他可改进项（低优先级）
- docs 中的示例代码有助于理解，但建议在文档顶部或每个文件中注明“代码示例为 pseudocode/示意，实际路径与实现请以仓库代码为准”。
- 在 docs 根或 README 增加“开发者常见问题”部分，列出常见失败（端口被占用、uvicorn 未安装、数据库连接被拒绝）与对应解决方法。

可复制粘贴的修复片段（关键 High 项）

1) application.yml（建议替换片段）
---
python:
  service:
    url: ${PYTHON_SERVICE_URL:http://localhost:8001}
    api-key: ${PYTHON_API_KEY:change_me}
    working-directory: ${PYTHON_SERVICE_DIR:python_service}
    # 注意：默认 start-command 为空。请在本地或部署环境通过环境变量 PYTHON_START_CMD 指定具体启动命令，
    # 例如: export PYTHON_START_CMD="./python_service/start_service.sh"
    start-command: ${PYTHON_START_CMD:}
---

2) 根 README.md（建议内容片段，加入仓库根）
---
# Bili_Insight — 本地运行快速上手

基本步骤（开发机）

1. 数据库：确保 MySQL 在本地运行并创建数据库 bili_insight_db
   - 示例：mysql -u root -p
   - 导入 schema：mysql -u${DB_USER} -p${DB_PASSWORD} bili_insight_db < sql/bili_insight_db.sql

2. Python 服务：
   - 进入目录：cd python_service
   - 创建虚拟环境并安装依赖：python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
   - 复制 .env.example 为 .env 并填入真实值
   - 启动服务（推荐）：./start_service.sh
   - 或者直接：.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8001 --log-level info

3. Java 后端：
   - 在仓库根：mvn spring-boot:run
   - 注意：默认情况下，Java 会在启动时检查 Python 服务并尝试自动拉起（如果配置了 start-command）。如不希望此行为，请在 application.yml 或环境变量中把 python.service.start-command 置空。

4. 前端：
   - cd bili-insight-frontend && npm install
   - npm run dev（Vite 将把 /insight/* 代理到 http://localhost:8080）

---

后续建议（可选）
- 立刻：移除或替换仓库中的真实凭据，添加 .env.example（High）。
- 接着：在根 README.md 中加入上面建议的启动步骤并说明 Java 自动拉起 Python 的行为（High）。
- 然后：根据报告中列出的 Medium 项逐步完善 docs/transformer_sentiment_upgrade_plan.md，补充命令示例并写明回滚策略。

交付物与位置
- 本次审计设计文件：docs/superpowers/specs/2026-04-16-documentation-audit-design.md
- 本次审计报告（此文件）：docs/superpowers/specs/2026-04-16-documentation-audit-report.md

下一步（请回复选择）
1. 我只需要你阅读报告（当前选择）并不做任何修改（默认）。
2. 请我对 High 优先级项做最小修复并创建本地 git commit（不会 push）——我会先显示要修改的 diff 供你确认，然后再提交。
3. 请我先为根 README.md 创建初稿并写入仓库（不提交），然后你审阅。

请回复 “2” 或 “3” 或 “1” 来选择下一步（默认 1）。
