package com.yuheng.demo.module.erp.dal.mysql.stock;

import cn.hutool.core.collection.CollUtil;
import cn.hutool.core.map.MapUtil;
import com.yuheng.platform.framework.common.pojo.PageResult;
import com.yuheng.platform.framework.mybatis.core.mapper.BaseMapperX;
import com.yuheng.platform.framework.mybatis.core.query.LambdaQueryWrapperX;
import com.yuheng.demo.module.erp.controller.admin.stock.vo.stock.ErpStockPageReqVO;
import com.yuheng.demo.module.erp.dal.dataobject.stock.ErpStockDO;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.core.conditions.update.LambdaUpdateWrapper;
import com.baomidou.mybatisplus.annotation.InterceptorIgnore;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Update;

import java.math.BigDecimal;
import java.util.List;
import java.util.Map;

/**
 * ERP 产品库存 Mapper
 *
 * @author 芋道源码
 */
@Mapper
public interface ErpStockMapper extends BaseMapperX<ErpStockDO> {

    default PageResult<ErpStockDO> selectPage(ErpStockPageReqVO reqVO) {
        return selectPage(reqVO, new LambdaQueryWrapperX<ErpStockDO>()
                .eqIfPresent(ErpStockDO::getProductId, reqVO.getProductId())
                .eqIfPresent(ErpStockDO::getWarehouseId, reqVO.getWarehouseId())
                .orderByDesc(ErpStockDO::getId));
    }

    default ErpStockDO selectByProductIdAndWarehouseId(Long productId, Long warehouseId) {
        return selectOne(ErpStockDO::getProductId, productId,
                ErpStockDO::getWarehouseId, warehouseId);
    }

    default ErpStockDO selectByProductIdAndWarehouseIdForUpdate(Long productId, Long warehouseId) {
        List<ErpStockDO> stocks = selectList(new LambdaQueryWrapperX<ErpStockDO>()
                .eq(ErpStockDO::getProductId, productId)
                .eq(ErpStockDO::getWarehouseId, warehouseId)
                .last("FOR UPDATE"));
        return CollUtil.getFirst(stocks);
    }

    @Update("INSERT INTO erp_stock (tenant_id, product_id, warehouse_id, `count`, deleted) " +
            "VALUES (#{tenantId}, #{productId}, #{warehouseId}, 0, b'0') " +
            "ON DUPLICATE KEY UPDATE id = id")
    @InterceptorIgnore(dataPermission = "1")
    int insertIfAbsent(@Param("tenantId") Long tenantId, @Param("productId") Long productId,
                       @Param("warehouseId") Long warehouseId);

    default int updateCountIncrement(Long id, BigDecimal count, boolean negativeEnable) {
        LambdaUpdateWrapper<ErpStockDO> updateWrapper = new LambdaUpdateWrapper<ErpStockDO>()
                .eq(ErpStockDO::getId, id);
        if (count.compareTo(BigDecimal.ZERO) > 0) {
            updateWrapper.setSql("count = count + " + count);
        } else if (count.compareTo(BigDecimal.ZERO) < 0) {
            if (!negativeEnable) {
                updateWrapper.ge(ErpStockDO::getCount, count.abs());
            }
            updateWrapper.setSql("count = count - " + count.abs());
        }
        return update(null, updateWrapper);
    }

    default BigDecimal selectSumByProductId(Long productId) {
        // SQL sum 查询
        List<Map<String, Object>> result = selectMaps(new QueryWrapper<ErpStockDO>()
                .select("SUM(count) AS sum_count")
                .eq("product_id", productId));
        // 获得数量
        if (CollUtil.isEmpty(result)) {
            return BigDecimal.ZERO;
        }
        BigDecimal sum = MapUtil.get(result.get(0), "sum_count", BigDecimal.class);
        return sum != null ? sum : BigDecimal.ZERO;
    }

}
