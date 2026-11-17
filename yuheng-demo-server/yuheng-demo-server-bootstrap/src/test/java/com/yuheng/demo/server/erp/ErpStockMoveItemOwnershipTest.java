package com.yuheng.demo.server.erp;

import com.yuheng.demo.module.erp.controller.admin.stock.vo.move.ErpStockMoveSaveReqVO;
import com.yuheng.demo.module.erp.dal.dataobject.stock.ErpStockMoveItemDO;
import com.yuheng.demo.module.erp.dal.mysql.stock.ErpStockMoveItemMapper;
import com.yuheng.demo.module.erp.service.stock.ErpStockMoveServiceImpl;
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

class ErpStockMoveItemOwnershipTest {
    private ErpStockMoveServiceImpl service;
    private ErpStockMoveItemMapper mapper;
    private Method updateItems;

    @BeforeEach
    void setup() throws Exception {
        service = new ErpStockMoveServiceImpl();
        mapper = mock(ErpStockMoveItemMapper.class);
        ReflectionTestUtils.setField(service, "stockMoveItemMapper", mapper);
        when(mapper.selectListByMoveId(1L)).thenReturn(List.of(item(10L)));
        updateItems = ErpStockMoveServiceImpl.class.getDeclaredMethod("updateStockMoveItemList", Long.class, List.class);
        updateItems.setAccessible(true);
    }

    private ErpStockMoveItemDO item(Long id) {
        return ErpStockMoveItemDO.builder().id(id).build();
    }

    @Test
    void rejectForeignMissingAndDuplicateIds() {
        for (List<ErpStockMoveItemDO> items : List.of(List.of(item(20L)), List.of(item(999L)),
                List.of(item(10L), item(10L)))) {
            InvocationTargetException thrown = assertThrows(InvocationTargetException.class,
                    () -> updateItems.invoke(service, 1L, items));
            assertInstanceOf(ServiceException.class, thrown.getCause());
            assertEquals(1030410001, ((ServiceException) thrown.getCause()).getCode());
        }
        verify(mapper, never()).insertBatch(any());
        verify(mapper, never()).updateBatch(any(java.util.Collection.class));
        verify(mapper, never()).deleteByIds(any());
    }

    @Test
    void createRejectsClientSuppliedItemId() {
        ErpStockMoveSaveReqVO.Item item = new ErpStockMoveSaveReqVO.Item();
        item.setId(20L);
        ErpStockMoveSaveReqVO request = new ErpStockMoveSaveReqVO();
        request.setItems(List.of(item));
        ServiceException thrown = assertThrows(ServiceException.class, () -> service.createStockMove(request));
        assertEquals(1030410001, thrown.getCode());
    }

    @Test
    void acceptsCurrentItemAndNewItem() throws Exception {
        updateItems.invoke(service, 1L, List.of(item(10L), item(null)));
        verify(mapper).insertBatch(any());
        verify(mapper).updateBatch(any(java.util.Collection.class));
        verify(mapper, never()).deleteByIds(any());
    }
}
