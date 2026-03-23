package com.ecut.bili_insight.controller;

import com.ecut.bili_insight.entity.VideoComment;
import com.ecut.bili_insight.service.IAnalysisTaskService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.nio.charset.StandardCharsets;
import java.util.List;

@RestController
@RequestMapping("/insight/export")
public class ExportController {

    @Autowired
    private IAnalysisTaskService analysisTaskService;

    @GetMapping("/comments/{taskId}")
    public ResponseEntity<byte[]> exportComments(@PathVariable String taskId) {
        List<VideoComment> comments = analysisTaskService.getComments(taskId, null, null);

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
