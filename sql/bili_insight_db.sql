/*
 Navicat Premium Dump SQL

 Source Server         : local
 Source Server Type    : MySQL
 Source Server Version : 90600 (9.6.0)
 Source Host           : localhost:3306
 Source Schema         : bili_insight_db

 Target Server Type    : MySQL
 Target Server Version : 90600 (9.6.0)
 File Encoding         : 65001

 Date: 24/03/2026 00:06:17
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for analysis_task
-- ----------------------------
DROP TABLE IF EXISTS `analysis_task`;
CREATE TABLE `analysis_task` (
  `task_id` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'UUID task identifier',
  `bvid` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'Bilibili Video ID',
  `user_id` bigint DEFAULT NULL COMMENT 'The user who created this task',
  `project_id` bigint DEFAULT NULL COMMENT 'Associated project, if any',
  `status` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'PENDING' COMMENT 'PENDING, RUNNING, COMPLETED, FAILED',
  `task_type` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'FULL' COMMENT 'FULL, COMMENTS_ONLY, DANMAKU_ONLY',
  `progress` int NOT NULL DEFAULT '0' COMMENT '0-100',
  `current_step` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'Description of current processing step',
  `error_message` text COLLATE utf8mb4_unicode_ci,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `completed_at` datetime DEFAULT NULL,
  PRIMARY KEY (`task_id`),
  KEY `idx_bvid` (`bvid`),
  KEY `idx_status` (`status`),
  KEY `idx_user_id` (`user_id`),
  KEY `fk_task_project` (`project_id`),
  KEY `idx_created_at` (`created_at`),
  CONSTRAINT `fk_task_project` FOREIGN KEY (`project_id`) REFERENCES `project` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_task_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Records of analysis_task
-- ----------------------------
BEGIN;
COMMIT;

-- ----------------------------
-- Table structure for popular_videos
-- ----------------------------
DROP TABLE IF EXISTS `popular_videos`;
CREATE TABLE `popular_videos` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `bvid` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `aid` bigint NOT NULL,
  `title` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `author` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `tname` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'Category name',
  `cover_url` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `publish_date` datetime DEFAULT NULL COMMENT '视频发布时间',
  `duration` int DEFAULT '0' COMMENT '视频时长(秒)',
  `view_count` int DEFAULT '0',
  `danmaku_count` int DEFAULT '0',
  `reply_count` int DEFAULT '0',
  `comment_count` int DEFAULT '0' COMMENT 'Fixed: was missing, causing Python driver errors',
  `favorite_count` int DEFAULT '0',
  `coin_count` int DEFAULT '0',
  `share_count` int DEFAULT '0',
  `like_count` int DEFAULT '0',
  `score` int DEFAULT '0' COMMENT 'Hot score',
  `rcmd_reason` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `scraped_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_bvid` (`bvid`),
  KEY `idx_tname` (`tname`),
  KEY `idx_score` (`score`)
) ENGINE=InnoDB AUTO_INCREMENT=301 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Records of popular_videos
-- ----------------------------
BEGIN;
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (1, 'BV1dScmz7ENx', 116218845465760, '这就是你想要的长大吗？', '就叫阿路8', NULL, 'http://i2.hdslb.com/bfs/archive/d13c509613643837820194f358b2744ccc713b18.jpg', '2026-03-13 11:10:00', 178, 5069537, 10596, 0, 16486, 177499, 229858, 30909, 585273, 0, NULL, '2026-03-17 23:00:57');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (2, 'BV1k9wDzKEvS', 116243189275427, '在性产业“合法”的地方，我们看到了...', '影视飓风', NULL, 'http://i2.hdslb.com/bfs/archive/b2572c304f4c52230ec71cb2159e7f1956a873b7.jpg', '2026-03-17 17:00:00', 1566, 1182553, 14268, 0, 5890, 40627, 95300, 18421, 131426, 0, NULL, '2026-03-17 23:00:57');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (3, 'BV1ezcDzXEUN', 116221211246940, '央美一等奖二维动画作品——《谱》', '央美盒', NULL, 'http://i0.hdslb.com/bfs/archive/a58c0db3a7c444108ac2aeda5ccd466d1b1f4655.jpg', '2026-03-13 19:00:00', 183, 1525750, 1643, 0, 7786, 111393, 82094, 20260, 305354, 0, NULL, '2026-03-17 23:00:57');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (4, 'BV1nWwFz9EFY', 116209097907675, '热烈欢迎瞿颖姐姐！看看她带来多少便宜货！！', 'papi酱', NULL, 'http://i2.hdslb.com/bfs/archive/fc65f1df10dcb3fe28fb95774c2241b24b47a5bb.jpg', '2026-03-12 12:00:00', 2159, 3866189, 32281, 0, 13147, 61311, 211610, 65224, 387394, 0, NULL, '2026-03-17 23:00:57');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (5, 'BV1tbwgzcEPZ', 116234632830287, '\"苦涩的沙 吹痛脸庞的感觉\"', '我爱吃派大星', NULL, 'http://i1.hdslb.com/bfs/archive/522a80bfc37dde37837c19bb0399c3e269e7d492.jpg', '2026-03-16 08:20:00', 167, 824345, 174, 0, 789, 16108, 891, 946, 75320, 0, NULL, '2026-03-17 23:00:57');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (6, 'BV1fJwTzzE6b', 116232468568109, '显白到发光的红色穿搭❤️', '清和Alicia', NULL, 'http://i1.hdslb.com/bfs/archive/30de952a10a7747cbf5b46c8b8917a48fa7a28ed.jpg', '2026-03-15 17:27:59', 53, 510324, 341, 0, 557, 8578, 3497, 730, 27918, 0, NULL, '2026-03-17 21:44:12');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (7, 'BV1J4w3zHEhX', 116234062469160, '每天都在感叹二次元的爱好伟大…', '素以兔兔TU', NULL, 'http://i0.hdslb.com/bfs/archive/a305bcbf7328724e841ba1627075fbc7c3481808.jpg', '2026-03-16 00:12:04', 40, 348696, 23, 0, 228, 4151, 784, 407, 61040, 0, NULL, '2026-03-17 23:00:57');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (8, 'BV1i6w4zoEJn', 116228089708749, '【自制AI动画】', '月亮轻声细语', NULL, 'http://i1.hdslb.com/bfs/archive/50e9c72e06196963d6cad2fcf1af3e730fd03ca5.jpg', '2026-03-14 22:59:21', 91, 535386, 348, 0, 3580, 21077, 11942, 4039, 50071, 0, NULL, '2026-03-17 23:00:57');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (9, 'BV1fgw5zfEBy', 116236562271106, '100个人在雪山救了一只狐狸....', '天天吃八碗', NULL, 'http://i2.hdslb.com/bfs/archive/9471b2802d099ae372e07807812c1b621e4efeb5.jpg', '2026-03-16 10:49:20', 80, 1552512, 589, 0, 1085, 12600, 1426, 4211, 102069, 0, NULL, '2026-03-17 23:00:57');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (10, 'BV1gzwTzoEJD', 116232250529636, '你懂玻璃大炮？', '一帆-浮生电竞', NULL, 'http://i1.hdslb.com/bfs/archive/ce051bc59ddd5b6fdcfd4db1ccfbf68b211d4639.jpg', '2026-03-15 16:46:11', 185, 1464486, 357, 0, 1719, 126038, 9600, 4610, 121885, 0, NULL, '2026-03-17 23:00:57');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (11, 'BV1UvwNzDEPr', 116231461932751, '她真的很可爱', '阿喻AYU唯一正版', NULL, 'http://i0.hdslb.com/bfs/archive/71bd93d52a33ec97ac159152da30cbd7e7e03f90.jpg', '2026-03-15 19:25:00', 149, 2423657, 1512, 0, 4297, 40794, 10449, 7076, 211386, 0, NULL, '2026-03-17 23:00:57');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (12, 'BV1kyw2zdEMz', 116239397618081, '两只喜鹊高空丢树枝，边飞边追进行“花式飞行”……网友：这才是顶级飞控！', '人民日报', NULL, 'http://i0.hdslb.com/bfs/archive/fc46897cfc9cd78efb40b00415da58cdb26d564b.jpg', '2026-03-16 22:50:32', 25, 478601, 222, 0, 1459, 5877, 870, 1438, 37563, 0, NULL, '2026-03-17 23:00:57');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (13, 'BV1Aiw9zLEPw', 116243491194629, '上压力就变聪明了 合着之前都在藏拙', '超级无敌大开门', NULL, 'http://i1.hdslb.com/bfs/archive/7dec8cbbc3e001527bd99980170b62dd735ca875.jpg', '2026-03-17 16:10:56', 45, 218197, 288, 0, 630, 1412, 1153, 2791, 30434, 0, NULL, '2026-03-17 23:00:57');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (14, 'BV1qJwtzcESv', 116227871672081, '生物观察日志', '颗粒状-KLZ', NULL, 'http://i1.hdslb.com/bfs/archive/5096a36c63a21c9ebbf971a01203e6aa6d618096.jpg', '2026-03-14 21:58:47', 91, 200555, 325, 0, 1126, 8397, 1292, 729, 32668, 0, NULL, '2026-03-17 20:42:07');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (15, 'BV1NPwTzDEL1', 116232300793045, '钓鱼钓出西部恩怨', '荒野大天官', NULL, 'http://i1.hdslb.com/bfs/archive/7317ebfb81c8f7dda58c209c2050bb0a3566a904.jpg', '2026-03-15 17:05:44', 273, 1471450, 783, 0, 589, 17747, 941, 1292, 54467, 0, NULL, '2026-03-17 23:00:57');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (16, 'BV1mCwXzDEKM', 116243860360287, '战况不利开始摇人？特朗普欲组万国护航联盟', '麻薯波比呀', NULL, 'http://i2.hdslb.com/bfs/archive/24035e21cd8d7307c4725e50d41b0d62a4c700a3.jpg', '2026-03-17 17:55:05', 1220, 420439, 4952, 0, 1967, 5735, 7300, 726, 37867, 0, NULL, '2026-03-17 20:42:08');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (17, 'BV1inwtz8Emm', 116227854895989, '救命！被网红恋爱观洗脑的人，到底有多离谱', '付曦冉', NULL, 'http://i2.hdslb.com/bfs/archive/376ab7f0745c808bcf22fdf5bf3523e715f30048.jpg', '2026-03-15 18:00:00', 480, 324289, 1410, 0, 723, 8133, 2880, 585, 14340, 0, NULL, '2026-03-17 21:44:12');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (18, 'BV1hFwuzwEBo', 116233525599130, '别怪我，我总得回家', '8点整', NULL, 'http://i0.hdslb.com/bfs/archive/33476cc0006e96f26f03fc78f2e1dc63b3327b78.jpg', '2026-03-15 21:56:56', 93, 555921, 120, 0, 1301, 3529, 615, 776, 29975, 0, NULL, '2026-03-17 21:44:12');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (19, 'BV1QMwmzgE1f', 116239146030418, '鸣潮手绘动画 / 笑一笑吧~', '再逐夏', NULL, 'http://i1.hdslb.com/bfs/archive/ddd3001d26ec72a2285931af64eb978563883bbf.jpg', '2026-03-16 22:00:00', 102, 297330, 1438, 0, 2017, 25290, 34433, 5078, 72143, 0, NULL, '2026-03-17 23:00:57');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (20, 'BV1dyw7zAE6F', 116238189594477, '我在你们心中就那么老吗？都快活成兵马俑了！', '板娘小薇', NULL, 'http://i1.hdslb.com/bfs/archive/fa5203e204d6fa390a27966cad2ba9bdd8261469.jpg', '2026-03-16 17:46:47', 186, 166478, 254, 0, 1463, 2463, 839, 383, 24488, 0, NULL, '2026-03-17 23:00:57');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (22, 'BV1QtwNzxECa', 116231210274360, '小企鹅这个肥美', '鱼不乐yu', NULL, 'http://i2.hdslb.com/bfs/archive/a4f7c218a7c6662fa4367d52ff1ed9f78813a5c8.jpg', '2026-03-15 12:06:30', 15, 238344, 34, 0, 696, 11777, 1964, 2317, 37663, 0, NULL, '2026-03-17 23:00:57');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (23, 'BV1fEwjzwEsE', 116237250139565, '冷知识先刷到的是皇上！#doro  yc@王大总管', 'Jooey吖', NULL, 'http://i0.hdslb.com/bfs/archive/c57be506beb4b5d967595b142fabe4b54a0f9d6c.jpg', '2026-03-16 16:30:00', 26, 325897, 54, 0, 5183, 10669, 2451, 44253, 44737, 0, NULL, '2026-03-17 23:00:57');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (24, 'BV1jTw9zKEE4', 116243608833045, '“只要反派长得好，三观跟着五官跑”', '哇周某人', NULL, 'http://i0.hdslb.com/bfs/archive/acb6143c94ac1b85f5c72cb448d8e5c5eda7e9bd.jpg', '2026-03-17 16:40:30', 26, 52209, 221, 0, 421, 1995, 1148, 306, 5591, 0, NULL, '2026-03-17 20:42:08');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (27, 'BV1h1cDzmEm3', 116221143948708, '来法国看看追我的人排到哪里了', '白昼小熊', NULL, 'http://i0.hdslb.com/bfs/archive/a3523aef7c5afd40df15502d8b215599be8c8d7e.jpg', '2026-03-13 17:36:21', 15, 3271483, 85, 0, 401, 17972, 6140, 2435, 166524, 0, NULL, '2026-03-17 23:00:57');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (28, 'BV1z7wEz6Ex2', 116238156040908, '过度提醒=提前责备。网友：我已经开始烦躁了', '河南卫视', NULL, 'http://i1.hdslb.com/bfs/archive/3f6339b1ddbc7209cd1bf6033c1c49d70b0aa688.jpg', '2026-03-16 17:36:28', 39, 580253, 89, 0, 953, 10107, 541, 10065, 19923, 0, NULL, '2026-03-17 20:42:08');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (29, 'BV1epwxznE9Q', 116226730827493, '写了一个反派营救正派BGM！', '所长sama', NULL, 'http://i0.hdslb.com/bfs/archive/6cda8767ed9b153dabe68d9014f91d34295cfe49.jpg', '2026-03-14 17:10:22', 30, 2101937, 1039, 0, 5734, 96157, 14000, 4058, 272265, 0, NULL, '2026-03-17 23:00:57');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (30, 'BV1qUwMzzEgx', 116233575928086, '我拍照', '_Okawarri', NULL, 'http://i2.hdslb.com/bfs/archive/4672ff204d5fdcec1da5c65b5e81ce2585c3d3a7.jpg', '2026-03-15 22:07:35', 27, 148548, 104, 0, 1063, 9907, 1886, 1305, 39336, 0, NULL, '2026-03-17 23:00:57');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (32, 'BV1raw4zAEuJ', 116226244222526, '拥抱', '林克斯先生Links', NULL, 'http://i1.hdslb.com/bfs/archive/83a4ce3c8224c721c0894db6c97bc779f2302c0d.jpg', '2026-03-14 15:04:07', 29, 3967250, 418, 0, 4259, 31186, 4058, 2585, 356191, 0, NULL, '2026-03-17 21:44:12');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (35, 'BV19VwMzYEHN', 116231545886140, '雪山救狐狸，但史上最离谱的一集！', '青时晚', NULL, 'http://i1.hdslb.com/bfs/archive/931d631508e9c1e4f2f85fbdd0695dec1e0a6d05.jpg', '2026-03-15 13:35:44', 96, 1236297, 368, 0, 800, 8875, 1948, 3270, 59770, 0, NULL, '2026-03-17 20:42:08');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (36, 'BV1fiwSzZEa8', 116241813478732, '【漂咲往事】第七集 | 千咲你明天不用来了！', 'Raven黑鸦', NULL, 'http://i2.hdslb.com/bfs/archive/c656b7ff2ff95898d18c8c4b17bf42efd9872f6a.jpg', '2026-03-17 09:03:19', 99, 234395, 218, 0, 497, 9111, 1072, 1500, 26767, 0, NULL, '2026-03-17 21:44:12');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (38, 'BV1TjwLzyEYr', 116237652723239, '⚡️眼睛瞎在卫戍上⚡️', '薯饼小狗M', NULL, 'http://i1.hdslb.com/bfs/archive/809241a1bcb832767664a586446ee6d91cadee65.jpg', '2026-03-16 15:24:32', 21, 289522, 35, 0, 2139, 9480, 3517, 29362, 49013, 0, NULL, '2026-03-17 23:00:57');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (39, 'BV1Tpw7zEEaP', 116238491589261, '男人之间，无需多言', '古泽源', NULL, 'http://i1.hdslb.com/bfs/archive/e9f6e5361c815444df0de99baaefa5d6f246696b.jpg', '2026-03-16 19:00:09', 32, 2397034, 267, 0, 2636, 15315, 4020, 1171, 196929, 0, NULL, '2026-03-17 23:00:57');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (108, 'BV1nvw7zgEuE', 116238625868647, '网络热门长虫视频(114)网友看完“盖瑞”后跟风饲养海岛竹叶青？被咬伤的只会越来越多！', '世界记忆大师龙雅', NULL, 'http://i1.hdslb.com/bfs/archive/45fb1083f3e4d72a367c323a2485a8dea4802227.jpg', '2026-03-17 18:30:04', 458, 65699, 862, 0, 396, 679, 866, 61, 6537, 0, NULL, '2026-03-17 21:44:12');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (110, 'BV1N8w9zJENw', 116243289869435, '别惹我，我老婆大唐高阳公主', '虾仁不放火', NULL, 'http://i1.hdslb.com/bfs/archive/45f64079581fffab1add3842c41da4e2531028ae.jpg', '2026-03-17 18:00:00', 522, 25892, 102, 0, 492, 840, 2072, 24, 3445, 0, NULL, '2026-03-17 21:44:12');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (115, 'BV1NQwEzEEGy', 116222419146652, '这是真拼豆！也是真草莓！！！', '黑猫厨房', NULL, 'http://i2.hdslb.com/bfs/archive/0a11b1c560e81cbbc936406307c7fc1d573eca4b.jpg', '2026-03-14 17:00:00', 165, 3800186, 480, 0, 769, 36756, 25165, 4287, 145256, 0, NULL, '2026-03-17 21:44:12');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (118, 'BV1Gew8zbEUH', 116228274264224, '真的唱的很用力了补药喷窝', '恐怖核桃人', NULL, 'http://i0.hdslb.com/bfs/archive/7f4085b021183044ff9155f36e5d5741c9e1673a.jpg', '2026-03-14 23:42:17', 196, 115925, 135, 0, 582, 3800, 2671, 238, 31147, 0, NULL, '2026-03-17 21:44:12');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (119, 'BV1jTw9zNEvn', 116243608635035, '【ITZY】\"THAT\'S A NO NO\" Dance Practice (Close-up CAM Ver.)', 'ITZY', NULL, 'http://i2.hdslb.com/bfs/archive/ad6ebcff74163ed6a1d725087e9176ea968b3cc2.jpg', '2026-03-17 18:00:00', 133, 20970, 778, 0, 438, 1086, 2398, 177, 4014, 0, NULL, '2026-03-17 21:44:12');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (120, 'BV16GwUzxEaB', 116240387413236, '它本来会痛苦的离开，但不巧遇到了我', '刘小鹿是小鹿6', NULL, 'http://i1.hdslb.com/bfs/archive/69df2a49b695611606bb630248be73e8714fa728.jpg', '2026-03-17 12:05:00', 187, 67795, 93, 0, 161, 747, 5410, 57, 8286, 0, NULL, '2026-03-17 21:44:12');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (123, 'BV1VRwMzvEh7', 116233508754698, '我也来画十二生肖，绝对公平', '一方之杰', NULL, 'http://i2.hdslb.com/bfs/archive/d1c444b3ceb20998cd98a153546a3ade5f9cd145.jpg', '2026-03-15 21:50:13', 34, 404853, 99, 0, 432, 6625, 672, 219, 39515, 0, NULL, '2026-03-17 23:00:57');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (127, 'BV1kQwjzzEo7', 116238827196672, '雪山救狐狸，但是有100万个农夫', 'istupidpig', NULL, 'http://i0.hdslb.com/bfs/archive/3600f8d27f924d0fe3cd9d58e0a71053dd82316a.jpg', '2026-03-16 20:22:36', 127, 2337052, 2125, 0, 2981, 20308, 5460, 14700, 149011, 0, NULL, '2026-03-17 23:00:57');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (132, 'BV1RUw7z8EPw', 116238407704109, '比流量', '爱玩的木炭', NULL, 'http://i2.hdslb.com/bfs/archive/85a00860aff1bfa99337b46173b286c6c5f64b6c.jpg', '2026-03-16 18:36:41', 17, 177011, 297, 0, 352, 645, 1884, 47, 57929, 0, NULL, '2026-03-17 21:44:12');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (147, 'BV1oewVzWExp', 116236696423199, '当山东人说', 'Cheems电玩屋', NULL, 'http://i1.hdslb.com/bfs/archive/9f9f23e01e9dff2b29a1eee0a1753e916b88b769.jpg', '2026-03-16 11:22:11', 20, 1209271, 311, 0, 4368, 14497, 1490, 25334, 92619, 0, NULL, '2026-03-17 23:00:57');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (153, 'BV1zLwjzPEVg', 116237350733503, '“不是风动，是心动”', '哇周某人', NULL, 'http://i0.hdslb.com/bfs/archive/e49c5ea544426783f8c9f536b2fdfe7f033221de.jpg', '2026-03-16 16:10:00', 32, 300824, 326, 0, 124, 6587, 1610, 668, 16803, 0, NULL, '2026-03-17 23:00:57');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (155, 'BV1cswVzhES6', 116234850927648, '蜘蛛糸モノポリー/九章', 'I黑鸦I', NULL, 'http://i0.hdslb.com/bfs/archive/db915d00545d1a009de239c8d013e94e24de33fd.jpg', '2026-03-16 03:31:55', 140, 114221, 40, 0, 344, 9701, 7083, 1346, 18284, 0, NULL, '2026-03-17 23:00:57');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (158, 'BV1ygcyz7EFY', 116216949641551, '谁在鼓励女性不婚不育？美国平权运动深度解析', '一万也', NULL, 'http://i2.hdslb.com/bfs/archive/3689b6c2b6b4a9897b5ea2a2f76c2753f2ef3992.jpg', '2026-03-12 23:42:59', 529, 511823, 1821, 0, 2827, 17907, 15173, 2147, 72803, 0, NULL, '2026-03-17 21:44:12');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (159, 'BV1uLwSzVEVR', 116242115461176, '各位义父义母 当老登小助理的第七天', '创业的杜老登', NULL, 'http://i1.hdslb.com/bfs/archive/57c3ce911dfe3479db5952e52d4b4c7b531430ec.jpg', '2026-03-17 10:26:28', 181, 148842, 95, 0, 1524, 767, 2708, 52, 27148, 0, NULL, '2026-03-17 23:00:57');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (160, 'BV1qjwjzYE15', 116237266848845, '为了以色列，特朗普和最爱他的人决裂了……【毒舌的南瓜】', '毒舌的南瓜', NULL, 'http://i1.hdslb.com/bfs/archive/539669f3b17ce49f8d5098f08b006abbcc33e0b9.jpg', '2026-03-16 16:00:00', 1405, 764695, 5786, 0, 2380, 7834, 4520, 1010, 43976, 0, NULL, '2026-03-17 21:44:12');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (175, 'BV14pwKzUE4h', 116230874733433, '干脆你俩凑一对得了', '改良大蓝猫', NULL, 'http://i0.hdslb.com/bfs/archive/75313d1d88286716b8306c868b59294bbb79091e.jpg', '2026-03-17 18:40:00', 81, 40387, 402, 0, 268, 1209, 652, 167, 5993, 0, NULL, '2026-03-17 21:44:12');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (176, 'BV1u5NwzJEyA', 116188176719750, 'plainjane遇上恋人', 'Strictlyviolin荀博', NULL, 'http://i2.hdslb.com/bfs/archive/d2c2604dcf4515756365bfaef8eb03dee2e1bebd.jpg', '2026-03-13 17:31:00', 53, 213928, 67, 0, 263, 6807, 2763, 893, 23180, 0, NULL, '2026-03-17 23:00:57');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (177, 'BV1AYwQzzEbV', 116242685891674, '美国超市就能买到枪？比买菜更简单！', '小鹿Lawrence', NULL, 'http://i2.hdslb.com/bfs/archive/8d72415235fce3c7b1e1a63fce56c1bc23831159.jpg', '2026-03-17 18:00:00', 2178, 157232, 1555, 0, 299, 2155, 3296, 277, 5923, 0, NULL, '2026-03-17 21:44:12');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (178, 'BV1P8w7zCEJB', 116238609028952, '全球首发！我国自研，世界最强！', '央视军事', NULL, 'http://i2.hdslb.com/bfs/archive/476807ac6e8336703094b6f36d3599a453f18323.jpg', '2026-03-16 20:00:00', 271, 276973, 811, 0, 2943, 2083, 1470, 908, 23195, 0, NULL, '2026-03-17 21:44:12');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (179, 'BV13MwVzGEFE', 116234767045957, '小企鹅和她的新朋友们', '千萤呐', NULL, 'http://i0.hdslb.com/bfs/archive/2665b33dd538ea491e98a8043dbfdf44a22cd0af.jpg', '2026-03-16 10:40:00', 252, 113853, 146, 0, 504, 3331, 3262, 416, 14734, 0, NULL, '2026-03-17 21:44:12');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (180, 'BV1mBwNzUEAX', 116231361268602, '【洛天依原创】MONTAGEM PITTY', '见过夏天P', NULL, 'http://i2.hdslb.com/bfs/archive/1353aba452eed43bdf0440a5c1b8a598ca76f994.jpg', '2026-03-15 12:48:22', 99, 130965, 799, 0, 1150, 25582, 8673, 1820, 41851, 0, NULL, '2026-03-17 21:44:12');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (202, 'BV1BpwXzNExk', 116244296500820, '雷霆语言从何而来？', '玉玉__', NULL, 'http://i1.hdslb.com/bfs/archive/c5e43ed74583c71acef16806fd16a79b386b9f01.jpg', '2026-03-17 19:37:03', 615, 60736, 658, 0, 599, 1752, 2526, 547, 11057, 0, NULL, '2026-03-17 23:00:57');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (205, 'BV1f7wtzaExX', 116227955629554, '《枯脉》', '鸦青色的夜', NULL, 'http://i0.hdslb.com/bfs/archive/dc63854291938fff58a159d5cd49dc03fa457d4f.jpg', '2026-03-14 22:25:58', 547, 226974, 718, 0, 1331, 12749, 8451, 4902, 36934, 0, NULL, '2026-03-17 23:00:57');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (207, 'BV1tBwjzEEfG', 116237099081145, '循环歌单|【PERFECTION FUNK】|“【战争巨兽の小曲】【夏季双子星の小曲】”', '蛋某人音乐', NULL, 'http://i2.hdslb.com/bfs/archive/e5ff4848fcd65c5e22d84602e062c6fa4aace73b.jpg', '2026-03-17 08:00:00', 3092, 884567, 31, 0, 415, 21961, 781, 96, 23441, 0, NULL, '2026-03-17 23:00:57');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (211, 'BV1ygwXzVEns', 116244162281583, '为什么内塔尼亚胡没能成功证明自己没死？', '波士顿圆脸', NULL, 'http://i2.hdslb.com/bfs/archive/f286909303a8ee29bfe0f5a66d72ddbd4a240cef.jpg', '2026-03-17 19:03:46', 579, 414083, 2686, 0, 2447, 3240, 1687, 1410, 30364, 0, NULL, '2026-03-17 23:00:57');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (218, 'BV1Lgw9zAErm', 116243776413097, '我的曼谷旅行记录!', '正直少年李发卡', NULL, 'http://i1.hdslb.com/bfs/archive/117b02ad07c889d691c00a5fe0aa981880abb4a4.jpg', '2026-03-17 17:27:32', 691, 38890, 550, 0, 549, 838, 2053, 218, 3872, 0, NULL, '2026-03-17 23:00:57');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (235, 'BV153cmz5Efr', 116218929348657, '漫夏长廊', '我不是喝杯咖啡', NULL, 'http://i0.hdslb.com/bfs/archive/319071ad4e6ea27dd99bb74f8fdf0e8561033d04.jpg', '2026-03-13 08:03:06', 14, 238137, 57, 0, 419, 11292, 977, 653, 44062, 0, NULL, '2026-03-17 23:00:57');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (236, 'BV1BJwtzcEXq', 116227871675717, '【百万纪念】唱了大家好像很想听的《浸春芜》', '果宝Official', NULL, 'http://i1.hdslb.com/bfs/archive/7096f45fae775328dbfcd640c664a473d159adf1.jpg', '2026-03-17 19:00:00', 191, 29156, 287, 0, 631, 1504, 3227, 280, 6330, 0, NULL, '2026-03-17 23:00:57');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (251, 'BV1KpwQzjEzU', 116242602003608, '最终获得胜利的是…', '无我漂佩MY', NULL, 'http://i2.hdslb.com/bfs/archive/b48baf5613278fa074d03e956e9782af535d4f4f.jpg', '2026-03-17 14:20:00', 160, 386776, 328, 0, 688, 8539, 3287, 997, 35986, 0, NULL, '2026-03-17 23:00:57');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (252, 'BV1mpwhzRE7J', 116229884873878, '⚡当通天代给姥爷豪代打…⚡', '千甶', NULL, 'http://i0.hdslb.com/bfs/archive/cd8c651298c4e3f4ed6148eea87b46839b0ce237.jpg', '2026-03-15 06:33:25', 167, 152528, 134, 0, 494, 2828, 609, 500, 17308, 0, NULL, '2026-03-17 23:00:57');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (253, 'BV1QXcCzfECp', 116216798648289, '全世界最懒国家！一年200天假期！生活到底什么样？一日三餐吃什么？', 'HOLA小测佬', NULL, 'http://i0.hdslb.com/bfs/archive/8b5bff8b214b67fd8f59a75a1aec20afb1d86719.jpg', '2026-03-14 18:18:00', 668, 5212240, 15203, 0, 8570, 40147, 22204, 16270, 98370, 0, NULL, '2026-03-17 23:00:57');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (254, 'BV1G3w7zdECV', 116238541919322, '超萌7套变装，点进来就出不去了！调色盘(｡•̀ᴗ-)✧❤️', '优联酱uu', NULL, 'http://i1.hdslb.com/bfs/archive/5d5f7baa2092be5e6cfbc4ad392280d0dc658af9.jpg', '2026-03-16 19:13:14', 197, 129539, 199, 0, 318, 5389, 2222, 314, 8484, 0, NULL, '2026-03-17 23:00:57');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (255, 'BV1iUwMzzE1R', 116233575928994, '崩坏星穹铁道：全员机娘的惊喜', '赛博浮云', NULL, 'http://i1.hdslb.com/bfs/archive/c17017b47d7d4c8fcd820704104b3288958524e2.jpg', '2026-03-15 22:09:58', 79, 286152, 114, 0, 305, 7432, 971, 1110, 27324, 0, NULL, '2026-03-17 23:00:57');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (256, 'BV16UwczxEgn', 116210054206743, '跟全世界的人合唱《We Are The World》', '你哇哥233', NULL, 'http://i0.hdslb.com/bfs/archive/41ef2a91b0d453b0bbb6917bd95cd4df66f907d7.jpg', '2026-03-11 18:26:33', 317, 646141, 3781, 0, 3098, 23836, 42852, 2271, 115765, 0, NULL, '2026-03-17 23:00:57');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (257, 'BV1Ztw3zSEpG', 116233710077091, '“你知道就算大雨让整座城市颠倒 我会给你怀抱”', '三点半官方', NULL, 'http://i1.hdslb.com/bfs/archive/e487ba9a2415e129834cdc84a49aa6a0fdfa09c4.jpg', '2026-03-16 17:00:00', 173, 799324, 253, 0, 288, 4656, 1237, 153, 21881, 0, NULL, '2026-03-17 23:00:57');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (260, 'BV1VAwmzyEPq', 116239196423379, '【本家投稿】キャンデー / r-906 feat. 鏡音リン', 'r-906_arukuremu', NULL, 'http://i2.hdslb.com/bfs/archive/b4edc9070484bb17665b458cb30f04ab1c710c22.jpg', '2026-03-16 22:00:01', 181, 103290, 294, 0, 978, 10122, 7175, 3781, 21495, 0, NULL, '2026-03-17 23:00:57');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (289, 'BV1QdcozNEgT', 116208577874112, '大师，我悟了！', '天天吃八碗', NULL, 'http://i1.hdslb.com/bfs/archive/17118b6d1281fd0dab53b1a8e3c6e82a7defd0c8.jpg', '2026-03-11 12:14:04', 81, 2483654, 1422, 0, 3441, 33278, 11332, 21009, 127479, 0, NULL, '2026-03-17 23:00:57');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (294, 'BV1rgwjzqE4A', 116237333956508, '【MrBeast官方】与前任们生活30天赢25万美元', 'MrBeast官方账号', NULL, 'http://i2.hdslb.com/bfs/archive/f253b2eeb7380f180af143501974b0551574225a.jpg', '2026-03-16 18:30:00', 1655, 884126, 3650, 0, 1810, 23238, 4898, 3915, 44159, 0, NULL, '2026-03-17 23:00:57');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (298, 'BV1tzwjzmEV9', 116237082303961, '欧布物语:超越次元与天空的极限', '朱梵枫', NULL, 'http://i0.hdslb.com/bfs/archive/e94b0b53e9d645530ae9f002ea98459385e9d442.jpg', '2026-03-16 13:08:02', 486, 206632, 864, 0, 561, 6302, 5923, 1326, 14940, 0, NULL, '2026-03-17 23:00:57');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (299, 'BV1WxwLzBEpm', 116237887676229, '30年伏笔一次性收完，结局直接看傻 生化危机9到底讲了个什么故事？【D9蒙太奇】', '黑椒墨鱼', NULL, 'http://i2.hdslb.com/bfs/archive/a29df5d7320f8a156330d939446567fd03437b01.jpg', '2026-03-16 18:15:32', 1416, 211177, 647, 0, 399, 3643, 769, 109, 22036, 0, NULL, '2026-03-17 23:00:57');
INSERT INTO `popular_videos` (`id`, `bvid`, `aid`, `title`, `author`, `tname`, `cover_url`, `publish_date`, `duration`, `view_count`, `danmaku_count`, `reply_count`, `comment_count`, `favorite_count`, `coin_count`, `share_count`, `like_count`, `score`, `rcmd_reason`, `scraped_at`) VALUES (300, 'BV1akcDzSEmt', 116221244606216, '小猫变成白丝美少女？小时候看过却记不起名字的动漫', '喜欢数码的陈同学', NULL, 'http://i1.hdslb.com/bfs/archive/4328126542310a6385b825494cf429131d54578e.jpg', '2026-03-13 18:19:18', 770, 213675, 1082, 0, 670, 5051, 761, 114, 8904, 0, NULL, '2026-03-17 23:00:57');
COMMIT;

-- ----------------------------
-- Table structure for project
-- ----------------------------
DROP TABLE IF EXISTS `project`;
CREATE TABLE `project` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `user_id` bigint NOT NULL,
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `keywords` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'JSON array of tracked keywords, e.g. ["小米14", "续航"]',
  `target_bvids` text COLLATE utf8mb4_unicode_ci COMMENT 'JSON array of target BV numbers',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_created_at` (`created_at`),
  CONSTRAINT `fk_project_user` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Records of project
-- ----------------------------
BEGIN;
COMMIT;

-- ----------------------------
-- Table structure for sentiment_timeline
-- ----------------------------
DROP TABLE IF EXISTS `sentiment_timeline`;
CREATE TABLE `sentiment_timeline` (
  `timeline_id` bigint NOT NULL AUTO_INCREMENT,
  `bvid` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `task_id` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `timeline_json` json NOT NULL COMMENT 'ECharts compatible JSON array of [timeIndex, sentimentScore]',
  `aspect_sentiment_json` json DEFAULT NULL COMMENT 'JSON object of aspect -> average sentiment',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`timeline_id`),
  UNIQUE KEY `uk_task_id` (`task_id`),
  KEY `idx_bvid` (`bvid`),
  CONSTRAINT `fk_timeline_task` FOREIGN KEY (`task_id`) REFERENCES `analysis_task` (`task_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Records of sentiment_timeline
-- ----------------------------
BEGIN;
COMMIT;

-- ----------------------------
-- Table structure for user
-- ----------------------------
DROP TABLE IF EXISTS `user`;
CREATE TABLE `user` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `username` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `password_hash` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `email` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `role` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'BRAND' COMMENT 'CREATOR (UP主) / BRAND (品牌方) / ADMIN',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  `bili_sessdata` text CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci COMMENT 'B站SESSDATA cookie',
  `bili_jct` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'B站bili_jct cookie',
  `bili_buvid3` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'B站buvid3 cookie',
  `bili_login_at` datetime DEFAULT NULL COMMENT 'B站最近登录时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_username` (`username`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Records of user
-- ----------------------------
BEGIN;
INSERT INTO `user` (`id`, `username`, `password_hash`, `email`, `role`, `created_at`, `updated_at`, `bili_sessdata`, `bili_jct`, `bili_buvid3`, `bili_login_at`) VALUES (1, 'konata', '$2a$10$CQVRjYGSqcBqxDBYSzSPiudU4IfJZph0MY5lAPkPsOHmpHfmS8GFu', NULL, 'CREATOR', '2026-03-17 21:45:04', '2026-03-17 22:58:53', 'b3bd291b%2C1789311533%2C62f95%2A31CjCqHJ6o88ZYfIFKFlPe0pf4wIP6MVBRIcMGV13_YBkAjYMMpwWXfvhiPTEXET4h9KoSVnpDTnhhZlk5Z1ZWZzRVaUhWMEZqR3BEUlZ2UGM0cG1IMGpaV0xhT1FzVlU3YmdneGFxYUZQSmpiQlRHVXJLbEZLWkVFVFdTdmFIQXh1dUc2bjNnbnJBIIEC', NULL, NULL, '2026-03-17 22:58:53');
COMMIT;

-- ----------------------------
-- Table structure for video_comment
-- ----------------------------
DROP TABLE IF EXISTS `video_comment`;
CREATE TABLE `video_comment` (
  `comment_id` bigint NOT NULL AUTO_INCREMENT,
  `bvid` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `task_id` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `username` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `gender` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT '未知',
  `content` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `sentiment_score` decimal(5,4) DEFAULT NULL COMMENT '0.0000 to 1.0000',
  `sentiment_label` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'POSITIVE, NEUTRAL, NEGATIVE',
  `like_count` int DEFAULT '0',
  `reply_count` int DEFAULT '0',
  `aspect` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'Aspect/Dimension (e.g., 外观, 性能, 价格)',
  `publish_time` datetime DEFAULT NULL,
  `scraped_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`comment_id`),
  KEY `idx_bvid` (`bvid`),
  KEY `idx_task_id` (`task_id`),
  KEY `idx_sentiment` (`sentiment_label`),
  KEY `idx_aspect` (`aspect`),
  CONSTRAINT `fk_comment_task` FOREIGN KEY (`task_id`) REFERENCES `analysis_task` (`task_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Records of video_comment
-- ----------------------------
BEGIN;
COMMIT;

-- ----------------------------
-- Table structure for video_danmaku
-- ----------------------------
DROP TABLE IF EXISTS `video_danmaku`;
CREATE TABLE `video_danmaku` (
  `danmaku_id` bigint NOT NULL AUTO_INCREMENT,
  `bvid` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `task_id` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `content` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `dm_time` int NOT NULL COMMENT 'Time in video (seconds)',
  `appear_time` int DEFAULT '0' COMMENT 'Same as dm_time, duplicate for compatibility',
  `send_time` datetime DEFAULT NULL COMMENT 'When the danmaku was actually sent',
  `sentiment_score` decimal(5,4) DEFAULT NULL COMMENT '0.0000 to 1.0000',
  `sentiment_label` varchar(10) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'POSITIVE, NEUTRAL, NEGATIVE',
  `scraped_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`danmaku_id`),
  KEY `idx_bvid` (`bvid`),
  KEY `idx_task_id` (`task_id`),
  KEY `idx_dm_time` (`dm_time`),
  KEY `idx_sentiment` (`sentiment_label`),
  CONSTRAINT `fk_danmaku_task` FOREIGN KEY (`task_id`) REFERENCES `analysis_task` (`task_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Records of video_danmaku
-- ----------------------------
BEGIN;
COMMIT;

-- ----------------------------
-- Table structure for video_info
-- ----------------------------
DROP TABLE IF EXISTS `video_info`;
CREATE TABLE `video_info` (
  `bvid` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `aid` bigint NOT NULL,
  `title` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `author` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `publish_date` datetime NOT NULL,
  `duration` int DEFAULT NULL,
  `view_count` int DEFAULT '0',
  `like_count` int DEFAULT '0',
  `coin_count` int DEFAULT '0',
  `fav_count` int DEFAULT '0',
  `share_count` int DEFAULT '0',
  `danmaku_count` int DEFAULT '0',
  `reply_count` int DEFAULT '0',
  `cover_url` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `scraped_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `last_analyzed_at` datetime DEFAULT NULL,
  `analysis_count` int DEFAULT '0',
  PRIMARY KEY (`bvid`),
  UNIQUE KEY `uk_aid` (`aid`),
  KEY `idx_author` (`author`),
  KEY `idx_publish_date` (`publish_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ----------------------------
-- Records of video_info
-- ----------------------------
BEGIN;
COMMIT;

-- ----------------------------
-- Triggers structure for table video_danmaku
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_danmaku_before_insert`;
delimiter ;;
CREATE TRIGGER `bili_insight_db`.`trg_danmaku_before_insert` BEFORE INSERT ON `video_danmaku` FOR EACH ROW BEGIN
    IF NEW.appear_time IS NULL OR NEW.appear_time = 0 THEN
        SET NEW.appear_time = NEW.dm_time;
    END IF;
END
;;
delimiter ;

-- ----------------------------
-- Triggers structure for table video_danmaku
-- ----------------------------
DROP TRIGGER IF EXISTS `trg_danmaku_before_update`;
delimiter ;;
CREATE TRIGGER `bili_insight_db`.`trg_danmaku_before_update` BEFORE UPDATE ON `video_danmaku` FOR EACH ROW BEGIN
    IF NEW.appear_time IS NULL OR NEW.appear_time = 0 THEN
        SET NEW.appear_time = NEW.dm_time;
    END IF;
END
;;
delimiter ;

SET FOREIGN_KEY_CHECKS = 1;
