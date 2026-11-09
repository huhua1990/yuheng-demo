package com.yuheng.demo.member.service;

import com.yuheng.platform.framework.common.pojo.PageResult;
import com.yuheng.demo.member.dal.dataobject.MemberDO;
import com.yuheng.demo.member.vo.MemberCreateReqVO;
import com.yuheng.demo.member.vo.MemberPageReqVO;
import com.yuheng.demo.member.vo.MemberUpdateReqVO;

import jakarta.validation.Valid;

/**
 * 会员 Service 接口
 *
 * @author Yuheng
 */
public interface MemberService {

    /**
     * 创建会员
     *
     * @param createReqVO 创建信息
     * @return 会员ID
     */
    Long createMember(@Valid MemberCreateReqVO createReqVO);

    /**
     * 更新会员
     *
     * @param updateReqVO 更新信息
     */
    void updateMember(@Valid MemberUpdateReqVO updateReqVO);

    /**
     * 删除会员
     *
     * @param id 会员ID
     */
    void deleteMember(Long id);

    /**
     * 获得会员
     *
     * @param id 会员ID
     * @return 会员
     */
    MemberDO getMember(Long id);

    /**
     * 获得会员分页
     *
     * @param pageReqVO 分页查询
     * @return 会员分页
     */
    PageResult<MemberDO> getMemberPage(MemberPageReqVO pageReqVO);

    // ==================== 子 Service 实现时需要实现的方法 ====================

    /**
     * 会员注册
     *
     * TODO: 需要实现
     * 1. 创建系统用户（集成 AdminUserService）
     * 2. 创建会员档案
     * 3. 发送欢迎短信（集成 SmsService）
     * 4. 初始化会员积分
     *
     * @param createReqVO 注册信息
     * @return 会员ID
     */
    // Long registerMember(@Valid MemberRegisterReqVO createReqVO);

    /**
     * 会员等级升级
     *
     * TODO: 需要实现
     * 1. 查询会员当前积分
     * 2. 根据积分确定新等级
     * 3. 更新会员等级
     * 4. 发送升级通知（短信/站内信）
     *
     * @param memberId 会员ID
     */
    // void upgradeMemberLevel(Long memberId);

    /**
     * 积分变更
     *
     * TODO: 需要实现
     * 1. 更新会员积分
     * 2. 记录积分变更历史
     * 3. 检查是否需要升级
     *
     * @param memberId 会员ID
     * @param points 积分变更数量（正数增加，负数减少）
     * @param reason 变更原因
     */
    // void changePoints(Long memberId, Integer points, String reason);

}
