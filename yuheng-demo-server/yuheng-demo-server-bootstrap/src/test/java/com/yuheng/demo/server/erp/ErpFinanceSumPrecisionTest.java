package com.yuheng.demo.server.erp;

import com.yuheng.demo.module.erp.dal.mysql.finance.ErpFinancePaymentItemMapper;
import com.yuheng.demo.module.erp.dal.mysql.finance.ErpFinanceReceiptItemMapper;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;
import java.util.Collections;
import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.CALLS_REAL_METHODS;
import static org.mockito.Mockito.doReturn;
import static org.mockito.Mockito.mock;

class ErpFinanceSumPrecisionTest {

    @Test
    void paymentSumPreservesMysqlDecimalAndEmptyResults() {
        ErpFinancePaymentItemMapper mapper = mock(ErpFinancePaymentItemMapper.class, CALLS_REAL_METHODS);
        for (String amount : List.of("9007199254740991.123456", "0.000001", "-9007199254740991.123456")) {
            doReturn(List.of(Map.of("payment_price_sum", new BigDecimal(amount)))).when(mapper).selectMaps(any());
            assertEquals(0, new BigDecimal(amount).compareTo(mapper.selectPaymentPriceSumByBizIdAndBizType(1L, 12)));
        }
        doReturn(List.of(Collections.emptyMap())).when(mapper).selectMaps(any());
        assertEquals(0, BigDecimal.ZERO.compareTo(mapper.selectPaymentPriceSumByBizIdAndBizType(1L, 12)));
        doReturn(Collections.emptyList()).when(mapper).selectMaps(any());
        assertEquals(0, BigDecimal.ZERO.compareTo(mapper.selectPaymentPriceSumByBizIdAndBizType(1L, 12)));
    }

    @Test
    void receiptSumPreservesMysqlDecimalAndEmptyResults() {
        ErpFinanceReceiptItemMapper mapper = mock(ErpFinanceReceiptItemMapper.class, CALLS_REAL_METHODS);
        for (String amount : List.of("9007199254740991.123456", "0.000001", "-9007199254740991.123456")) {
            doReturn(List.of(Map.of("receipt_price_sum", new BigDecimal(amount)))).when(mapper).selectMaps(any());
            assertEquals(0, new BigDecimal(amount).compareTo(mapper.selectReceiptPriceSumByBizIdAndBizType(1L, 22)));
        }
        doReturn(List.of(Collections.emptyMap())).when(mapper).selectMaps(any());
        assertEquals(0, BigDecimal.ZERO.compareTo(mapper.selectReceiptPriceSumByBizIdAndBizType(1L, 22)));
        doReturn(Collections.emptyList()).when(mapper).selectMaps(any());
        assertEquals(0, BigDecimal.ZERO.compareTo(mapper.selectReceiptPriceSumByBizIdAndBizType(1L, 22)));
    }
}
