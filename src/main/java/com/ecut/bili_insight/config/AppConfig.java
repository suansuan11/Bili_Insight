package com.ecut.bili_insight.config;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.scheduling.annotation.EnableAsync;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.web.client.RestTemplate;

/**
 * 应用程序配置类
 * 配置异步支持、HTTP客户端等
 */
@Configuration
@EnableAsync
public class AppConfig {

    /**
     * 配置RestTemplate用于HTTP调用
     */
    @Bean
    public RestTemplate restTemplate() {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(5000); // 5 seconds connect timeout
        factory.setReadTimeout(120000); // 120 seconds read timeout (for long python analysis tasks)
        return new RestTemplate(factory);
    }

    /**
     * 配置ObjectMapper用于JSON处理
     * 支持Java 8日期时间类型
     */
    @Bean
    public ObjectMapper objectMapper() {
        ObjectMapper mapper = new ObjectMapper();
        // 注册Java 8日期时间模块
        mapper.registerModule(new JavaTimeModule());
        // 禁用将日期写为时间戳的功能
        mapper.disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);
        return mapper;
    }
}
