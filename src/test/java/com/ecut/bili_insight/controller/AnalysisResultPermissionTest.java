package com.ecut.bili_insight.controller;

import com.ecut.bili_insight.entity.AnalysisTask;
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
class AnalysisResultPermissionTest {

    @Autowired
    private IAnalysisTaskService analysisTaskService;

    @Autowired
    private AnalysisTaskMapper taskMapper;

    @Autowired
    private UserMapper userMapper;

    @BeforeEach
    void setup() {
        if (userMapper.findById(10L) == null) {
            User user = new User();
            user.setId(10L);
            user.setUsername("user_10");
            user.setPassword("pass");
            user.setRole("CREATOR");
            userMapper.insert(user);
        }
    }

    @Test
    void testAnalysisResultPermission() {
        String bvid = "BV_PERM_" + System.currentTimeMillis();
        String taskId = analysisTaskService.submitAnalysisTask(bvid, 10L, null);
        taskMapper.updateStatus(taskId, "COMPLETED", null);

        // 获取结果应该检查权限
        Map<String, Object> result = analysisTaskService.getAnalysisResult(taskId);
        assertNotNull(result);

        AnalysisTask task = (AnalysisTask) result.get("task");
        assertEquals(10L, task.getUserId(), "任务应属于用户10");
    }
}
