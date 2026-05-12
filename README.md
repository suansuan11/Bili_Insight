# Bili_Insight

小型开发者/维护者导读与本地运行快速上手说明。

目标
- 帮助开发者在本地启动完整服务链：MySQL -> Python 分析服务 -> Java 后端 -> 前端。
- 指出危险点（如自动拉起 Python、仓库中不应包含的凭据）与常见排错方案。

目录（重要位置）
- python_service/: FastAPI 分析服务（评论/弹幕情感分析）
- src/: Java Spring Boot 后端
- bili-insight-frontend/: Vue 3 前端应用
- sql/bili_insight_db.sql: 数据库 schema 与种子数据
- docs/: 项目文档与迁移计划（例如 docs/transformer_sentiment_upgrade_plan.md）

先决条件
- 本地安装：Java 11+、Maven、Node.js & npm、Python 3.8+/venv、MySQL
- 建议：在开发机上分配至少 4GB 内存给 Python/模型推理（若使用 Transformer 推理）

快速上手（开发环境）
1) 数据库
   - 启动本地 MySQL 并创建数据库：
     mysql -u root -p
     CREATE DATABASE bili_insight_db DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
   - 导入 schema：
     mysql -u${DB_USER} -p${DB_PASSWORD} bili_insight_db < sql/bili_insight_db.sql
   - 强烈建议在导入或迁移前先做 mysqldump 备份：
     mysqldump -u${DB_USER} -p${DB_PASSWORD} bili_insight_db > backup-before-migration.sql

2) Python 分析服务（推荐在 python_service 目录操作）
   - 进入目录：`cd python_service`
   - 创建并激活虚拟环境：
     python3 -m venv .venv
     source .venv/bin/activate
   - 安装依赖：`pip install -r requirements.txt`
   - 配置环境变量：复制一个 .env.example 为 .env（仓库可能没有真实的 .env.example，请创建并填入占位符）
     - 必需项示例（请在本地填写真实值，切勿把真实凭据提交到仓库）：
       DB_HOST=localhost
       DB_PORT=3306
       DB_USER=root
       DB_PASSWORD=change_me
       DB_NAME=bili_insight_db
       API_KEY=change_me
       SERVICE_PORT=8001
   - 启动服务（推荐脚本，脚本会把日志写入 python_service/logs/service.log）：
     ./start_service.sh
   - 或使用 uvicorn 直接运行（虚拟环境激活后）：
     .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8001 --log-level info

3) Java 后端
   - 在仓库根运行：`mvn spring-boot:run`
   - 注意：后端包含启动器 `StartupDataInitializer`，会在启动时检测 Python 服务健康；如果未运行且在 `application.yml` 中配置了 `python.service.start-command`，Java 会尝试拉起 Python 子进程并等待健康检查通过。
   - 如需禁用 Java 自动拉起 Python：确保环境变量或配置把 `python.service.start-command` 留空。例如在 shell 中运行：
     export PYTHON_START_CMD=""
     mvn spring-boot:run
   - 或在 `src/main/resources/application.yml`（只在本地开发时）把 `python.service.start-command` 设置为空。

4) 前端
   - 进入：`cd bili-insight-frontend`
   - 安装依赖：`npm install`
   - 启动开发服务器：`npm run dev`
   - Vite dev 服务器会将以 `/insight` 开头的请求代理到 `http://localhost:8080`（即 Java 后端），如需直连后端请修改 `vite.config.ts` 或前端 `src/utils/request.ts` 中的 base URL。

配置与安全（重要）
- 不要在仓库中提交真实凭据（DB 密码、JWT secret、API keys）。
- 推荐做法：在仓库中添加 `python_service/.env.example` 与根目录的 `README.md` 中示例，实际凭据保存在本地的 `.env`（并将其加入 .gitignore）。
- 当前仓库检测到示例配置文件包含开发默认值，请务必用占位符替换真实值并在部署前通过 CI/环境变量注入真实凭据。

与 docs/ 的关系
- 详细设计与迁移计划请参阅：`docs/transformer_sentiment_upgrade_plan.md` 和 `docs/项目技术文档.md`（若存在）。

常见问题与排错
- 数据库连接被拒绝：确认 MySQL 运行并且 `DB_USER`/`DB_PASSWORD` 与 `DB_NAME` 正确；检查 `application.yml` 与 `python_service/.env` 中的配置是否一致。
- Python 服务无法启动：检查虚拟环境是否激活、依赖是否安装（`pip install -r requirements.txt`）、以及 `uvicorn` 是否可执行。
- Java 报错找不到 Python：检查 `PYTHON_START_CMD` 或 `application.yml: python.service.start-command` 是否正确指向可执行命令（建议使用 `./python_service/start_service.sh`）。
- 前端无法代理 /insight：确认 Java 后端已在 8080 端口启动，或根据需要修改 `vite.config.ts` 的 proxy 配置。

下一步建议
- 立刻：在仓库中添加或替换 `.env.example`（占位符），从仓库中移除任何真实凭据（High）。
- 将本 README 作为快速上手页纳入仓库（已写入，待你审阅）。

如需我把 README.md 的内容调整为更详细的分步指南或创建 `.env.example` 文件并把真实 `.env` 添加到 `.gitignore`，回复我「请继续：创建 .env.example 并更新 .gitignore」或直接回复你想要的变更。 
