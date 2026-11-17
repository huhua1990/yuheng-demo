package com.yuheng.demo.server.erp;

import com.yuheng.demo.module.erp.controller.admin.stock.vo.check.ErpStockCheckSaveReqVO;
import com.yuheng.demo.module.erp.dal.dataobject.stock.ErpStockCheckItemDO;
import com.yuheng.demo.module.erp.dal.mysql.stock.ErpStockCheckItemMapper;
import com.yuheng.demo.module.erp.service.stock.ErpStockCheckServiceImpl;
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

class ErpStockCheckItemOwnershipTest {
    private ErpStockCheckServiceImpl service;
    private ErpStockCheckItemMapper mapper;
    private Method updateItems;

    @BeforeEach
    void setup() throws Exception {
        service = new ErpStockCheckServiceImpl();
        mapper = mock(ErpStockCheckItemMapper.class);
        ReflectionTestUtils.setField(service, "stockCheckItemMapper", mapper);
        when(mapper.selectListByCheckId(1L)).thenReturn(List.of(item(10L)));
        updateItems = ErpStockCheckServiceImpl.class.getDeclaredMethod("updateStockCheckItemList", Long.class, List.class);
        updateItems.setAccessible(true);
    }

    private ErpStockCheckItemDO item(Long id) {
        return ErpStockCheckItemDO.builder().id(id).build();
    }

    @Test
    void rejectForeignMissingAndDuplicateIds() {
        for (List<ErpStockCheckItemDO> items : List.of(List.of(item(20L)), List.of(item(999L)),
                List.of(item(10L), item(10L)))) {
            InvocationTargetException thrown = assertThrows(InvocationTargetException.class,
                    () -> updateItems.invoke(service, 1L, items));
            assertInstanceOf(ServiceException.class, thrown.getCause());
            assertEquals(1030410000, ((ServiceException) thrown.getCause()).getCode());
        }
        verify(mapper, never()).insertBatch(any());
        verify(mapper, never()).updateBatch(any(java.util.Collection.class));
        verify(mapper, never()).deleteByIds(any());
    }

    @Test
    void createRejectsClientSuppliedItemId() {
        ErpStockCheckSaveReqVO.Item item = new ErpStockCheckSaveReqVO.Item();
        item.setId(20L);
        ErpStockCheckSaveReqVO request = new ErpStockCheckSaveReqVO();
        request.setItems(List.of(item));
        ServiceException thrown = assertThrows(ServiceException.class, () -> service.createStockCheck(request));
        assertEquals(1030410000, thrown.getCode());
    }

    @Test
    void acceptsCurrentItemAndNewItem() throws Exception {
        updateItems.invoke(service, 1L, List.of(item(10L), item(null)));
        verify(mapper).insertBatch(any());
        verify(mapper).updateBatch(any(java.util.Collection.class));
        verify(mapper, never()).deleteByIds(any());
    }
}
