package com.ecut.bili_insight.task;

import com.ecut.bili_insight.service.IPopularVideosService;
import com.ecut.bili_insight.service.PythonApiClient;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Component;

import javax.annotation.PreDestroy;
import java.io.File;
import java.util.Arrays;
import java.util.List;

/**
 * 应用启动初始化器
 *
 * 1. 检测 Python 服务是否已在运行
 * 2. 若未运行且配置了启动命令，则自动拉起 Python 进程
 * 3. 等待 Python 服务健康检查通过
 * 4. 触发热门视频数据初始化
 * 5. Java 关闭时自动 kill 由本进程启动的 Python 子进程
 */
@Component
public class StartupDataInitializer implements ApplicationRunner {

    private static final Logger logger = LoggerFactory.getLogger(StartupDataInitializer.class);

    private final IPopularVideosService popularVideosService;
    private final PythonApiClient pythonApiClient;

    /** 记录由本实例启动的 Python 子进程，用于关闭时 kill */
    private Process pythonProcess;

    @Value("${python.service.working-directory:python_service}")
    private String pythonWorkingDirectory;

    @Value("${python.service.start-command:}")
    private String pythonStartCommand;

    @Value("${python.service.health-check-timeout:30}")
    private int healthCheckTimeoutSeconds;

    public StartupDataInitializer(IPopularVideosService popularVideosService,
                                   PythonApiClient pythonApiClient) {
        this.popularVideosService = popularVideosService;
        this.pythonApiClient = pythonApiClient;
    }

    @Override
    @Async
    public void run(ApplicationArguments args) {
        logger.info("[启动] 开始初始化 Python 服务...");

        try {
            ensurePythonServiceRunning();
        } catch (Exception e) {
            logger.error("[启动] Python 服务启动失败，跳过热门视频初始化: {}", e.getMessage());
            return;
        }

        // Python 服务就绪后触发热门视频爬取
        try {
            popularVideosService.refreshAndSavePopularVideos();
            logger.info("[启动] 热门视频数据初始化任务已提交");
        } catch (Exception e) {
            logger.warn("[启动] 热门视频初始化失败（不影响运行）: {}", e.getMessage());
        }
    }

    /**
     * Java 关闭时自动停止由本进程启动的 Python 子进程
     */
    @PreDestroy
    public void stopPythonProcess() {
        if (pythonProcess == null) {
            logger.info("[关闭] 未检测到由Java启动的Python进程，无需关闭");
            return;
        }

        if (!pythonProcess.isAlive()) {
            logger.info("[关闭] Python进程已停止");
            return;
        }

        logger.info("[关闭] 检测到Python子进程运行中，发送SIGTERM信号，等待优雅关闭...");
        pythonProcess.destroy();

        try {
            if (!pythonProcess.waitFor(5, java.util.concurrent.TimeUnit.SECONDS)) {
                logger.warn("[关闭] Python进程5秒内未响应，发送SIGKILL强制终止");
                pythonProcess.destroyForcibly();
                pythonProcess.waitFor(2, java.util.concurrent.TimeUnit.SECONDS);
                logger.info("[关闭] Python进程已强制终止");
            } else {
                int exitCode = pythonProcess.exitValue();
                logger.info("[关闭] Python进程已正常退出，退出码: {}", exitCode);
            }
        } catch (InterruptedException e) {
            logger.error("[关闭] 等待Python进程退出时被中断，强制终止");
            pythonProcess.destroyForcibly();
            Thread.currentThread().interrupt();
        }
    }

    /**
     * 确保 Python 服务处于运行状态：
     * - 已在运行：直接返回
     * - 未运行且配置了启动命令：拉起进程并等待健康检查通过
     * - 未运行且无启动命令：抛出异常
     */
    private void ensurePythonServiceRunning() throws Exception {
        boolean isRunning = pythonApiClient.checkHealth();
        
        if (isRunning) {
            logger.info("[启动] Python 服务已在运行，跳过启动");
            return;
        }

        logger.info("[启动] Python 服务未运行，准备启动...");
        
        if (pythonStartCommand == null || pythonStartCommand.trim().isEmpty()) {
            throw new IllegalStateException(
                "Python 服务未运行，且未配置 python.service.start-command，请手动启动后重试");
        }

        startPythonProcess();
        waitForPythonHealthy();
    }

    /**
     * 使用 ProcessBuilder 拉起 Python 服务进程，并保存引用供关闭时使用
     */
    private void startPythonProcess() throws Exception {
        List<String> command = Arrays.asList(pythonStartCommand.trim().split("\\s+"));
        logger.info("[启动] 正在拉起 Python 服务: {}", String.join(" ", command));

        File workDir = resolveWorkingDirectory();
        logger.info("[启动] Python 工作目录: {}", workDir.getAbsolutePath());

        ProcessBuilder pb = new ProcessBuilder(command);
        pb.directory(workDir);
        pb.inheritIO();
        pythonProcess = pb.start();

        logger.info("[启动] Python 进程已启动，等待服务就绪...");
    }

    /**
     * 轮询健康检查，直到服务就绪或超时
     */
    private void waitForPythonHealthy() throws Exception {
        int waited = 0;
        int intervalSeconds = 2;

        while (waited < healthCheckTimeoutSeconds) {
            Thread.sleep(intervalSeconds * 1000L);
            waited += intervalSeconds;

            if (pythonApiClient.checkHealth()) {
                logger.info("[启动] Python 服务已就绪（等待 {}s）", waited);
                return;
            }
            logger.info("[启动] 等待 Python 服务就绪... ({}/{}s)", waited, healthCheckTimeoutSeconds);
        }

        throw new IllegalStateException(
            "Python 服务在 " + healthCheckTimeoutSeconds + "s 内未就绪，请检查日志");
    }

    /**
     * 解析工作目录：支持绝对路径和相对路径（相对于项目根目录）
     */
    private File resolveWorkingDirectory() {
        File dir = new File(pythonWorkingDirectory);
        if (!dir.isAbsolute()) {
            dir = new File(System.getProperty("user.dir"), pythonWorkingDirectory);
        }
        if (!dir.exists()) {
            throw new IllegalArgumentException(
                "Python 服务目录不存在: " + dir.getAbsolutePath());
        }
        return dir;
    }
}
