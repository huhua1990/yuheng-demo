package com.yuheng.demo.module.erp.service.stock;

import com.yuheng.platform.framework.common.pojo.PageResult;
import com.yuheng.demo.module.erp.controller.admin.stock.vo.stock.ErpStockPageReqVO;
import com.yuheng.demo.module.erp.dal.dataobject.stock.ErpStockDO;
import com.yuheng.demo.module.erp.dal.mysql.stock.ErpStockMapper;
import com.yuheng.demo.module.erp.service.product.ErpProductService;
import com.yuheng.platform.framework.tenant.core.context.TenantContextHolder;
import jakarta.annotation.Resource;
import org.springframework.dao.DuplicateKeyException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.validation.annotation.Validated;

import java.math.BigDecimal;

import static com.yuheng.platform.framework.common.exception.util.ServiceExceptionUtil.exception;
import static com.yuheng.demo.module.erp.enums.ErrorCodeConstants.STOCK_COUNT_NEGATIVE;
import static com.yuheng.demo.module.erp.enums.ErrorCodeConstants.STOCK_COUNT_NEGATIVE2;

/**
 * ERP 产品库存 Service 实现类
 *
 * @author 芋道源码
 */
@Service
@Validated
public class ErpStockServiceImpl implements ErpStockService {

    /**
     * 允许库存为负数
     *
     * TODO 芋艿：后续做成 db 配置
     */
    private static final Boolean NEGATIVE_STOCK_COUNT_ENABLE = false;

    @Resource
    private ErpProductService productService;
    @Resource
    private ErpWarehouseService warehouseService;

    @Resource
    private ErpStockMapper stockMapper;

    @Override
    public ErpStockDO getStock(Long id) {
        return stockMapper.selectById(id);
    }

    @Override
    public ErpStockDO getStock(Long productId, Long warehouseId) {
        return stockMapper.selectByProductIdAndWarehouseId(productId, warehouseId);
    }

    @Override
    public BigDecimal getStockCount(Long productId) {
        BigDecimal count = stockMapper.selectSumByProductId(productId);
        return count != null ? count : BigDecimal.ZERO;
    }

    @Override
    public PageResult<ErpStockDO> getStockPage(ErpStockPageReqVO pageReqVO) {
        return stockMapper.selectPage(pageReqVO);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public BigDecimal updateStockCountIncrement(Long productId, Long warehouseId, BigDecimal count) {
        Long tenantId = TenantContextHolder.getRequiredTenantId();
        try {
            stockMapper.insertIfAbsent(tenantId, productId, warehouseId);
        } catch (DuplicateKeyException ignored) {
            // A concurrent first insert won; continue with the active row.
        }

        // Lock and read the current committed row before validating and recording its balance.
        ErpStockDO stock = stockMapper.selectByProductIdAndWarehouseIdForUpdate(productId, warehouseId);
        if (stock == null) {
            throw new IllegalStateException("Unable to initialize ERP stock row");
        }
        // 1.2 校验库存是否充足
        if (!NEGATIVE_STOCK_COUNT_ENABLE && stock.getCount().add(count).compareTo(BigDecimal.ZERO) < 0) {
            throw exception(STOCK_COUNT_NEGATIVE, productService.getProduct(productId).getName(),
                    warehouseService.getWarehouse(warehouseId).getName(), stock.getCount(), count);
        }

        // 2. 库存变更
        int updateCount = stockMapper.updateCountIncrement(stock.getId(), count, NEGATIVE_STOCK_COUNT_ENABLE);
        if (updateCount == 0) {
            // 此时不好去查询最新库存，所以直接抛出该提示，不提供具体库存数字
            throw exception(STOCK_COUNT_NEGATIVE2, productService.getProduct(productId).getName(),
                    warehouseService.getWarehouse(warehouseId).getName());
        }

        // 3. 返回最新库存
        return stockMapper.selectById(stock.getId()).getCount();
    }

}
