package com.ecut.bili_insight.controller;

import com.ecut.bili_insight.entity.Project;
import com.ecut.bili_insight.entity.User;
import com.ecut.bili_insight.mapper.ProjectMapper;
import com.ecut.bili_insight.mapper.UserMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.transaction.annotation.Transactional;

import static org.junit.jupiter.api.Assertions.*;

@SpringBootTest
@Transactional
class ProjectQuotaTest {

    @Autowired
    private ProjectMapper projectMapper;

    @Autowired
    private UserMapper userMapper;

    @BeforeEach
    void setup() {
        if (userMapper.findById(999L) == null) {
            User user = new User();
            user.setId(999L);
            user.setUsername("test_quota_user");
            user.setPassword("password");
            user.setRole("BRAND");
            userMapper.insert(user);
        }
    }

    @Test
    void testProjectQuotaLimit() {
        Long userId = 999L;

        for (int i = 0; i < 10; i++) {
            Project project = new Project();
            project.setUserId(userId);
            project.setName("Test Project " + i);
            projectMapper.insert(project);
        }

        int count = projectMapper.countByUserId(userId);
        assertEquals(10, count);
    }
}
