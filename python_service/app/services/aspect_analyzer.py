"""
Aspect 情感分析模块
实现"候选召回 + 针对 aspect 的情感二次判别"
"""
from typing import List, Dict, Optional
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

    # B站通用 aspect 关键词库（与 video_storage_service 保持一致的分类体系）
    DEFAULT_ASPECT_KEYWORDS = {
        # 数码/产品类
        "外观": ["外观", "颜值", "设计", "外形", "好看", "漂亮", "丑", "美", "造型", "外壳", "配色"],
        "性能": ["性能", "配置", "速度", "快", "慢", "卡", "流畅", "处理器", "芯片", "帧率", "延迟"],
        "价格": ["价格", "贵", "便宜", "性价比", "值", "划算", "钱", "元", "块", "折扣", "优惠"],
        "续航": ["续航", "电池", "耗电", "充电", "电量", "待机", "掉电"],
        "拍照": ["拍照", "摄像", "相机", "照片", "镜头", "像素", "夜拍", "画质"],
        "屏幕": ["屏幕", "显示", "分辨率", "刷新率", "亮度", "色彩", "护眼"],
        "系统": ["系统", "软件", "界面", "UI", "操作", "体验", "功能", "更新"],
        "售后": ["售后", "服务", "维修", "保修", "客服", "退换"],
        # 美食/食品类
        "口味": ["好吃", "难吃", "味道", "口感", "香", "甜", "咸", "辣", "酸", "苦", "鲜", "腻"],
        "食材": ["食材", "原料", "配料", "新鲜", "食品", "原材料", "用料"],
        "分量": ["分量", "份量", "量大", "量少"],
        "环境": ["环境", "装修", "氛围", "干净", "卫生", "位置"],
        # 内容/视频类
        "内容": ["内容", "干货", "有用", "没用", "信息量", "知识", "教程", "讲解"],
        "剪辑": ["剪辑", "节奏", "画面", "特效", "转场", "字幕", "配乐", "bgm"],
        "主播": ["主播", "up主", "up", "博主", "作者", "讲得", "说得", "表达", "幽默"],
        # 游戏类
        "玩法": ["玩法", "操作", "手感", "机制", "模式", "难度", "平衡"],
        # 通用情感
        "整体": ["总体", "整体", "总的来说", "综合", "推荐", "不推荐", "值得", "后悔"],
    }

    def __init__(self, sentiment_analyzer=None, aspect_keywords: Optional[Dict] = None):
        """
        Args:
            sentiment_analyzer: SentimentAnalyzer 实例，用于 aspect 情感判别
            aspect_keywords: 自定义 aspect 关键词库，None 则使用默认库
        """
        self.sentiment_analyzer = sentiment_analyzer
        self.aspect_keywords = aspect_keywords or self.DEFAULT_ASPECT_KEYWORDS

    def _extract_aspect_context(self, text: str, aspect: str) -> str:
        """
        尽量抽取与当前 aspect 更相关的局部上下文，避免所有 aspect 继承整句情绪。
        """
        keywords = self.aspect_keywords.get(aspect, [])
        if not keywords:
            return text

        clauses = re.split(r"[，。！？!?；;]|但是|但|不过|然而|只是|就是|却|而是", text)
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
        hit = []
        for aspect, keywords in self.aspect_keywords.items():
            if any(keyword in text for keyword in keywords):
                hit.append(aspect)
        return hit

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

        # 候选召回
        aspects = self.recall_aspects(text)
        if not aspects:
            return []

        results = []
        for aspect in aspects:
            context = self._extract_aspect_context(text, aspect)
            try:
                pair_result = self.sentiment_analyzer.analyze_aspect(
                    aspect, context, text_type=text_type
                )
                results.append({
                    "aspect": aspect,
                    "label": pair_result["label"],
                    "score": pair_result["score"],
                    "confidence": pair_result["confidence"],
                    "source": pair_result.get("source", ""),
                    "version": pair_result.get("version", ""),
                    "context": context,
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
        return max(aspect_details, key=lambda x: x.get("confidence", 0))["aspect"]
