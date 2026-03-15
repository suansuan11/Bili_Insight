<template>
  <div class="comment-list">
    <div class="filters">
      <el-select v-model="sentimentFilter" placeholder="Sentiment Label" clearable @change="filterComments">
        <el-option label="Positive" value="Positive" />
        <el-option label="Negative" value="Negative" />
        <el-option label="Neutral" value="Neutral" />
      </el-select>
      
      <el-select v-model="aspectFilter" placeholder="Aspect" clearable @change="filterComments" class="ml-2">
        <el-option v-for="aspect in aspects" :key="aspect" :label="aspect" :value="aspect" />
      </el-select>
    </div>
    
    <div v-if="filteredComments.length === 0" class="no-comments">
      <el-empty description="No comments found" />
    </div>

    <el-card v-for="comment in filteredComments" :key="comment.id" class="comment-item">
      <div class="comment-header">
        <span class="user">{{ comment.username }}</span>
        <span class="time">{{ comment.created_at }}</span>
      </div>
      <div class="comment-content">{{ comment.content }}</div>
      <div class="comment-tags">
        <el-tag size="small" :type="getSentimentType(comment.sentiment_label)">{{ comment.sentiment_label }}</el-tag>
        <el-tag size="small" type="info" v-if="comment.aspect" class="ml-2">{{ comment.aspect }}</el-tag>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'

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
    const matchSentiment = sentimentFilter.value ? c.sentiment_label === sentimentFilter.value : true
    const matchAspect = aspectFilter.value ? c.aspect === aspectFilter.value : true
    return matchSentiment && matchAspect
  })
})

const getSentimentType = (label: string) => {
  if (label === 'Positive') return 'success'
  if (label === 'Negative') return 'danger'
  return 'info'
}

const filterComments = () => {
  // Handled by computed automatically
}
</script>

<style scoped>
.comment-list {
  margin-top: 20px;
}
.filters {
  margin-bottom: 20px;
}
.ml-2 {
  margin-left: 8px;
}
.comment-item {
  margin-bottom: 15px;
}
.comment-header {
  font-size: 13px;
  color: #666;
  margin-bottom: 8px;
  display: flex;
  justify-content: space-between;
}
.user { font-weight: bold; color: #333; }
.comment-content {
  margin-bottom: 10px;
  font-size: 14px;
}
.comment-tags {
  display: flex;
  gap: 5px;
}
</style>
