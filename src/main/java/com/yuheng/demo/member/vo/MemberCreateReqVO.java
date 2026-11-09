package com.yuheng.demo.member.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import java.time.LocalDate;

/**
 * 会员创建 Request VO
 *
 * @author Yuheng
 */
@Schema(description = "管理后台 - 会员创建 Request VO")
@Data
public class MemberCreateReqVO {

    @Schema(description = "会员昵称", requiredMode = Schema.RequiredMode.REQUIRED, example = "张三")
    @NotBlank(message = "会员昵称不能为空")
    private String nickname;

    @Schema(description = "手机号", requiredMode = Schema.RequiredMode.REQUIRED, example = "13800138000")
    @NotBlank(message = "手机号不能为空")
    private String mobile;

    @Schema(description = "头像URL", example = "https://example.com/avatar.jpg")
    private String avatar;

    @Schema(description = "会员等级ID", requiredMode = Schema.RequiredMode.REQUIRED, example = "1")
    @NotNull(message = "会员等级不能为空")
    private Long levelId;

    @Schema(description = "积分", example = "100")
    private Integer point;

    @Schema(description = "状态", example = "0")
    private Integer status;

    @Schema(description = "生日", example = "2000-01-01")
    private LocalDate birthday;

    @Schema(description = "性别", example = "1")
    private Integer gender;

}
