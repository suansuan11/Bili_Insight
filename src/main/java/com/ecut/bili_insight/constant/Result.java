package com.ecut.bili_insight.constant;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.Getter;
import lombok.NoArgsConstructor;

@NoArgsConstructor
@Getter // 只生成Getter，因为字段是final，不需要Setter
public class Result<T> {
    private Integer code;   // 业务状态码
    private String message; // 提示信息
    private T data;         // 响应数据

    // 私有化构造函数，强制使用静态工厂方法
    private Result(Integer code, String message, T data) {
        this.code = code;
        this.message = message;
        this.data = data;
    }

    /**
     * 成功返回结果（带数据）
     */
    public static <T> Result<T> success(T data) {
        return new Result<>(ResultCode.SUCCESS.getCode(), ResultCode.SUCCESS.getMessage(), data);
    }

    /**
     * 成功返回结果（不带数据）
     */
    public static <T> Result<T> success() {
        return success(null);
    }

    /**
     * 通用失败返回结果
     */
    public static <T> Result<T> failed(IErrorCode errorCode) {
        return new Result<>(errorCode.getCode(), errorCode.getMessage(), null);
    }

    /**
     * 通用失败返回结果（可自定义提示信息）
     */
    public static <T> Result<T> failed(IErrorCode errorCode, String message) {
        return new Result<>(errorCode.getCode(), message, null);
    }

    /**
     * 通用失败返回结果（使用默认的“操作失败”提示）
     */
    public static <T> Result<T> failed() {
        return failed(ResultCode.FAILED);
    }

    /**
     * 参数验证失败返回结果
     */
    public static <T> Result<T> validateFailed() {
        return failed(ResultCode.VALIDATE_FAILED);
    }

    /**
     * 参数验证失败返回结果（可自定义提示信息）
     */
    public static <T> Result<T> validateFailed(String message) {
        return failed(ResultCode.VALIDATE_FAILED, message);
    }

    /**
     * 未登录返回结果
     */
    public static <T> Result<T> unauthorized(T data) {
        return new Result<>(ResultCode.UNAUTHORIZED.getCode(), ResultCode.UNAUTHORIZED.getMessage(), data);
    }

    /**
     * 未授权返回结果
     */
    public static <T> Result<T> forbidden(T data) {
        return new Result<>(ResultCode.FORBIDDEN.getCode(), ResultCode.FORBIDDEN.getMessage(), data);
    }

    /**
     * 资源未找到返回结果
     */
    public static <T> Result<T> notFound(T data) {
        return new Result<>(ResultCode.NOT_FOUND.getCode(), ResultCode.NOT_FOUND.getMessage(), data);
    }
}