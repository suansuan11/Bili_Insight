package com.ecut.bili_insight.mapper;

import com.ecut.bili_insight.entity.User;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

@Mapper
public interface UserMapper {
    User findByUsername(@Param("username") String username);
    User findById(@Param("id") Long id);
    int insert(User user);
    /** 扫码登录成功后，将B站凭证绑定到用户账号 */
    int updateBiliCredential(@Param("userId") Long userId,
                             @Param("sessdata") String sessdata,
                             @Param("jct") String jct,
                             @Param("buvid3") String buvid3);
}
