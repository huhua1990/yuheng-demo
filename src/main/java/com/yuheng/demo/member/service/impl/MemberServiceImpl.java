package com.yuheng.demo.member.service.impl;

import com.yuheng.platform.framework.common.pojo.PageResult;
import com.yuheng.platform.framework.common.util.object.BeanUtils;
import com.yuheng.demo.member.dal.dataobject.MemberDO;
import com.yuheng.demo.member.dal.mysql.MemberMapper;
import com.yuheng.demo.member.service.MemberService;
import com.yuheng.demo.member.vo.MemberCreateReqVO;
import com.yuheng.demo.member.vo.MemberPageReqVO;
import com.yuheng.demo.member.vo.MemberUpdateReqVO;
import jakarta.annotation.Resource;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.validation.annotation.Validated;

import static com.yuheng.platform.framework.common.exception.util.ServiceExceptionUtil.exception;
// import static com.yuheng.demo.member.enums.ErrorCodeConstants.*;

/**
 * 会员 Service 实现类
 *
 * 本类提供会员管理的基础 CRUD 功能（约30%完整度）
 *
 * TODO: 需要实现的功能
 * 1. 会员注册流程（集成 AdminUserService 创建系统用户）
 * 2. 会员等级升级逻辑
 * 3. 积分管理功能
 * 4. 短信通知集成（集成 SmsService）
 *
 * 使用说明：
 * 1. 注入平台服务：
 *    @Resource private AdminUserService adminUserService;
 *    @Resource private SmsService smsService;
 *
 * 2. 添加操作日志注解：
 *    @OperateLog(type = OperateTypeEnum.CREATE)
 *
 * 3. 添加权限控制（在 Controller 层）：
 *    @PreAuthorize("@ss.hasPermission('demo:member:create')")
 *
 * @author Yuheng
 */
@Service
@Validated
@Slf4j
public class MemberServiceImpl implements MemberService {

    @Resource
    private MemberMapper memberMapper;

    // TODO: 注入平台服务
    // @Resource
    // private AdminUserService adminUserService;
    //
    // @Resource
    // private SmsService smsService;
    //
    // @Resource
    // private FileService fileService;

    @Override
    @Transactional(rollbackFor = Exception.class)
    public Long createMember(MemberCreateReqVO createReqVO) {
        // TODO: 1. 校验手机号唯一性
        // validateMemberMobileUnique(null, createReqVO.getMobile());

        // 2. 插入
        MemberDO member = BeanUtils.toBean(createReqVO, MemberDO.class);

        // TODO: 3. 如果需要创建系统用户，可以在这里实现
        // UserSaveReqVO userReqVO = new UserSaveReqVO();
        // userReqVO.setUsername(createReqVO.getMobile());
        // userReqVO.setNickname(createReqVO.getNickname());
        // Long userId = adminUserService.createUser(userReqVO);
        // member.setUserId(userId);

        memberMapper.insert(member);

        return member.getId();
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void updateMember(MemberUpdateReqVO updateReqVO) {
        // 1. 校验存在
        validateMemberExists(updateReqVO.getId());

        // 2. 更新
        MemberDO updateObj = BeanUtils.toBean(updateReqVO, MemberDO.class);
        memberMapper.updateById(updateObj);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void deleteMember(Long id) {
        // 1. 校验存在
        validateMemberExists(id);

        // 2. 删除
        memberMapper.deleteById(id);
    }

    private void validateMemberExists(Long id) {
        if (memberMapper.selectById(id) == null) {
            throw new RuntimeException("会员不存在"); // TODO: 使用错误码常量
        }
    }

    // TODO: 实现手机号唯一性校验
    // private void validateMemberMobileUnique(Long id, String mobile) {
    //     MemberDO member = memberMapper.selectByMobile(mobile);
    //     if (member != null && !Objects.equals(member.getId(), id)) {
    //         throw exception(MEMBER_MOBILE_EXISTS);
    //     }
    // }

    @Override
    public MemberDO getMember(Long id) {
        return memberMapper.selectById(id);
    }

    @Override
    public PageResult<MemberDO> getMemberPage(MemberPageReqVO pageReqVO) {
        return memberMapper.selectPage(pageReqVO);
    }

    // ==================== 待实现的业务方法 ====================

    /**
     * 会员注册示例
     *
     * TODO: 实现会员注册流程
     */
    // @Override
    // @Transactional(rollbackFor = Exception.class)
    // public Long registerMember(MemberRegisterReqVO reqVO) {
    //     // 1. 校验手机号唯一性
    //     validateMemberMobileUnique(null, reqVO.getMobile());
    //
    //     // 2. 创建系统用户
    //     UserSaveReqVO userReqVO = new UserSaveReqVO();
    //     userReqVO.setUsername(reqVO.getMobile());
    //     userReqVO.setNickname(reqVO.getNickname());
    //     userReqVO.setMobile(reqVO.getMobile());
    //     Long userId = adminUserService.createUser(userReqVO);
    //
    //     // 3. 创建会员档案
    //     MemberDO member = BeanUtils.toBean(reqVO, MemberDO.class);
    //     member.setUserId(userId);
    //     member.setLevelId(1L); // 默认等级
    //     member.setPoint(100);  // 注册送100积分
    //     member.setStatus(CommonStatusEnum.ENABLE.getStatus());
    //     memberMapper.insert(member);
    //
    //     // 4. 发送欢迎短信
    //     smsService.sendSingleSms(
    //         reqVO.getMobile(),
    //         null,
    //         null,
    //         "MEMBER_WELCOME",
    //         Map.of("nickname", reqVO.getNickname())
    //     );
    //
    //     log.info("[registerMember] 会员注册成功，memberId: {}, userId: {}", member.getId(), userId);
    //     return member.getId();
    // }

    /**
     * 会员等级升级示例
     *
     * TODO: 实现等级升级逻辑
     */
    // @Override
    // @Transactional(rollbackFor = Exception.class)
    // public void upgradeMemberLevel(Long memberId) {
    //     // 1. 查询会员
    //     MemberDO member = validateMemberExists(memberId);
    //
    //     // 2. 根据积分查询应有的等级
    //     MemberLevelDO newLevel = memberLevelMapper.selectByRequiredPoint(member.getPoint());
    //
    //     // 3. 如果等级有变化，则升级
    //     if (newLevel != null && !Objects.equals(newLevel.getId(), member.getLevelId())) {
    //         MemberDO updateObj = new MemberDO();
    //         updateObj.setId(memberId);
    //         updateObj.setLevelId(newLevel.getId());
    //         memberMapper.updateById(updateObj);
    //
    //         // 4. 发送升级通知
    //         smsService.sendSingleSms(
    //             member.getMobile(),
    //             null,
    //             null,
    //             "MEMBER_LEVEL_UPGRADE",
    //             Map.of("level", newLevel.getName())
    //         );
    //
    //         log.info("[upgradeMemberLevel] 会员等级升级，memberId: {}, oldLevel: {}, newLevel: {}",
    //                  memberId, member.getLevelId(), newLevel.getId());
    //     }
    // }

    /**
     * 积分变更示例
     *
     * TODO: 实现积分管理
     */
    // @Override
    // @Transactional(rollbackFor = Exception.class)
    // public void changePoints(Long memberId, Integer points, String reason) {
    //     // 1. 查询会员
    //     MemberDO member = validateMemberExists(memberId);
    //
    //     // 2. 计算新积分
    //     int newPoints = member.getPoint() + points;
    //     if (newPoints < 0) {
    //         throw exception(MEMBER_POINT_NOT_ENOUGH);
    //     }
    //
    //     // 3. 更新积分
    //     MemberDO updateObj = new MemberDO();
    //     updateObj.setId(memberId);
    //     updateObj.setPoint(newPoints);
    //     memberMapper.updateById(updateObj);
    //
    //     // 4. 记录积分变更历史（需要创建积分历史表）
    //     // MemberPointHistoryDO history = new MemberPointHistoryDO();
    //     // history.setMemberId(memberId);
    //     // history.setPoints(points);
    //     // history.setReason(reason);
    //     // memberPointHistoryMapper.insert(history);
    //
    //     // 5. 检查是否需要升级
    //     // upgradeMemberLevel(memberId);
    //
    //     log.info("[changePoints] 会员积分变更，memberId: {}, points: {}, newPoints: {}, reason: {}",
    //              memberId, points, newPoints, reason);
    // }

}
