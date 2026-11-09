package com.yuheng.demo.member.dal.dataobject;

import com.yuheng.platform.framework.mybatis.core.dataobject.BaseDO;
import com.baomidou.mybatisplus.annotation.KeySequence;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.*;

import java.time.LocalDate;

/**
 * 会员 DO
 *
 * @author Yuheng
 */
@TableName("member")
@KeySequence("member_seq")
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class MemberDO extends BaseDO {

    /**
     * 会员ID
     */
    @TableId
    private Long id;

    /**
     * 关联的系统用户ID
     */
    private Long userId;

    /**
     * 会员昵称
     */
    private String nickname;

    /**
     * 手机号
     */
    private String mobile;

    /**
     * 头像URL
     */
    private String avatar;

    /**
     * 会员等级ID
     */
    private Long levelId;

    /**
     * 积分
     */
    private Integer point;

    /**
     * 状态
     *
     * 枚举 {@link com.yuheng.platform.framework.common.enums.CommonStatusEnum}
     */
    private Integer status;

    /**
     * 生日
     */
    private LocalDate birthday;

    /**
     * 性别
     *
     * 枚举 1-男 2-女
     */
    private Integer gender;

}
