<template>
  <div class="projects-container">
    <div class="page-header">
      <h2>监测项目</h2>
      <el-button type="primary" @click="openCreateDialog">
        <el-icon><Plus /></el-icon>
        新建项目
      </el-button>
    </div>

    <!-- Project Cards -->
    <el-row :gutter="20" v-loading="loading">
      <el-col :xs="24" :sm="12" :lg="8" v-for="project in projects" :key="project.id">
        <el-card class="project-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span class="project-name">{{ project.name }}</span>
              <div>
                <el-button text type="primary" @click="openEditDialog(project)">
                  <el-icon><Edit /></el-icon>
                </el-button>
                <el-button text type="danger" @click="handleDelete(project)">
                  <el-icon><Delete /></el-icon>
                </el-button>
              </div>
            </div>
          </template>
          <p class="project-desc">{{ project.description || '暂无描述' }}</p>
          <div class="keyword-tags" v-if="parseKeywords(project.keywords).length">
            <el-tag
              v-for="(kw, idx) in parseKeywords(project.keywords)"
              :key="idx"
              size="small"
              type="info"
              class="keyword-tag"
            >
              {{ kw }}
            </el-tag>
          </div>
          <div class="card-footer">
            <span class="create-time">创建于 {{ formatDate(project.createdAt) }}</span>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-empty v-if="!loading && projects.length === 0" description="暂无监测项目，点击上方按钮创建" />

    <!-- Create/Edit Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑项目' : '新建项目'"
      width="560px"
      destroy-on-close
    >
      <el-form :model="form" label-width="100px" :rules="rules" ref="formRef">
        <el-form-item label="项目名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入项目名称" />
        </el-form-item>
        <el-form-item label="项目描述" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            placeholder="请输入项目描述"
          />
        </el-form-item>
        <el-form-item label="监测关键词">
          <div class="tag-input-area">
            <el-tag
              v-for="(tag, index) in keywordList"
              :key="index"
              closable
              @close="removeKeyword(index)"
              class="keyword-tag"
            >
              {{ tag }}
            </el-tag>
            <el-input
              v-if="keywordInputVisible"
              ref="keywordInputRef"
              v-model="keywordInputValue"
              size="small"
              style="width: 120px"
              @keyup.enter="addKeyword"
              @blur="addKeyword"
            />
            <el-button v-else size="small" @click="showKeywordInput">
              + 添加关键词
            </el-button>
          </div>
        </el-form-item>
        <el-form-item label="目标BVIDs">
          <el-input
            v-model="form.targetBvids"
            type="textarea"
            :rows="3"
            placeholder="输入目标视频BV号，每行一个"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitting">
          {{ isEdit ? '保存' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, nextTick, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Edit, Delete } from '@element-plus/icons-vue'
import { getProjects, createProject, updateProject, deleteProject } from '@/api/project'
import type { ProjectData } from '@/api/project'
import type { FormInstance } from 'element-plus'
import { useUserSettings } from '@/composables/useUserSettings'

const { formatDate } = useUserSettings()

const loading = ref(false)
const submitting = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const editingId = ref<number | null>(null)
const projects = ref<ProjectData[]>([])
const formRef = ref<FormInstance>()

const form = reactive({
  name: '',
  description: '',
  targetBvids: ''
})

const rules = {
  name: [{ required: true, message: '请输入项目名称', trigger: 'blur' }]
}

// Keyword tag input state
const keywordList = ref<string[]>([])
const keywordInputVisible = ref(false)
const keywordInputValue = ref('')
const keywordInputRef = ref<InstanceType<typeof import('element-plus')['ElInput']>>()

const fetchProjects = async () => {
  loading.value = true
  try {
    const res = await getProjects()
    projects.value = res.data || []
  } catch (e) {
    ElMessage.error('获取项目列表失败')
  } finally {
    loading.value = false
  }
}

const parseKeywords = (keywords?: string): string[] => {
  if (!keywords) return []
  try {
    const parsed = JSON.parse(keywords)
    return Array.isArray(parsed) ? parsed : []
  } catch {
    return []
  }
}

const formatTargetBvidsForTextarea = (targetBvids?: string): string => {
  if (!targetBvids) return ''
  try {
    const parsed = JSON.parse(targetBvids)
    if (Array.isArray(parsed)) {
      return parsed.filter((item): item is string => typeof item === 'string').join('\n')
    }
  } catch {
    // 兼容旧格式项目
  }

  return targetBvids
    .split(/[\n,，]+/)
    .map(item => item.trim())
    .filter(Boolean)
    .join('\n')
}



const openCreateDialog = () => {
  isEdit.value = false
  editingId.value = null
  form.name = ''
  form.description = ''
  form.targetBvids = ''
  keywordList.value = []
  dialogVisible.value = true
}

const openEditDialog = (project: ProjectData) => {
  isEdit.value = true
  editingId.value = project.id!
  form.name = project.name
  form.description = project.description || ''
  form.targetBvids = formatTargetBvidsForTextarea(project.targetBvids)
  keywordList.value = parseKeywords(project.keywords)
  dialogVisible.value = true
}

const showKeywordInput = () => {
  keywordInputVisible.value = true
  nextTick(() => {
    keywordInputRef.value?.input?.focus()
  })
}

const addKeyword = () => {
  const val = keywordInputValue.value.trim()
  if (val && !keywordList.value.includes(val)) {
    keywordList.value.push(val)
  }
  keywordInputVisible.value = false
  keywordInputValue.value = ''
}

const removeKeyword = (index: number) => {
  keywordList.value.splice(index, 1)
}

const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate()

  submitting.value = true
  try {
    const data: ProjectData = {
      name: form.name,
      description: form.description,
      keywords: JSON.stringify(keywordList.value),
      targetBvids: form.targetBvids
    }

    if (isEdit.value && editingId.value !== null) {
      await updateProject(editingId.value, data)
      ElMessage.success('项目更新成功')
    } else {
      await createProject(data)
      ElMessage.success('项目创建成功')
    }

    dialogVisible.value = false
    await fetchProjects()
  } catch (e) {
    ElMessage.error(isEdit.value ? '更新失败' : '创建失败')
  } finally {
    submitting.value = false
  }
}

const handleDelete = (project: ProjectData) => {
  ElMessageBox.confirm(
    `确定要删除项目「${project.name}」吗？此操作不可撤销。`,
    '删除确认',
    { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' }
  ).then(async () => {
    try {
      await deleteProject(project.id!)
      ElMessage.success('删除成功')
      await fetchProjects()
    } catch (e) {
      ElMessage.error('删除失败')
    }
  }).catch(() => {})
}

onMounted(() => {
  fetchProjects()
})
</script>

<style scoped>
.projects-container {
  padding: 24px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-header h2 {
  margin: 0;
  font-size: 22px;
  color: #303133;
}

.project-card {
  margin-bottom: 20px;
  border-radius: 12px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.project-name {
  font-weight: 600;
  font-size: 16px;
}

.project-desc {
  color: #606266;
  font-size: 14px;
  margin: 0 0 12px 0;
  line-height: 1.6;
}

.keyword-tags {
  margin-bottom: 12px;
}

.keyword-tag {
  margin-right: 6px;
  margin-bottom: 4px;
}

.card-footer {
  border-top: 1px solid #f0f0f0;
  padding-top: 10px;
}

.create-time {
  font-size: 12px;
  color: #909399;
}

.tag-input-area {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}
</style>
