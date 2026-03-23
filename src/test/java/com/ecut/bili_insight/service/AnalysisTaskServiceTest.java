package com.ecut.bili_insight.service;

import com.ecut.bili_insight.entity.User;
import com.ecut.bili_insight.mapper.AnalysisTaskMapper;
import com.ecut.bili_insight.mapper.UserMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.transaction.annotation.Transactional;

import static org.junit.jupiter.api.Assertions.*;

@SpringBootTest
@Transactional
class AnalysisTaskServiceTest {

    @Autowired
    private IAnalysisTaskService analysisTaskService;

    @Autowired
    private AnalysisTaskMapper taskMapper;

    @Autowired
    private UserMapper userMapper;

    @BeforeEach
    void setup() {
        // 创建测试用户
        if (userMapper.findById(1L) == null) {
            User user1 = new User();
            user1.setId(1L);
            user1.setUsername("test_user_1");
            user1.setPassword("password");
            user1.setRole("CREATOR");
            userMapper.insert(user1);
        }

        if (userMapper.findById(2L) == null) {
            User user2 = new User();
            user2.setId(2L);
            user2.setUsername("test_user_2");
            user2.setPassword("password");
            user2.setRole("CREATOR");
            userMapper.insert(user2);
        }
    }

    @Test
    void testTaskOwnershipValidation() {
        String bvid = "BV_TEST_" + System.currentTimeMillis();
        Long userId1 = 1L;
        Long userId2 = 2L;

        // 用户1创建并完成任务
        String taskId1 = analysisTaskService.submitAnalysisTask(bvid, userId1, null);
        assertNotNull(taskId1);
        taskMapper.updateStatus(taskId1, "COMPLETED", null);

        // 用户1再次提交，应复用
        String taskId1Reuse = analysisTaskService.submitAnalysisTask(bvid, userId1, null);
        assertEquals(taskId1, taskId1Reuse);

        // 用户2提交，应创建新任务
        String taskId2 = analysisTaskService.submitAnalysisTask(bvid, userId2, null);
        assertNotEquals(taskId1, taskId2);
    }
}
