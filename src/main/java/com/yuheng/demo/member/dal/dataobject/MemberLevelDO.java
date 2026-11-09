package com.yuheng.demo.member.dal.dataobject;

import com.yuheng.platform.framework.mybatis.core.dataobject.BaseDO;
import com.baomidou.mybatisplus.annotation.KeySequence;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.*;

import java.math.BigDecimal;

/**
 * 会员等级 DO
 *
 * @author Yuheng
 */
@TableName("member_level")
@KeySequence("member_level_seq")
@Data
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class MemberLevelDO extends BaseDO {

    /**
     * 等级ID
     */
    @TableId
    private Long id;

    /**
     * 等级名称
     */
    private String name;

    /**
     * 所需积分
     */
    private Integer requiredPoint;

    /**
     * 折扣率
     *
     * 例如: 0.95 表示95折
     */
    private BigDecimal discount;

    /**
     * 等级图标URL
     */
    private String icon;

}
