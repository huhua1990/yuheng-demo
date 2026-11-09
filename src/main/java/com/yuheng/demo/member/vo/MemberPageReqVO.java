package com.yuheng.demo.member.vo;

import com.yuheng.platform.framework.common.pojo.PageParam;
import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.ToString;
import org.springframework.format.annotation.DateTimeFormat;

import java.time.LocalDateTime;

import static com.yuheng.platform.framework.common.util.date.DateUtils.FORMAT_YEAR_MONTH_DAY_HOUR_MINUTE_SECOND;

/**
 * 会员分页查询 Request VO
 *
 * @author Yuheng
 */
@Schema(description = "管理后台 - 会员分页查询 Request VO")
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
public class MemberPageReqVO extends PageParam {

    @Schema(description = "会员昵称", example = "张三")
    private String nickname;

    @Schema(description = "手机号", example = "13800138000")
    private String mobile;

    @Schema(description = "会员等级ID", example = "1")
    private Long levelId;

    @Schema(description = "状态", example = "0")
    private Integer status;

    @Schema(description = "创建时间")
    @DateTimeFormat(pattern = FORMAT_YEAR_MONTH_DAY_HOUR_MINUTE_SECOND)
    private LocalDateTime[] createTime;

}
