package com.yuheng.demo.server.erp;

import com.yuheng.demo.module.erp.controller.admin.product.vo.product.ProductSaveReqVO;
import com.yuheng.demo.module.erp.controller.admin.purchase.vo.in.ErpPurchaseInSaveReqVO;
import com.yuheng.demo.module.erp.controller.admin.purchase.vo.order.ErpPurchaseOrderSaveReqVO;
import com.yuheng.demo.module.erp.controller.admin.purchase.vo.returns.ErpPurchaseReturnSaveReqVO;
import com.yuheng.demo.module.erp.controller.admin.purchase.vo.supplier.ErpSupplierSaveReqVO;
import com.yuheng.demo.module.erp.controller.admin.sale.vo.customer.ErpCustomerSaveReqVO;
import com.yuheng.demo.module.erp.controller.admin.sale.vo.order.ErpSaleOrderSaveReqVO;
import com.yuheng.demo.module.erp.controller.admin.sale.vo.out.ErpSaleOutSaveReqVO;
import com.yuheng.demo.module.erp.controller.admin.sale.vo.returns.ErpSaleReturnSaveReqVO;
import jakarta.validation.Validation;
import jakarta.validation.Validator;
import org.junit.jupiter.api.Test;

import java.lang.reflect.Constructor;
import java.lang.reflect.Field;
import java.math.BigDecimal;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class ErpMoneyBoundsValidationTest {

    @Test
    void taxPercentagesAcceptZeroAndOneHundredAndRejectOutOfRangeValues() throws Exception {
        try (var factory = Validation.buildDefaultValidatorFactory()) {
            Validator validator = factory.getValidator();
            List<Class<?>> documentItems = List.of(
                    ErpPurchaseOrderSaveReqVO.Item.class,
                    ErpPurchaseInSaveReqVO.Item.class,
                    ErpPurchaseReturnSaveReqVO.Item.class,
                    ErpSaleOrderSaveReqVO.Item.class,
                    ErpSaleOutSaveReqVO.Item.class,
                    ErpSaleReturnSaveReqVO.Item.class
            );
            List<Class<?>> parties = List.of(ErpSupplierSaveReqVO.class, ErpCustomerSaveReqVO.class);

            for (Class<?> type : documentItems) {
                assertDecimalRange(validator, type, "taxPercent", "0", "100");
            }
            for (Class<?> type : parties) {
                assertDecimalRange(validator, type, "taxPercent", "0", "100");
            }
        }
    }

    @Test
    void productAndStockReferencePricesRejectNegativeValuesAndKeepNullOptional() throws Exception {
        try (var factory = Validation.buildDefaultValidatorFactory()) {
            Validator validator = factory.getValidator();
            assertDecimalMin(validator, ProductSaveReqVO.class, "weight", "基础重量", "0");
            assertDecimalMin(validator, ProductSaveReqVO.class, "purchasePrice", "采购价格", "0");
            assertDecimalMin(validator, ProductSaveReqVO.class, "salePrice", "销售价格", "0");
            assertDecimalMin(validator, ProductSaveReqVO.class, "minPrice", "最低价格", "0");
            assertDecimalMin(validator, ErpPurchaseOrderSaveReqVO.Item.class,
                    "productPrice", "产品单价", "0");
            assertDecimalMin(validator, com.yuheng.demo.module.erp.controller.admin.stock.vo.check.ErpStockCheckSaveReqVO.Item.class,
                    "productPrice", "产品单价", "0");
            assertDecimalMin(validator, com.yuheng.demo.module.erp.controller.admin.stock.vo.in.ErpStockInSaveReqVO.Item.class,
                    "productPrice", "产品单价", "0");
            assertDecimalMin(validator, com.yuheng.demo.module.erp.controller.admin.stock.vo.move.ErpStockMoveSaveReqVO.Item.class,
                    "productPrice", "产品单价", "0");
            assertDecimalMin(validator, com.yuheng.demo.module.erp.controller.admin.stock.vo.out.ErpStockOutSaveReqVO.Item.class,
                    "productPrice", "产品单价", "0");
        }
    }

    private static void assertDecimalRange(Validator validator, Class<?> type, String field,
                                           String minimum, String maximum) throws Exception {
        assertValue(validator, type, field, minimum, true, null);
        assertValue(validator, type, field, maximum, true, null);
        assertValue(validator, type, field, "-0.01", false, "税率不能小于 0");
        assertValue(validator, type, field, "100.01", false, "税率不能大于 100");
        assertValue(validator, type, field, null, true, null);
    }

    private static void assertDecimalMin(Validator validator, Class<?> type, String field,
                                         String label, String minimum) throws Exception {
        assertValue(validator, type, field, minimum, true, null);
        assertValue(validator, type, field, "-0.01", false, label + "不能小于 0");
        assertValue(validator, type, field, null, true, null);
    }

    private static void assertValue(Validator validator, Class<?> type, String fieldName,
                                    String value, boolean valid, String message) throws Exception {
        Constructor<?> constructor = type.getDeclaredConstructor();
        constructor.setAccessible(true);
        Object bean = constructor.newInstance();
        Field field = type.getDeclaredField(fieldName);
        field.setAccessible(true);
        field.set(bean, value == null ? null : new BigDecimal(value));
        var violations = validator.validate(bean);
        if (valid) {
            assertTrue(violations.stream().noneMatch(v -> fieldName.equals(v.getPropertyPath().toString())),
                    type.getSimpleName() + "." + fieldName + " should accept " + value);
        } else {
            var fieldViolations = violations.stream()
                    .filter(v -> fieldName.equals(v.getPropertyPath().toString()))
                    .toList();
            assertEquals(1, fieldViolations.size(),
                    type.getSimpleName() + "." + fieldName + " should reject " + value);
            assertEquals(message, fieldViolations.get(0).getMessage());
        }
    }
}
