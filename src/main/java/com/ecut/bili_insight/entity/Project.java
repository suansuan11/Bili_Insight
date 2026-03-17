package com.ecut.bili_insight.entity;

import lombok.Data;
import java.time.LocalDateTime;

@Data
public class Project {
    private Long id;
    private Long userId;
    private String name;
    private String description;
    private String keywords;
    private String targetBvids;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
