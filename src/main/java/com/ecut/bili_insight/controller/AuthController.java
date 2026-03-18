package com.ecut.bili_insight.controller;

import com.ecut.bili_insight.entity.User;
import com.ecut.bili_insight.service.UserService;
import com.ecut.bili_insight.util.JwtUtil;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/insight/auth")
public class AuthController {

    @Autowired
    private UserService userService;

    @Autowired
    private PasswordEncoder passwordEncoder;

    @Autowired
    private JwtUtil jwtUtil;

    @PostMapping("/register")
    public ResponseEntity<?> register(@RequestBody User user) {
        if (user.getUsername() == null || user.getUsername().trim().isEmpty()) {
            return ResponseEntity.badRequest().body("用户名不能为空");
        }
        if (user.getPassword() == null || user.getPassword().trim().isEmpty()) {
            return ResponseEntity.badRequest().body("密码不能为空");
        }
        if (userService.findByUsername(user.getUsername()) != null) {
            return ResponseEntity.badRequest().body("用户名已存在");
        }
        if (user.getRole() == null || user.getRole().trim().isEmpty()) {
            user.setRole("CREATOR");
        }
        // 只保留合法角色
        if (!user.getRole().equals("CREATOR") && !user.getRole().equals("BRAND")) {
            user.setRole("CREATOR");
        }
        // email 为空字符串时置 null
        if (user.getEmail() != null && user.getEmail().trim().isEmpty()) {
            user.setEmail(null);
        }
        try {
            userService.register(user);
            return ResponseEntity.ok("注册成功");
        } catch (Exception e) {
            return ResponseEntity.status(500).body("注册失败：" + e.getMessage());
        }
    }

    @PostMapping("/login")
    public ResponseEntity<?> login(@RequestBody User loginReq) {
        User user = userService.findByUsername(loginReq.getUsername());
        if (user == null || !passwordEncoder.matches(loginReq.getPassword(), user.getPassword())) {
            return ResponseEntity.status(401).body("用户名或密码错误");
        }

        // JWT 中嵌入 userId，避免后续请求再查 DB
        String token = jwtUtil.generateToken(user.getUsername(), user.getRole(), user.getId());

        Map<String, Object> response = new HashMap<>();
        response.put("token", token);
        response.put("userId", user.getId());
        response.put("username", user.getUsername());
        response.put("role", user.getRole());
        response.put("email", user.getEmail());
        // 告诉前端是否已绑定B站账号
        response.put("biliLinked", user.getBiliSessdata() != null && !user.getBiliSessdata().isEmpty());
        return ResponseEntity.ok(response);
    }

    /** 获取当前登录用户的信息（含B站绑定状态） */
    @GetMapping("/me")
    public ResponseEntity<?> me(@org.springframework.web.bind.annotation.RequestHeader("Authorization") String authHeader) {
        try {
            String token = authHeader.replace("Bearer ", "").trim();
            String username = jwtUtil.extractUsername(token);
            User user = userService.findByUsername(username);
            if (user == null) return ResponseEntity.status(404).body("用户不存在");

            Map<String, Object> info = new HashMap<>();
            info.put("userId", user.getId());
            info.put("username", user.getUsername());
            info.put("role", user.getRole());
            info.put("email", user.getEmail());
            info.put("biliLinked", user.getBiliSessdata() != null && !user.getBiliSessdata().isEmpty());
            info.put("biliLoginAt", user.getBiliLoginAt());
            return ResponseEntity.ok(info);
        } catch (Exception e) {
            return ResponseEntity.status(401).body("Token无效");
        }
    }
}
