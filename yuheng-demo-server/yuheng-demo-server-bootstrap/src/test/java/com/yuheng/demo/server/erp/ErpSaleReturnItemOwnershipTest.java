package com.yuheng.demo.server.erp;

import com.yuheng.demo.module.erp.controller.admin.sale.vo.returns.ErpSaleReturnSaveReqVO;
import com.yuheng.demo.module.erp.dal.dataobject.sale.ErpSaleReturnItemDO;
import com.yuheng.demo.module.erp.dal.mysql.sale.ErpSaleReturnItemMapper;
import com.yuheng.demo.module.erp.service.sale.ErpSaleReturnServiceImpl;
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

class ErpSaleReturnItemOwnershipTest {
    private ErpSaleReturnServiceImpl service;
    private ErpSaleReturnItemMapper mapper;
    private Method updateItems;

    @BeforeEach
    void setup() throws Exception {
        service = new ErpSaleReturnServiceImpl();
        mapper = mock(ErpSaleReturnItemMapper.class);
        ReflectionTestUtils.setField(service, "saleReturnItemMapper", mapper);
        when(mapper.selectListByReturnId(1L)).thenReturn(List.of(item(10L)));
        updateItems = ErpSaleReturnServiceImpl.class.getDeclaredMethod("updateSaleReturnItemList", Long.class, List.class);
        updateItems.setAccessible(true);
    }

    private ErpSaleReturnItemDO item(Long id) {
        return ErpSaleReturnItemDO.builder().id(id).build();
    }

    @Test
    void rejectForeignMissingAndDuplicateIds() {
        for (List<ErpSaleReturnItemDO> items : List.of(List.of(item(20L)), List.of(item(999L)),
                List.of(item(10L), item(10L)))) {
            InvocationTargetException thrown = assertThrows(InvocationTargetException.class,
                    () -> updateItems.invoke(service, 1L, items));
            assertInstanceOf(ServiceException.class, thrown.getCause());
            assertEquals(1020203009, ((ServiceException) thrown.getCause()).getCode());
        }
        verify(mapper, never()).insertBatch(any());
        verify(mapper, never()).updateBatch(any(java.util.Collection.class));
        verify(mapper, never()).deleteByIds(any());
    }

    @Test
    void createRejectsClientSuppliedItemId() {
        ErpSaleReturnSaveReqVO.Item item = new ErpSaleReturnSaveReqVO.Item();
        item.setId(20L);
        ErpSaleReturnSaveReqVO request = new ErpSaleReturnSaveReqVO();
        request.setItems(List.of(item));
        ServiceException thrown = assertThrows(ServiceException.class, () -> service.createSaleReturn(request));
        assertEquals(1020203009, thrown.getCode());
    }

    @Test
    void acceptsCurrentItemAndNewItem() throws Exception {
        updateItems.invoke(service, 1L, List.of(item(10L), item(null)));
        verify(mapper).insertBatch(any());
        verify(mapper).updateBatch(any(java.util.Collection.class));
        verify(mapper, never()).deleteByIds(any());
    }
}
