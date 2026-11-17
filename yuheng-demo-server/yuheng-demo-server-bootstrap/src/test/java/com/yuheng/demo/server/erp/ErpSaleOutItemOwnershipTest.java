package com.yuheng.demo.server.erp;

import com.yuheng.demo.module.erp.controller.admin.sale.vo.out.ErpSaleOutSaveReqVO;
import com.yuheng.demo.module.erp.dal.dataobject.sale.ErpSaleOutItemDO;
import com.yuheng.demo.module.erp.dal.mysql.sale.ErpSaleOutItemMapper;
import com.yuheng.demo.module.erp.service.sale.ErpSaleOutServiceImpl;
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

class ErpSaleOutItemOwnershipTest {
    private ErpSaleOutServiceImpl service;
    private ErpSaleOutItemMapper mapper;
    private Method updateItems;

    @BeforeEach
    void setup() throws Exception {
        service = new ErpSaleOutServiceImpl();
        mapper = mock(ErpSaleOutItemMapper.class);
        ReflectionTestUtils.setField(service, "saleOutItemMapper", mapper);
        when(mapper.selectListByOutId(1L)).thenReturn(List.of(item(10L)));
        updateItems = ErpSaleOutServiceImpl.class.getDeclaredMethod("updateSaleOutItemList", Long.class, List.class);
        updateItems.setAccessible(true);
    }

    private ErpSaleOutItemDO item(Long id) {
        return ErpSaleOutItemDO.builder().id(id).build();
    }

    @Test
    void rejectForeignMissingAndDuplicateIds() {
        for (List<ErpSaleOutItemDO> items : List.of(List.of(item(20L)), List.of(item(999L)),
                List.of(item(10L), item(10L)))) {
            InvocationTargetException thrown = assertThrows(InvocationTargetException.class,
                    () -> updateItems.invoke(service, 1L, items));
            assertInstanceOf(ServiceException.class, thrown.getCause());
            assertEquals(1020202009, ((ServiceException) thrown.getCause()).getCode());
        }
        verify(mapper, never()).insertBatch(any());
        verify(mapper, never()).updateBatch(any(java.util.Collection.class));
        verify(mapper, never()).deleteByIds(any());
    }

    @Test
    void createRejectsClientSuppliedItemId() {
        ErpSaleOutSaveReqVO.Item item = new ErpSaleOutSaveReqVO.Item();
        item.setId(20L);
        ErpSaleOutSaveReqVO request = new ErpSaleOutSaveReqVO();
        request.setItems(List.of(item));
        ServiceException thrown = assertThrows(ServiceException.class, () -> service.createSaleOut(request));
        assertEquals(1020202009, thrown.getCode());
    }

    @Test
    void acceptsCurrentItemAndNewItem() throws Exception {
        updateItems.invoke(service, 1L, List.of(item(10L), item(null)));
        verify(mapper).insertBatch(any());
        verify(mapper).updateBatch(any(java.util.Collection.class));
        verify(mapper, never()).deleteByIds(any());
    }
}
