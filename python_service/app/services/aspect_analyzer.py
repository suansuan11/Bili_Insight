"""
Aspect 情感分析模块
实现"领域推断 + 候选召回 + 局部上下文 + 针对 aspect 的情感二次判别"
"""
from typing import List, Dict, Optional, Tuple
import re
from ..utils.logger import logger


class AspectAnalyzer:
    """
    多切面情感分析器

    工作流程:
    1. 候选召回：关键词命中候选 aspect
    2. 情感二次判别：pair classification 格式 "[aspect] [SEP] [text]"
    3. 返回多 aspect 结果列表
    """

    DOMAIN_HINTS = {
        "content": ["视频", "镜头", "剧情", "舞台", "配乐", "表演", "up", "主播", "内容", "讲解", "剪辑"],
        "product": ["手机", "电脑", "耳机", "平板", "配置", "电池", "屏幕", "拍照", "系统", "价格"],
        "food": ["好吃", "难吃", "口感", "味道", "食材", "店里", "环境", "分量"],
        "game": ["游戏", "操作", "机制", "平衡", "剧情", "氪", "帧率", "优化", "玩法"],
    }

    COMMON_ASPECT_KEYWORDS = {
        "整体": ["总体", "整体", "总的来说", "综合", "推荐", "不推荐", "值得", "后悔", "一般", "不错"],
        "内容": ["内容", "信息量", "表达", "观点", "立意", "干货", "主题", "讲解", "编排"],
        "情绪": ["感动", "震撼", "治愈", "共鸣", "上头", "哭了", "泪目", "燃", "情绪"],
    }

    DOMAIN_ASPECT_KEYWORDS = {
        "content": {
            "表演": ["表演", "演出", "演技", "动作", "舞蹈", "唱功", "台风", "表现力", "业务能力"],
            "剪辑": ["剪辑", "转场", "节奏", "卡点", "特效", "字幕", "镜头语言"],
            "画面": ["画面", "镜头", "构图", "布景", "质感", "服化道", "摄影", "色调"],
            "配乐": ["配乐", "bgm", "音乐", "音效", "伴奏", "旋律"],
            "主播": ["主播", "up主", "up", "博主", "作者", "主持", "讲得", "说得"],
            "剧情": ["剧情", "故事", "叙事", "铺垫", "反转", "人设", "角色", "台词"],
            "专业度": ["专业", "专业性", "技术", "功底", "水平", "细节", "稳", "到位"],
            "造型": ["造型", "服装", "妆造", "外形", "颜值", "搭配"],
        },
        "product": {
            "外观": ["外观", "颜值", "设计", "外形", "好看", "漂亮", "丑", "造型", "外壳", "配色"],
            "性能": ["性能", "配置", "速度", "快", "慢", "卡", "流畅", "处理器", "芯片", "帧率", "延迟"],
            "价格": ["价格", "贵", "便宜", "性价比", "值", "划算", "钱", "元", "块", "折扣", "优惠"],
            "续航": ["续航", "电池", "耗电", "充电", "电量", "待机", "掉电"],
            "拍照": ["拍照", "摄像", "相机", "照片", "镜头", "像素", "夜拍", "画质"],
            "屏幕": ["屏幕", "显示", "分辨率", "刷新率", "亮度", "色彩", "护眼"],
            "系统": ["系统", "软件", "界面", "UI", "操作", "体验", "功能", "更新"],
            "售后": ["售后", "服务", "维修", "保修", "客服", "退换"],
        },
        "food": {
            "口味": ["好吃", "难吃", "味道", "口感", "香", "甜", "咸", "辣", "酸", "苦", "鲜", "腻"],
            "食材": ["食材", "原料", "配料", "新鲜", "食品", "原材料", "用料"],
            "分量": ["分量", "份量", "量大", "量少"],
            "环境": ["环境", "装修", "氛围", "干净", "卫生", "位置"],
            "价格": ["价格", "贵", "便宜", "性价比", "值", "划算"],
        },
        "game": {
            "玩法": ["玩法", "操作", "手感", "机制", "模式", "难度", "平衡"],
            "剧情": ["剧情", "故事", "角色", "叙事"],
            "画面": ["画面", "建模", "特效", "美术", "质感", "贴图"],
            "优化": ["优化", "卡顿", "掉帧", "延迟", "发热"],
            "氪金": ["氪", "抽卡", "付费", "充值", "逼氪"],
        },
    }

    def __init__(self, sentiment_analyzer=None, aspect_keywords: Optional[Dict] = None):
        """
        Args:
            sentiment_analyzer: SentimentAnalyzer 实例，用于 aspect 情感判别
            aspect_keywords: 自定义 aspect 关键词库，None 则使用默认库
        """
        self.sentiment_analyzer = sentiment_analyzer
        self.aspect_keywords = aspect_keywords or self.DOMAIN_ASPECT_KEYWORDS

    @staticmethod
    def _strip_mentions_and_noise(text: str) -> str:
        cleaned = re.sub(r"@[\w\u4e00-\u9fff\-]+", " ", text or "")
        cleaned = re.sub(r"\[[^\]]{1,12}\]", " ", cleaned)
        cleaned = re.sub(r"https?://\S+", " ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned)
        return cleaned.strip()

    @staticmethod
    def _has_meaningful_signal(text: str) -> bool:
        if not text:
            return False
        chinese_chars = re.findall(r"[\u4e00-\u9fff]", text)
        alpha_words = re.findall(r"[A-Za-z]{2,}", text)
        return len(chinese_chars) >= 2 or bool(alpha_words)

    def _prepare_text(self, text: str) -> str:
        cleaned = self._strip_mentions_and_noise(text)
        return cleaned if self._has_meaningful_signal(cleaned) else ""

    def infer_domain(self, text: str) -> str:
        text = self._prepare_text(text)
        if not text:
            return "content"
        scores = {}
        for domain, hints in self.DOMAIN_HINTS.items():
            scores[domain] = sum(1 for hint in hints if hint in text)
        best_domain = max(scores, key=scores.get) if scores else "content"
        return best_domain if scores.get(best_domain, 0) > 0 else "content"

    def _active_aspect_keywords(self, text: str) -> Dict[str, List[str]]:
        text = self._prepare_text(text)
        domain = self.infer_domain(text)
        active = dict(self.COMMON_ASPECT_KEYWORDS)
        active.update(self.aspect_keywords.get(domain, {}))
        for domain_aspects in self.aspect_keywords.values():
            for aspect, keywords in domain_aspects.items():
                if any(keyword in text for keyword in keywords):
                    active[aspect] = keywords
        return active

    def _split_clauses(self, text: str) -> List[str]:
        text = self._prepare_text(text)
        clauses = re.split(r"[，。！？!?；;]|但是|不过|然而|只是|就是|却|而是|但", text)
        return [clause.strip() for clause in clauses if clause and clause.strip()]

    def _extract_aspect_context(self, text: str, aspect: str) -> str:
        """
        尽量抽取与当前 aspect 更相关的局部上下文，避免所有 aspect 继承整句情绪。
        """
        keywords = self._active_aspect_keywords(text).get(aspect, [])
        if not keywords:
            return text

        clauses = self._split_clauses(text)
        matched = [clause.strip() for clause in clauses if clause.strip() and any(k in clause for k in keywords)]

        if matched:
            return "；".join(matched)

        return text

    def recall_aspects(self, text: str) -> List[str]:
        """
        候选 aspect 召回

        Args:
            text: 文本（建议使用 normalized_text）

        Returns:
            命中的 aspect 列表（有序，按关键词库顺序）
        """
        prepared_text = self._prepare_text(text)
        if not prepared_text:
            return []

        hit = []
        active_keywords = self._active_aspect_keywords(prepared_text)
        for aspect, keywords in active_keywords.items():
            if any(keyword in prepared_text for keyword in keywords):
                hit.append(aspect)
        return hit

    def _relevant_clauses(self, text: str, aspect: str) -> Tuple[List[str], int]:
        prepared_text = self._prepare_text(text)
        if not prepared_text:
            return ([], 0)

        active_keywords = self._active_aspect_keywords(prepared_text)
        keywords = active_keywords.get(aspect, [])
        clauses = self._split_clauses(prepared_text)
        matched = []
        mention_count = 0
        for clause in clauses:
            hit_count = sum(1 for keyword in keywords if keyword in clause)
            if hit_count > 0:
                mention_count += hit_count
                matched.append(clause)
        return (matched or [prepared_text]), mention_count

    def analyze(self, text: str, text_type: str = "comment") -> List[Dict]:
        """
        多切面情感分析

        Args:
            text: 原始文本
            text_type: 'comment' / 'danmaku'

        Returns:
            aspect 情感结果列表，每项格式：
            {
                "aspect": str,
                "label": POSITIVE / NEUTRAL / NEGATIVE,
                "score": float [-1, 1],
                "confidence": float [0, 1],
                "source": str,
                "version": str
            }
            若无 aspect 命中，返回空列表 []
        """
        if self.sentiment_analyzer is None:
            logger.warning("AspectAnalyzer: sentiment_analyzer 未注入，跳过 aspect 分析")
            return []

        prepared_text = self._prepare_text(text)
        if not prepared_text:
            return []

        # 候选召回
        aspects = self.recall_aspects(prepared_text)
        if not aspects:
            return []

        results = []
        for aspect in aspects:
            clauses, mention_count = self._relevant_clauses(prepared_text, aspect)
            try:
                score_sum = 0.0
                conf_sum = 0.0
                local_contexts = []
                local_labels = {"POSITIVE": 0, "NEUTRAL": 0, "NEGATIVE": 0}

                for clause in clauses:
                    local_contexts.append(clause)
                    pair_result = self.sentiment_analyzer.analyze_aspect(
                        aspect, clause, text_type=text_type
                    )
                    plain_result = self.sentiment_analyzer.analyze(clause, text_type=text_type)
                    sarcasm_like = "sarcasm" in (plain_result.get("emotion_tags") or [])
                    rhetorical = "？" in clause or "?" in clause or "这也" in clause or "就这" in clause
                    if sarcasm_like or rhetorical:
                        blended_score = pair_result["score"] * 0.3 + plain_result["score"] * 0.7
                    else:
                        blended_score = pair_result["score"] * 0.65 + plain_result["score"] * 0.35
                    if "这也叫" in clause or "就这" in clause:
                        blended_score -= 0.8
                    blended_score = max(-1.0, min(1.0, blended_score))
                    blended_conf = max(pair_result["confidence"], plain_result["confidence"])
                    weight = max(0.35, blended_conf) * max(1, mention_count)
                    score_sum += blended_score * weight
                    conf_sum += weight
                    local_label = pair_result["label"]
                    local_labels[local_label] = local_labels.get(local_label, 0) + 1

                final_score = round(score_sum / conf_sum, 4) if conf_sum > 0 else 0.0
                if final_score >= 0.22:
                    final_label = "POSITIVE"
                elif final_score <= -0.22:
                    final_label = "NEGATIVE"
                else:
                    final_label = "NEUTRAL"

                if max(local_labels.values()) > 1:
                    final_label = max(local_labels, key=local_labels.get)

                final_confidence = round(min(0.99, conf_sum / max(len(clauses), 1)), 4)
                if mention_count <= 0 or final_confidence < 0.52:
                    continue

                results.append({
                    "aspect": aspect,
                    "label": final_label,
                    "score": final_score,
                    "confidence": final_confidence,
                    "source": "hybrid_clause_pair_v2",
                    "version": "aspect-hybrid-v2.0.0",
                    "context": "；".join(local_contexts),
                    "mention_count": mention_count,
                })
            except Exception as e:
                logger.warning(f"aspect '{aspect}' 情感判别失败: {e}")

        return results

    def get_primary_aspect(self, aspect_details: List[Dict]) -> Optional[str]:
        """
        从多 aspect 结果中选取"主 aspect"（兼容老字段）

        策略：置信度最高的 aspect

        Args:
            aspect_details: analyze() 返回的列表

        Returns:
            主 aspect 名称，或 None
        """
        if not aspect_details:
            return None
        return max(
            aspect_details,
            key=lambda x: (x.get("mention_count", 0), x.get("confidence", 0), abs(x.get("score", 0)))
        )["aspect"]
