package com.ecut.bili_insight.util;

import java.io.BufferedReader;
import java.io.File;
import java.io.IOException;
import java.io.InputStreamReader;
import java.util.concurrent.Executors;

public class BiliCommentDownloader {

    /**
     * 调用Python脚本来下载B站评论
     *
     * @param pythonExecutablePath python解释器的路径 (例如: "python" 或 "C:\\Python39\\python.exe")
     * @param scriptPath           你的python脚本的路径 (例如: "C:\\path\\to\\comment_scraper.py")
     * @param oid                  要爬取的视频OID
     * @param outputFileName       希望保存的CSV文件名
     * @return 进程退出码 (0代表成功)
     * @throws IOException
     * @throws InterruptedException
     */
    public int runDownloader(String pythonExecutablePath, String scriptPath, String oid, String outputFileName)
            throws IOException, InterruptedException {

        // 1. 构建要执行的命令
        // 格式: python comment_scraper.py --oid <oid_value> --output <filename_value>
        ProcessBuilder processBuilder = new ProcessBuilder(
                pythonExecutablePath,
                scriptPath,
                "--oid", oid,
                "--output", outputFileName
        );

        // 2. 设置工作目录 (可选，但推荐)
        // 让脚本知道在哪里生成文件
        processBuilder.directory(new File(".")); // "." 代表当前Java程序运行的目录

        // 3. 合并错误流和输出流，方便统一查看Python脚本的打印信息
        processBuilder.redirectErrorStream(true);

        // 4. 启动进程
        System.out.println("Executing command: " + String.join(" ", processBuilder.command()));
        Process process = processBuilder.start();

        // 5. 异步读取Python脚本的输出，防止Java进程阻塞
        // 如果不读取，当Python脚本输出过多时，可能会导致缓冲区满而使子进程挂起
        Executors.newSingleThreadExecutor().submit(() -> {
            new BufferedReader(new InputStreamReader(process.getInputStream())).lines()
                    .forEach(line -> System.out.println("Python >> " + line));
        });

        // 6. 等待Python脚本执行完毕，并获取退出码
        int exitCode = process.waitFor();

        // 7. 检查结果
        if (exitCode == 0) {
            System.out.println("脚本执行成功! 评论已保存到: " + outputFileName);
        } else {
            System.err.println("脚本执行失败! 退出码: " + exitCode);
        }

        return exitCode;
    }

    public static void main(String[] args) {
        // --- 配置你的路径 ---
        // 你的Python解释器命令或绝对路径
        // 如果python已加入环境变量，可以直接用"python"或"python3"
        String pythonPath = "python";

        // 你的Python脚本的绝对路径或相对路径
        String scriptPath = "path/to/your/comment_scraper.py"; // <== 在这里填入你脚本的真实路径!

        // --- 你想从Java传入的动态参数 ---
        String oidToScrape = "847256639"; // 示例：另一个视频的OID
        String outputFile = "bili_comments_" + oidToScrape + ".csv"; // 动态生成文件名

        // --- 执行下载 ---
        BiliCommentDownloader downloader = new BiliCommentDownloader();
        try {
            downloader.runDownloader(pythonPath, scriptPath, oidToScrape, outputFile);
        } catch (IOException | InterruptedException e) {
            System.err.println("执行过程中发生错误: " + e.getMessage());
            e.printStackTrace();
        }
    }
}