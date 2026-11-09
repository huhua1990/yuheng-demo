package com.yuheng.demo.member.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.time.LocalDate;
import java.time.LocalDateTime;

/**
 * 会员 Response VO
 *
 * @author Yuheng
 */
@Schema(description = "管理后台 - 会员 Response VO")
@Data
public class MemberRespVO {

    @Schema(description = "会员ID", example = "1")
    private Long id;

    @Schema(description = "关联的系统用户ID", example = "100")
    private Long userId;

    @Schema(description = "会员昵称", example = "张三")
    private String nickname;

    @Schema(description = "手机号", example = "13800138000")
    private String mobile;

    @Schema(description = "头像URL", example = "https://example.com/avatar.jpg")
    private String avatar;

    @Schema(description = "会员等级ID", example = "1")
    private Long levelId;

    @Schema(description = "会员等级名称", example = "普通会员")
    private String levelName;

    @Schema(description = "积分", example = "100")
    private Integer point;

    @Schema(description = "状态", example = "0")
    private Integer status;

    @Schema(description = "生日", example = "2000-01-01")
    private LocalDate birthday;

    @Schema(description = "性别", example = "1")
    private Integer gender;

    @Schema(description = "创建时间")
    private LocalDateTime createTime;

}
