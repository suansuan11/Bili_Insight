package com.ecut.bili_insight.business;

import com.ecut.bili_insight.entity.User;
import com.ecut.bili_insight.mapper.AnalysisTaskMapper;
import com.ecut.bili_insight.mapper.UserMapper;
import com.ecut.bili_insight.service.IAnalysisTaskService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.transaction.annotation.Transactional;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

@SpringBootTest
@Transactional
class CoreBusinessTest {

    @Autowired
    private IAnalysisTaskService analysisTaskService;

    @Autowired
    private AnalysisTaskMapper taskMapper;

    @Autowired
    private UserMapper userMapper;

    @BeforeEach
    void setup() {
        createTestUser(100L, "business_user_1");
        createTestUser(101L, "business_user_2");
    }

    private void createTestUser(Long id, String username) {
        if (userMapper.findById(id) == null) {
            User user = new User();
            user.setId(id);
            user.setUsername(username);
            user.setPassword("password");
            user.setRole("CREATOR");
            userMapper.insert(user);
        }
    }

    @Test
    void testPermissionIsolation() {
        String bvid = "BV_PERM_" + System.currentTimeMillis();

        // 用户100创建任务
        String taskId = analysisTaskService.submitAnalysisTask(bvid, 100L, null);
        taskMapper.updateStatus(taskId, "COMPLETED", null);

        // 用户100可以访问
        Map<String, Object> result = analysisTaskService.getAnalysisResult(taskId, 100L);
        assertNotNull(result);

        // 用户101不能访问
        assertThrows(RuntimeException.class, () -> {
            analysisTaskService.getAnalysisResult(taskId, 101L);
        });
    }

    @Test
    void testTaskReuseSameUser() {
        String bvid = "BV_REUSE_" + System.currentTimeMillis();

        String taskId1 = analysisTaskService.submitAnalysisTask(bvid, 100L, null);
        taskMapper.updateStatus(taskId1, "COMPLETED", null);

        String taskId2 = analysisTaskService.submitAnalysisTask(bvid, 100L, null);
        assertEquals(taskId1, taskId2, "同一用户应复用已完成任务");
    }

    @Test
    void testTaskNotReuseDifferentUser() {
        String bvid = "BV_DIFF_" + System.currentTimeMillis();

        String taskId1 = analysisTaskService.submitAnalysisTask(bvid, 100L, null);
        taskMapper.updateStatus(taskId1, "COMPLETED", null);

        String taskId2 = analysisTaskService.submitAnalysisTask(bvid, 101L, null);
        assertNotEquals(taskId1, taskId2, "不同用户应创建新任务");
    }
}
