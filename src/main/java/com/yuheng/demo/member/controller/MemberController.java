package com.yuheng.demo.member.controller;

import com.yuheng.platform.framework.common.pojo.CommonResult;
import com.yuheng.platform.framework.common.pojo.PageResult;
import com.yuheng.platform.framework.common.util.object.BeanUtils;
import com.yuheng.demo.member.dal.dataobject.MemberDO;
import com.yuheng.demo.member.service.MemberService;
import com.yuheng.demo.member.vo.MemberCreateReqVO;
import com.yuheng.demo.member.vo.MemberPageReqVO;
import com.yuheng.demo.member.vo.MemberRespVO;
import com.yuheng.demo.member.vo.MemberUpdateReqVO;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.annotation.Resource;
import jakarta.validation.Valid;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import static com.yuheng.platform.framework.common.pojo.CommonResult.success;

/**
 * 管理后台 - 会员管理 API
 *
 * 提供会员的 CRUD 接口
 *
 * TODO: 需要添加的功能
 * 1. 会员导入导出
 * 2. 会员统计报表
 * 3. 会员标签管理
 *
 * @author Yuheng
 */
@Tag(name = "管理后台 - 会员管理")
@RestController
@RequestMapping("/demo/member")
@Validated
public class MemberController {

    @Resource
    private MemberService memberService;

    @PostMapping("/create")
    @Operation(summary = "创建会员")
    @PreAuthorize("@ss.hasPermission('demo:member:create')")
    public CommonResult<Long> createMember(@Valid @RequestBody MemberCreateReqVO createReqVO) {
        return success(memberService.createMember(createReqVO));
    }

    @PutMapping("/update")
    @Operation(summary = "更新会员")
    @PreAuthorize("@ss.hasPermission('demo:member:update')")
    public CommonResult<Boolean> updateMember(@Valid @RequestBody MemberUpdateReqVO updateReqVO) {
        memberService.updateMember(updateReqVO);
        return success(true);
    }

    @DeleteMapping("/delete")
    @Operation(summary = "删除会员")
    @Parameter(name = "id", description = "会员ID", required = true, example = "1")
    @PreAuthorize("@ss.hasPermission('demo:member:delete')")
    public CommonResult<Boolean> deleteMember(@RequestParam("id") Long id) {
        memberService.deleteMember(id);
        return success(true);
    }

    @GetMapping("/get")
    @Operation(summary = "获得会员")
    @Parameter(name = "id", description = "会员ID", required = true, example = "1")
    @PreAuthorize("@ss.hasPermission('demo:member:query')")
    public CommonResult<MemberRespVO> getMember(@RequestParam("id") Long id) {
        MemberDO member = memberService.getMember(id);
        return success(BeanUtils.toBean(member, MemberRespVO.class));
    }

    @GetMapping("/page")
    @Operation(summary = "获得会员分页")
    @PreAuthorize("@ss.hasPermission('demo:member:query')")
    public CommonResult<PageResult<MemberRespVO>> getMemberPage(@Valid MemberPageReqVO pageReqVO) {
        PageResult<MemberDO> pageResult = memberService.getMemberPage(pageReqVO);
        return success(BeanUtils.toBean(pageResult, MemberRespVO.class));
    }

    // TODO: 添加会员导出接口
    // @GetMapping("/export")
    // @Operation(summary = "导出会员 Excel")
    // @PreAuthorize("@ss.hasPermission('demo:member:export')")
    // public void exportMemberExcel(@Valid MemberPageReqVO pageReqVO,
    //                                HttpServletResponse response) throws IOException {
    //     pageReqVO.setPageSize(PAGE_SIZE_NONE);
    //     List<MemberDO> list = memberService.getMemberPage(pageReqVO).getList();
    //     ExcelUtils.write(response, "会员.xls", "数据", MemberRespVO.class,
    //             BeanUtils.toBean(list, MemberRespVO.class));
    // }

}
