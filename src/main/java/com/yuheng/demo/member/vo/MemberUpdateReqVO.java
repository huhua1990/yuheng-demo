package com.yuheng.demo.member.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import jakarta.validation.constraints.NotNull;
import java.time.LocalDate;

/**
 * 会员更新 Request VO
 *
 * @author Yuheng
 */
@Schema(description = "管理后台 - 会员更新 Request VO")
@Data
public class MemberUpdateReqVO {

    @Schema(description = "会员ID", requiredMode = Schema.RequiredMode.REQUIRED, example = "1")
    @NotNull(message = "会员ID不能为空")
    private Long id;

    @Schema(description = "会员昵称", example = "张三")
    private String nickname;

    @Schema(description = "头像URL", example = "https://example.com/avatar.jpg")
    private String avatar;

    @Schema(description = "会员等级ID", example = "1")
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
