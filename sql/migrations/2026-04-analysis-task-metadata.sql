ALTER TABLE analysis_task
    ADD COLUMN video_title VARCHAR(255) NULL COMMENT 'Video title for direct task display' AFTER bvid,
    ADD COLUMN comment_fetch_mode VARCHAR(32) NULL COMMENT 'api/playwright/curl_cffi' AFTER error_message,
    ADD COLUMN comment_risk_controlled TINYINT(1) NOT NULL DEFAULT 0 COMMENT 'Whether comment crawling hit risk control' AFTER comment_fetch_mode,
    ADD COLUMN comment_fetch_retries INT NOT NULL DEFAULT 0 COMMENT 'Retry count before success/failure' AFTER comment_risk_controlled;

UPDATE analysis_task t
JOIN video_info v ON v.bvid = t.bvid
SET t.video_title = v.title
WHERE t.video_title IS NULL
  AND v.title IS NOT NULL;
