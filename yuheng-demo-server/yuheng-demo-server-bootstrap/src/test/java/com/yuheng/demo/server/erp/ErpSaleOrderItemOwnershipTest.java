package com.yuheng.demo.server.erp;

import com.yuheng.demo.module.erp.controller.admin.sale.vo.order.ErpSaleOrderSaveReqVO;
import com.yuheng.demo.module.erp.dal.dataobject.sale.ErpSaleOrderItemDO;
import com.yuheng.demo.module.erp.dal.mysql.sale.ErpSaleOrderItemMapper;
import com.yuheng.demo.module.erp.service.sale.ErpSaleOrderServiceImpl;
import com.yuheng.platform.framework.common.exception.ServiceException;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.test.util.ReflectionTestUtils;

import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

class ErpSaleOrderItemOwnershipTest {
    private ErpSaleOrderServiceImpl service;
    private ErpSaleOrderItemMapper mapper;
    private Method updateItems;

    @BeforeEach
    void setup() throws Exception {
        service = new ErpSaleOrderServiceImpl();
        mapper = mock(ErpSaleOrderItemMapper.class);
        ReflectionTestUtils.setField(service, "saleOrderItemMapper", mapper);
        when(mapper.selectListByOrderId(1L)).thenReturn(List.of(item(10L)));
        updateItems = ErpSaleOrderServiceImpl.class.getDeclaredMethod("updateSaleOrderItemList", Long.class, List.class);
        updateItems.setAccessible(true);
    }

    private ErpSaleOrderItemDO item(Long id) {
        return ErpSaleOrderItemDO.builder().id(id).build();
    }

    @Test
    void rejectForeignMissingAndDuplicateIds() {
        for (List<ErpSaleOrderItemDO> items : List.of(List.of(item(20L)), List.of(item(999L)),
                List.of(item(10L), item(10L)))) {
            InvocationTargetException thrown = assertThrows(InvocationTargetException.class,
                    () -> updateItems.invoke(service, 1L, items));
            assertInstanceOf(ServiceException.class, thrown.getCause());
            assertEquals(1020201011, ((ServiceException) thrown.getCause()).getCode());
        }
        verify(mapper, never()).insertBatch(any());
        verify(mapper, never()).updateBatch(any(java.util.Collection.class));
        verify(mapper, never()).deleteByIds(any());
    }

    @Test
    void createRejectsClientSuppliedItemId() {
        ErpSaleOrderSaveReqVO.Item item = new ErpSaleOrderSaveReqVO.Item();
        item.setId(20L);
        ErpSaleOrderSaveReqVO request = new ErpSaleOrderSaveReqVO();
        request.setItems(List.of(item));
        ServiceException thrown = assertThrows(ServiceException.class, () -> service.createSaleOrder(request));
        assertEquals(1020201011, thrown.getCode());
    }

    @Test
    void acceptsCurrentItemAndNewItem() throws Exception {
        updateItems.invoke(service, 1L, List.of(item(10L), item(null)));
        verify(mapper).insertBatch(any());
        verify(mapper).updateBatch(any(java.util.Collection.class));
        verify(mapper, never()).deleteByIds(any());
    }
}
