<template>
  <div class="comment-list">
    <div class="filters">
      <el-select v-model="sentimentFilter" placeholder="情感倾向" clearable>
        <el-option label="😊 正面" value="POSITIVE" />
        <el-option label="😐 中性" value="NEUTRAL" />
        <el-option label="😞 负面" value="NEGATIVE" />
      </el-select>

      <el-select v-model="aspectFilter" placeholder="讨论维度" clearable style="margin-left: 12px">
        <el-option v-for="aspect in aspects" :key="aspect" :label="aspect" :value="aspect" />
      </el-select>

      <span class="filter-count">
        筛选结果：<strong>{{ filteredComments.length }}</strong> / {{ comments.length }} 条
      </span>
    </div>

    <div v-if="paginatedComments.length === 0" class="no-comments">
      <el-empty description="暂无评论数据" :image-size="80" />
    </div>

    <div v-else class="comments-container">
      <div v-for="comment in paginatedComments" :key="comment.commentId || comment.comment_id" class="comment-card">
        <div class="comment-header">
          <span class="username">{{ comment.username || comment.author }}</span>
          <span class="like-count" v-if="comment.likeCount || comment.like_count">
            <el-icon><Star /></el-icon>
            {{ comment.likeCount || comment.like_count }}
          </span>
        </div>
        <div class="comment-content">{{ comment.content }}</div>
        <div class="comment-footer">
          <el-tag size="small" :type="getSentimentType(comment.sentimentLabel || comment.sentiment_label)">
            {{ formatSentimentLabel(comment.sentimentLabel || comment.sentiment_label) }}
          </el-tag>
          <el-tag size="small" type="info" v-if="comment.aspect">{{ comment.aspect }}</el-tag>
        </div>
      </div>
    </div>

    <el-pagination
      v-if="filteredComments.length > pageSize"
      v-model:current-page="currentPage"
      :page-size="pageSize"
      :total="filteredComments.length"
      layout="total, prev, pager, next"
      style="margin-top: 20px; justify-content: center"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { Star } from '@element-plus/icons-vue'

const props = defineProps<{
  comments: any[]
}>()

const sentimentFilter = ref('')
const aspectFilter = ref('')
const currentPage = ref(1)
const pageSize = 20

// 监听筛选条件变化，重置分页
watch([sentimentFilter, aspectFilter], () => {
  currentPage.value = 1
})

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

const paginatedComments = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return filteredComments.value.slice(start, start + pageSize)
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
  padding: 20px;
}

.filters {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.filter-count {
  margin-left: auto;
  font-size: 14px;
  color: #606266;
}

.filter-count strong {
  color: #409eff;
  font-weight: 600;
}

.comments-container {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.comment-card {
  padding: 16px;
  background: #fff;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  transition: all 0.2s;
}

.comment-card:hover {
  border-color: #409eff;
  box-shadow: 0 2px 12px rgba(64, 158, 255, 0.1);
}

.comment-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.username {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.like-count {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: #909399;
}

.comment-content {
  font-size: 14px;
  line-height: 1.6;
  color: #606266;
  margin-bottom: 12px;
}

.comment-footer {
  display: flex;
  gap: 8px;
}
</style>
