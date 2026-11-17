package com.yuheng.demo.module.erp.enums;

import com.yuheng.platform.framework.common.validation.InEnum;
import com.yuheng.platform.framework.common.util.validation.ValidationUtils;
import jakarta.validation.constraints.NotNull;

/** Validates status values before audit transitions reach a service. */
public final class ErpAuditStatusValidation {

    private ErpAuditStatusValidation() {
    }

    public static void validate(Integer status) {
        ValidationUtils.validate(new StatusRequest(status));
    }

    private record StatusRequest(
            @NotNull(message = "审核状态不能为空")
            @InEnum(value = ErpAuditStatus.class, message = "审核状态必须为 10 或 20")
            Integer status) {
    }
}
