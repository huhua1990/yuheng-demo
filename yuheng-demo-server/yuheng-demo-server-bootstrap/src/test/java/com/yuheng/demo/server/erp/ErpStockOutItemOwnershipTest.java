package com.yuheng.demo.server.erp;

import com.yuheng.demo.module.erp.controller.admin.stock.vo.out.ErpStockOutSaveReqVO;
import com.yuheng.demo.module.erp.dal.dataobject.stock.ErpStockOutItemDO;
import com.yuheng.demo.module.erp.dal.mysql.stock.ErpStockOutItemMapper;
import com.yuheng.demo.module.erp.service.stock.ErpStockOutServiceImpl;
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

class ErpStockOutItemOwnershipTest {
    private ErpStockOutServiceImpl service;
    private ErpStockOutItemMapper mapper;
    private Method updateItems;

    @BeforeEach
    void setup() throws Exception {
        service = new ErpStockOutServiceImpl();
        mapper = mock(ErpStockOutItemMapper.class);
        ReflectionTestUtils.setField(service, "stockOutItemMapper", mapper);
        when(mapper.selectListByOutId(1L)).thenReturn(List.of(item(10L)));
        updateItems = ErpStockOutServiceImpl.class.getDeclaredMethod("updateStockOutItemList", Long.class, List.class);
        updateItems.setAccessible(true);
    }

    private ErpStockOutItemDO item(Long id) {
        return ErpStockOutItemDO.builder().id(id).build();
    }

    @Test
    void rejectForeignMissingAndDuplicateIds() {
        for (List<ErpStockOutItemDO> items : List.of(List.of(item(20L)), List.of(item(999L)),
                List.of(item(10L), item(10L)))) {
            InvocationTargetException thrown = assertThrows(InvocationTargetException.class,
                    () -> updateItems.invoke(service, 1L, items));
            assertInstanceOf(ServiceException.class, thrown.getCause());
            assertEquals(1030402099, ((ServiceException) thrown.getCause()).getCode());
        }
        verify(mapper, never()).insertBatch(any());
        verify(mapper, never()).updateBatch(any(java.util.Collection.class));
        verify(mapper, never()).deleteByIds(any());
    }

    @Test
    void createRejectsClientSuppliedItemId() {
        ErpStockOutSaveReqVO.Item item = new ErpStockOutSaveReqVO.Item();
        item.setId(20L);
        ErpStockOutSaveReqVO request = new ErpStockOutSaveReqVO();
        request.setItems(List.of(item));
        ServiceException thrown = assertThrows(ServiceException.class, () -> service.createStockOut(request));
        assertEquals(1030402099, thrown.getCode());
    }

    @Test
    void acceptsCurrentItemAndNewItem() throws Exception {
        updateItems.invoke(service, 1L, List.of(item(10L), item(null)));
        verify(mapper).insertBatch(any());
        verify(mapper).updateBatch(any(java.util.Collection.class));
        verify(mapper, never()).deleteByIds(any());
    }
}
