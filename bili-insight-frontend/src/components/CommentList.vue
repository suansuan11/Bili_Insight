<template>
  <div class="comment-list">
    <div class="filters">
      <el-select v-model="sentimentFilter" placeholder="情感倾向" clearable style="width: 140px">
        <el-option label="正面" value="POSITIVE" />
        <el-option label="中性" value="NEUTRAL" />
        <el-option label="负面" value="NEGATIVE" />
      </el-select>

      <el-select v-model="aspectFilter" placeholder="讨论维度" clearable style="width: 140px; margin-left: 10px">
        <el-option v-for="aspect in aspects" :key="aspect" :label="aspect" :value="aspect" />
      </el-select>

      <span style="margin-left: 10px; color: #909399; font-size: 13px">
        共 {{ filteredComments.length }} / {{ comments.length }} 条
      </span>
    </div>

    <div v-if="filteredComments.length === 0" class="no-comments">
      <el-empty description="暂无评论数据" />
    </div>

    <el-card v-for="comment in filteredComments" :key="comment.commentId || comment.comment_id" class="comment-item">
      <div class="comment-header">
        <span class="user">{{ comment.username || comment.author }}</span>
        <span class="like" v-if="comment.likeCount || comment.like_count">
          {{ comment.likeCount || comment.like_count }} 赞
        </span>
      </div>
      <div class="comment-content">{{ comment.content }}</div>
      <div class="comment-tags">
        <el-tag size="small" :type="getSentimentType(comment.sentimentLabel || comment.sentiment_label)">
          {{ formatSentimentLabel(comment.sentimentLabel || comment.sentiment_label) }}
        </el-tag>
        <el-tag size="small" type="info" v-if="comment.aspect" style="margin-left: 6px">{{ comment.aspect }}</el-tag>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const props = defineProps<{
  comments: any[]
}>()

const sentimentFilter = ref('')
const aspectFilter = ref('')

const aspects = computed(() => {
  const set = new Set<string>()
  props.comments.forEach(c => {
    if (c.aspect) set.add(c.aspect)
  })
  return Array.from(set)
})

const filteredComments = computed(() => {
  return props.comments.filter(c => {
    const label = c.sentimentLabel || c.sentiment_label
    const matchSentiment = sentimentFilter.value ? label === sentimentFilter.value : true
    const matchAspect = aspectFilter.value ? c.aspect === aspectFilter.value : true
    return matchSentiment && matchAspect
  })
})

const getSentimentType = (label: string) => {
  if (label === 'POSITIVE') return 'success'
  if (label === 'NEGATIVE') return 'danger'
  return 'info'
}

const formatSentimentLabel = (label: string) => {
  const map: Record<string, string> = {
    'POSITIVE': '正面',
    'NEUTRAL': '中性',
    'NEGATIVE': '负面'
  }
  return map[label] || label || '未知'
}
</script>

<style scoped>
.comment-list {
  margin-top: 10px;
}
.filters {
  margin-bottom: 16px;
  display: flex;
  align-items: center;
}
.comment-item {
  margin-bottom: 12px;
}
.comment-header {
  font-size: 13px;
  color: #666;
  margin-bottom: 8px;
  display: flex;
  justify-content: space-between;
}
.user { font-weight: bold; color: #333; }
.like { color: #909399; font-size: 12px; }
.comment-content {
  margin-bottom: 10px;
  font-size: 14px;
  line-height: 1.6;
}
.comment-tags {
  display: flex;
  gap: 5px;
}
</style>
