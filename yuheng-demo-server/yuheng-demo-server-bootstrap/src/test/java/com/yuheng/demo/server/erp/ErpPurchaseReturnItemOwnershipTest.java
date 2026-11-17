package com.yuheng.demo.server.erp;

import com.yuheng.demo.module.erp.controller.admin.purchase.vo.returns.ErpPurchaseReturnSaveReqVO;
import com.yuheng.demo.module.erp.dal.dataobject.purchase.ErpPurchaseReturnItemDO;
import com.yuheng.demo.module.erp.dal.mysql.purchase.ErpPurchaseReturnItemMapper;
import com.yuheng.demo.module.erp.service.purchase.ErpPurchaseReturnServiceImpl;
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

class ErpPurchaseReturnItemOwnershipTest {
    private ErpPurchaseReturnServiceImpl service;
    private ErpPurchaseReturnItemMapper mapper;
    private Method updateItems;

    @BeforeEach
    void setup() throws Exception {
        service = new ErpPurchaseReturnServiceImpl();
        mapper = mock(ErpPurchaseReturnItemMapper.class);
        ReflectionTestUtils.setField(service, "purchaseReturnItemMapper", mapper);
        when(mapper.selectListByReturnId(1L)).thenReturn(List.of(item(10L)));
        updateItems = ErpPurchaseReturnServiceImpl.class.getDeclaredMethod("updatePurchaseReturnItemList", Long.class, List.class);
        updateItems.setAccessible(true);
    }

    private ErpPurchaseReturnItemDO item(Long id) {
        return ErpPurchaseReturnItemDO.builder().id(id).build();
    }

    @Test
    void rejectForeignMissingAndDuplicateIds() {
        for (List<ErpPurchaseReturnItemDO> items : List.of(List.of(item(20L)), List.of(item(999L)),
                List.of(item(10L), item(10L)))) {
            InvocationTargetException thrown = assertThrows(InvocationTargetException.class,
                    () -> updateItems.invoke(service, 1L, items));
            assertInstanceOf(ServiceException.class, thrown.getCause());
            assertEquals(1030103009, ((ServiceException) thrown.getCause()).getCode());
        }
        verify(mapper, never()).insertBatch(any());
        verify(mapper, never()).updateBatch(any(java.util.Collection.class));
        verify(mapper, never()).deleteByIds(any());
    }

    @Test
    void createRejectsClientSuppliedItemId() {
        ErpPurchaseReturnSaveReqVO.Item item = new ErpPurchaseReturnSaveReqVO.Item();
        item.setId(20L);
        ErpPurchaseReturnSaveReqVO request = new ErpPurchaseReturnSaveReqVO();
        request.setItems(List.of(item));
        ServiceException thrown = assertThrows(ServiceException.class, () -> service.createPurchaseReturn(request));
        assertEquals(1030103009, thrown.getCode());
    }

    @Test
    void acceptsCurrentItemAndNewItem() throws Exception {
        updateItems.invoke(service, 1L, List.of(item(10L), item(null)));
        verify(mapper).insertBatch(any());
        verify(mapper).updateBatch(any(java.util.Collection.class));
        verify(mapper, never()).deleteByIds(any());
    }
}
