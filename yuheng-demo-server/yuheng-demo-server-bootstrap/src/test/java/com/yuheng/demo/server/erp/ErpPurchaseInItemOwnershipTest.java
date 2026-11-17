package com.yuheng.demo.server.erp;

import com.yuheng.demo.module.erp.controller.admin.purchase.vo.in.ErpPurchaseInSaveReqVO;
import com.yuheng.demo.module.erp.dal.dataobject.purchase.ErpPurchaseInItemDO;
import com.yuheng.demo.module.erp.dal.mysql.purchase.ErpPurchaseInItemMapper;
import com.yuheng.demo.module.erp.service.purchase.ErpPurchaseInServiceImpl;
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

class ErpPurchaseInItemOwnershipTest {
    private ErpPurchaseInServiceImpl service;
    private ErpPurchaseInItemMapper mapper;
    private Method updateItems;

    @BeforeEach
    void setup() throws Exception {
        service = new ErpPurchaseInServiceImpl();
        mapper = mock(ErpPurchaseInItemMapper.class);
        ReflectionTestUtils.setField(service, "purchaseInItemMapper", mapper);
        when(mapper.selectListByInId(1L)).thenReturn(List.of(item(10L)));
        updateItems = ErpPurchaseInServiceImpl.class.getDeclaredMethod("updatePurchaseInItemList", Long.class, List.class);
        updateItems.setAccessible(true);
    }

    private ErpPurchaseInItemDO item(Long id) {
        return ErpPurchaseInItemDO.builder().id(id).build();
    }

    @Test
    void rejectForeignMissingAndDuplicateIds() {
        for (List<ErpPurchaseInItemDO> items : List.of(List.of(item(20L)), List.of(item(999L)),
                List.of(item(10L), item(10L)))) {
            InvocationTargetException thrown = assertThrows(InvocationTargetException.class,
                    () -> updateItems.invoke(service, 1L, items));
            assertInstanceOf(ServiceException.class, thrown.getCause());
            assertEquals(1030102009, ((ServiceException) thrown.getCause()).getCode());
        }
        verify(mapper, never()).insertBatch(any());
        verify(mapper, never()).updateBatch(any(java.util.Collection.class));
        verify(mapper, never()).deleteByIds(any());
    }

    @Test
    void createRejectsClientSuppliedItemId() {
        ErpPurchaseInSaveReqVO.Item item = new ErpPurchaseInSaveReqVO.Item();
        item.setId(20L);
        ErpPurchaseInSaveReqVO request = new ErpPurchaseInSaveReqVO();
        request.setItems(List.of(item));
        ServiceException thrown = assertThrows(ServiceException.class, () -> service.createPurchaseIn(request));
        assertEquals(1030102009, thrown.getCode());
    }

    @Test
    void acceptsCurrentItemAndNewItem() throws Exception {
        updateItems.invoke(service, 1L, List.of(item(10L), item(null)));
        verify(mapper).insertBatch(any());
        verify(mapper).updateBatch(any(java.util.Collection.class));
        verify(mapper, never()).deleteByIds(any());
    }
}
