package com.yuheng.demo.server.erp;

import com.yuheng.demo.module.erp.controller.admin.stock.vo.in.ErpStockInSaveReqVO;
import com.yuheng.demo.module.erp.dal.dataobject.stock.ErpStockInItemDO;
import com.yuheng.demo.module.erp.dal.mysql.stock.ErpStockInItemMapper;
import com.yuheng.demo.module.erp.service.stock.ErpStockInServiceImpl;
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

class ErpStockInItemOwnershipTest {
    private ErpStockInServiceImpl service;
    private ErpStockInItemMapper mapper;
    private Method updateItems;

    @BeforeEach
    void setup() throws Exception {
        service = new ErpStockInServiceImpl();
        mapper = mock(ErpStockInItemMapper.class);
        ReflectionTestUtils.setField(service, "stockInItemMapper", mapper);
        when(mapper.selectListByInId(1L)).thenReturn(List.of(item(10L)));
        updateItems = ErpStockInServiceImpl.class.getDeclaredMethod("updateStockInItemList", Long.class, List.class);
        updateItems.setAccessible(true);
    }

    private ErpStockInItemDO item(Long id) {
        return ErpStockInItemDO.builder().id(id).build();
    }

    @Test
    void rejectForeignMissingAndDuplicateIds() {
        for (List<ErpStockInItemDO> items : List.of(List.of(item(20L)), List.of(item(999L)),
                List.of(item(10L), item(10L)))) {
            InvocationTargetException thrown = assertThrows(InvocationTargetException.class,
                    () -> updateItems.invoke(service, 1L, items));
            assertInstanceOf(ServiceException.class, thrown.getCause());
            assertEquals(1030401099, ((ServiceException) thrown.getCause()).getCode());
        }
        verify(mapper, never()).insertBatch(any());
        verify(mapper, never()).updateBatch(any(java.util.Collection.class));
        verify(mapper, never()).deleteByIds(any());
    }

    @Test
    void createRejectsClientSuppliedItemId() {
        ErpStockInSaveReqVO.Item item = new ErpStockInSaveReqVO.Item();
        item.setId(20L);
        ErpStockInSaveReqVO request = new ErpStockInSaveReqVO();
        request.setItems(List.of(item));
        ServiceException thrown = assertThrows(ServiceException.class, () -> service.createStockIn(request));
        assertEquals(1030401099, thrown.getCode());
    }

    @Test
    void acceptsCurrentItemAndNewItem() throws Exception {
        updateItems.invoke(service, 1L, List.of(item(10L), item(null)));
        verify(mapper).insertBatch(any());
        verify(mapper).updateBatch(any(java.util.Collection.class));
        verify(mapper, never()).deleteByIds(any());
    }
}
