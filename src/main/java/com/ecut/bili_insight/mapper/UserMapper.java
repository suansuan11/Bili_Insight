package com.ecut.bili_insight.mapper;

import com.ecut.bili_insight.entity.User;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

@Mapper
public interface UserMapper {
    User findByUsername(@Param("username") String username);
    int insert(User user);
}
