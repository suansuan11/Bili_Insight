-- ============================================================
-- Bili-Insight Transformer 情感分析升级迁移脚本
-- 版本: 2026-03
-- 说明: 扩展 video_comment / video_danmaku / sentiment_timeline 表，
--       新建 sentiment_annotation 人工标注表
-- ============================================================

DROP PROCEDURE IF EXISTS add_column_if_missing;
DELIMITER //
CREATE PROCEDURE add_column_if_missing(
    IN p_table_name VARCHAR(64),
    IN p_column_name VARCHAR(64),
    IN p_statement TEXT
)
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = DATABASE()
          AND table_name = p_table_name
          AND column_name = p_column_name
    ) THEN
        SET @ddl = p_statement;
        PREPARE stmt FROM @ddl;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
    END IF;
END //
DELIMITER ;

-- -------------------------------------------------------------
-- 1. 扩展 video_comment 表
-- -------------------------------------------------------------
ALTER TABLE video_comment
    MODIFY COLUMN sentiment_score decimal(6,4) DEFAULT NULL COMMENT '[-1.0000, 1.0000]';

CALL add_column_if_missing(
    'video_comment',
    'normalized_content',
    "ALTER TABLE video_comment ADD COLUMN normalized_content text DEFAULT NULL COMMENT 'Normalized text used for inference' AFTER content"
);
CALL add_column_if_missing(
    'video_comment',
    'text_type',
    "ALTER TABLE video_comment ADD COLUMN text_type varchar(16) NOT NULL DEFAULT 'comment' COMMENT 'comment / danmaku' AFTER gender"
);
CALL add_column_if_missing(
    'video_comment',
    'sentiment_confidence',
    "ALTER TABLE video_comment ADD COLUMN sentiment_confidence decimal(5,4) DEFAULT NULL COMMENT '0.0000 to 1.0000' AFTER sentiment_score"
);
CALL add_column_if_missing(
    'video_comment',
    'sentiment_intensity',
    "ALTER TABLE video_comment ADD COLUMN sentiment_intensity varchar(16) DEFAULT NULL COMMENT 'WEAK / MEDIUM / STRONG' AFTER sentiment_confidence"
);
CALL add_column_if_missing(
    'video_comment',
    'sentiment_source',
    "ALTER TABLE video_comment ADD COLUMN sentiment_source varchar(64) DEFAULT NULL COMMENT 'transformer_comment_v1 / fallback_rule_v1' AFTER sentiment_intensity"
);
CALL add_column_if_missing(
    'video_comment',
    'sentiment_version',
    "ALTER TABLE video_comment ADD COLUMN sentiment_version varchar(64) DEFAULT NULL COMMENT 'comment-roberta-v1.0.0' AFTER sentiment_source"
);
CALL add_column_if_missing(
    'video_comment',
    'emotion_tags_json',
    "ALTER TABLE video_comment ADD COLUMN emotion_tags_json json DEFAULT NULL COMMENT '[\"complaint\",\"sarcasm\"]' AFTER sentiment_version"
);
CALL add_column_if_missing(
    'video_comment',
    'aspect_details_json',
    "ALTER TABLE video_comment ADD COLUMN aspect_details_json json DEFAULT NULL COMMENT 'Per-aspect sentiment results' AFTER emotion_tags_json"
);

-- -------------------------------------------------------------
-- 2. 扩展 video_danmaku 表
-- -------------------------------------------------------------
ALTER TABLE video_danmaku
    MODIFY COLUMN sentiment_score decimal(6,4) DEFAULT NULL COMMENT '[-1.0000, 1.0000]';

CALL add_column_if_missing(
    'video_danmaku',
    'normalized_content',
    "ALTER TABLE video_danmaku ADD COLUMN normalized_content text DEFAULT NULL COMMENT 'Normalized text used for inference' AFTER content"
);
CALL add_column_if_missing(
    'video_danmaku',
    'text_type',
    "ALTER TABLE video_danmaku ADD COLUMN text_type varchar(16) NOT NULL DEFAULT 'danmaku' COMMENT 'comment / danmaku' AFTER task_id"
);
CALL add_column_if_missing(
    'video_danmaku',
    'sentiment_confidence',
    "ALTER TABLE video_danmaku ADD COLUMN sentiment_confidence decimal(5,4) DEFAULT NULL COMMENT '0.0000 to 1.0000' AFTER sentiment_score"
);
CALL add_column_if_missing(
    'video_danmaku',
    'sentiment_intensity',
    "ALTER TABLE video_danmaku ADD COLUMN sentiment_intensity varchar(16) DEFAULT NULL COMMENT 'WEAK / MEDIUM / STRONG' AFTER sentiment_confidence"
);
CALL add_column_if_missing(
    'video_danmaku',
    'sentiment_source',
    "ALTER TABLE video_danmaku ADD COLUMN sentiment_source varchar(64) DEFAULT NULL COMMENT 'transformer_danmaku_v1 / fallback_rule_v1' AFTER sentiment_intensity"
);
CALL add_column_if_missing(
    'video_danmaku',
    'sentiment_version',
    "ALTER TABLE video_danmaku ADD COLUMN sentiment_version varchar(64) DEFAULT NULL COMMENT 'danmaku-roberta-v1.0.0' AFTER sentiment_source"
);
CALL add_column_if_missing(
    'video_danmaku',
    'emotion_tags_json',
    "ALTER TABLE video_danmaku ADD COLUMN emotion_tags_json json DEFAULT NULL COMMENT '[\"sarcasm\",\"mocking\"]' AFTER sentiment_version"
);

-- -------------------------------------------------------------
-- 3. 扩展 sentiment_timeline 表
-- -------------------------------------------------------------

CALL add_column_if_missing(
    'sentiment_timeline',
    'timeline_version',
    "ALTER TABLE sentiment_timeline ADD COLUMN timeline_version varchar(64) DEFAULT NULL COMMENT 'timeline-v2' AFTER aspect_sentiment_json"
);
CALL add_column_if_missing(
    'sentiment_timeline',
    'aggregation_meta_json',
    "ALTER TABLE sentiment_timeline ADD COLUMN aggregation_meta_json json DEFAULT NULL COMMENT 'window, weights, filters' AFTER timeline_version"
);

-- -------------------------------------------------------------
-- 4. 新建 sentiment_annotation 人工标注表
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sentiment_annotation (
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='人工情感标注表';

DROP PROCEDURE IF EXISTS add_column_if_missing;
