// src/main/java/com/ecut/bili_insight/service/impl/PythonExecutorService.java

package com.ecut.bili_insight.service.impl;

import com.ecut.bili_insight.config.PythonExecutorProperties; // 导入配置属性类
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.concurrent.TimeUnit;

@Service
public class PythonExecutorService {

    private final PythonExecutorProperties properties;

    // 使用构造函数注入配置属性，这是Spring推荐的方式
    @Autowired
    public PythonExecutorService(PythonExecutorProperties properties) {
        this.properties = properties;
    }

    /**
     * 执行一个Python脚本并返回其标准输出。
     * @param relativeScriptPath 脚本相对于scripts目录的路径，例如 "login/qr_generate.py" 或 "danmaku_scraper.py"
     * @param args 传递给脚本的命令行参数
     * @return 脚本的标准输出字符串
     * @throws Exception 如果脚本执行失败或超时
     */
    public String executeScript(String relativeScriptPath, String... args) throws Exception {

        // 1. 使用配置动态构建命令和脚本的完整路径
        Path scriptPath = Paths.get(properties.getScriptsDirectory(), relativeScriptPath);

        List<String> command = new ArrayList<>();
        command.add(properties.getCommand());
        command.add(scriptPath.toString()); // 使用相对路径
        Collections.addAll(command, args);

        // 2. 创建并启动进程
        ProcessBuilder processBuilder = new ProcessBuilder(command);
        processBuilder.redirectErrorStream(true);

        System.out.println("Executing command: " + String.join(" ", processBuilder.command()));
        Process process = processBuilder.start();

        // 3. 读取脚本输出 (已包含UTF-8编码处理)
        StringBuilder output = new StringBuilder();
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(process.getInputStream(), StandardCharsets.UTF_8))) {
            String line;
            while ((line = reader.readLine()) != null) {
                output.append(line).append(System.lineSeparator()); // 保留换行符
            }
        }

        // 4. 等待进程结束并检查退出码
        if (!process.waitFor(60, TimeUnit.SECONDS)) { // 增加到60秒超时
            process.destroy();
            throw new RuntimeException("Python script execution timed out for: " + relativeScriptPath);
        }

        int exitCode = process.exitValue();
        if (exitCode != 0) {
            throw new RuntimeException("Python script [" + relativeScriptPath + "] failed with exit code " + exitCode + ". Output:\n" + output);
        }

        return output.toString().trim();
    }
}