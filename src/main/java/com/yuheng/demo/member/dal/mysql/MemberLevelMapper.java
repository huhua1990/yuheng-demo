package com.yuheng.demo.member.dal.mysql;

import com.yuheng.platform.framework.mybatis.core.mapper.BaseMapperX;
import com.yuheng.platform.framework.mybatis.core.query.LambdaQueryWrapperX;
import com.yuheng.demo.member.dal.dataobject.MemberLevelDO;
import org.apache.ibatis.annotations.Mapper;

import java.util.List;

/**
 * 会员等级 Mapper
 *
 * @author Yuheng
 */
@Mapper
public interface MemberLevelMapper extends BaseMapperX<MemberLevelDO> {

    default List<MemberLevelDO> selectList() {
        return selectList(new LambdaQueryWrapperX<MemberLevelDO>()
                .orderByAsc(MemberLevelDO::getRequiredPoint));
    }

    default MemberLevelDO selectByName(String name) {
        return selectOne(MemberLevelDO::getName, name);
    }

}
