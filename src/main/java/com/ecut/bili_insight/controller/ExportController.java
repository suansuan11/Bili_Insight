package com.ecut.bili_insight.controller;

import com.ecut.bili_insight.entity.VideoComment;
import com.ecut.bili_insight.entity.User;
import com.ecut.bili_insight.mapper.UserMapper;
import com.ecut.bili_insight.service.IAnalysisTaskService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;

import java.nio.charset.StandardCharsets;
import java.util.List;

@RestController
@RequestMapping("/insight/export")
public class ExportController {

    @Autowired
    private IAnalysisTaskService analysisTaskService;

    @Autowired
    private UserMapper userMapper;

    private User getCurrentUser() {
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        if (auth == null || !auth.isAuthenticated()) {
            return null;
        }
        return userMapper.findByUsername(auth.getName());
    }

    @GetMapping("/comments/{taskId}")
    public ResponseEntity<byte[]> exportComments(@PathVariable String taskId) {
        User currentUser = getCurrentUser();
        if (currentUser == null) {
            return ResponseEntity.status(401).build();
        }

        List<VideoComment> comments = analysisTaskService.getCommentsForExport(taskId, currentUser.getId());

        StringBuilder csv = new StringBuilder();
        csv.append("用户名,内容,情感倾向,维度,点赞数\n");

        for (VideoComment c : comments) {
            csv.append(escape(c.getUsername())).append(",")
               .append(escape(c.getContent())).append(",")
               .append(c.getSentimentLabel()).append(",")
               .append(c.getAspect() != null ? c.getAspect() : "").append(",")
               .append(c.getLikeCount()).append("\n");
        }

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_OCTET_STREAM);
        headers.setContentDispositionFormData("attachment", "comments_" + taskId + ".csv");

        return ResponseEntity.ok()
                .headers(headers)
                .body(csv.toString().getBytes(StandardCharsets.UTF_8));
    }

    private String escape(String s) {
        if (s == null) return "";
        return "\"" + s.replace("\"", "\"\"") + "\"";
    }
}
