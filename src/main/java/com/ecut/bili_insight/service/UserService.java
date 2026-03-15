package com.ecut.bili_insight.service;

import com.ecut.bili_insight.entity.User;

public interface UserService {
    User findByUsername(String username);
    void register(User user);
}
