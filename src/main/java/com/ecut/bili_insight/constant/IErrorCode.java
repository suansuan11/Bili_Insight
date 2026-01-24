package com.ecut.bili_insight.constant;
/**
 * 封装API的错误码规范
 */
public interface IErrorCode {
    /**
     * 获取业务状态码
     * @return 状态码
     */
    Integer getCode();

    /**
     * 获取状态码对应的提示信息
     * @return 提示信息
     */
    String getMessage();
}