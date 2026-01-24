package com.ecut.bili_insight.config;

// src/main/java/com/ecut/bili_insight/config/PythonExecutorProperties.java
import lombok.Getter;
import lombok.Setter;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

@Setter
@Getter
@Component
@ConfigurationProperties(prefix = "python.executor")
public class PythonExecutorProperties {

    // --- Getter 和 Setter ---
    /**
     * Python解释器的命令 (例如 "python" 或 "python3")
     */
    private String command;

    /**
     * 存放所有Python脚本的文件夹名称 (例如 "scripts")
     */
    private String scriptsDirectory;

    private String dataOutputDirectory;

}