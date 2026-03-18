package com.ecut.bili_insight.entity;

import lombok.Data;
import java.time.LocalDateTime;

@Data
public class User {
    private Long id;
    private String username;
    private String password;
    private String email;
    private String role;
    // B站登录凭证（由扫码登录后写入，用于提升爬虫稳定性）
    private String biliSessdata;
    private String biliJct;
    private String biliBuvid3;
    private LocalDateTime biliLoginAt;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
