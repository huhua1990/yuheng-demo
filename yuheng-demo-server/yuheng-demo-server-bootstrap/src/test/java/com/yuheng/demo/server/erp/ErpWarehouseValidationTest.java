package com.yuheng.demo.server.erp;

import com.yuheng.demo.module.erp.controller.admin.stock.vo.warehouse.ErpWarehouseSaveReqVO;
import jakarta.validation.Validation;
import jakarta.validation.ValidatorFactory;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class ErpWarehouseValidationTest {

    @Test
    void acceptsNamesAtTheExistingDatabaseLimit() {
        try (ValidatorFactory factory = Validation.buildDefaultValidatorFactory()) {
            for (String character : new String[]{"a", "仓"}) {
                assertTrue(factory.getValidator().validate(request(character.repeat(20))).isEmpty());
            }
        }
    }

    @Test
    void rejectsNamesBeyondTheDatabaseLimitForCreateAndUpdate() {
        try (ValidatorFactory factory = Validation.buildDefaultValidatorFactory()) {
            for (String character : new String[]{"a", "仓"}) {
                for (Long id : new Long[]{null, 1L}) {
                    ErpWarehouseSaveReqVO request = request(character.repeat(21));
                    request.setId(id);
                    var violations = factory.getValidator().validate(request);
                    assertEquals(1, violations.size(), "21-character name must fail before persistence");
                    var violation = violations.iterator().next();
                    assertEquals("name", violation.getPropertyPath().toString());
                    assertEquals("仓库名称长度不能超过 20 个字符", violation.getMessage());
                }
            }
        }
    }

    @Test
    void preservesRequiredNameValidation() {
        try (ValidatorFactory factory = Validation.buildDefaultValidatorFactory()) {
            for (String name : new String[]{null, ""}) {
                var violations = factory.getValidator().validate(request(name));
                assertTrue(violations.stream().anyMatch(violation ->
                        "name".equals(violation.getPropertyPath().toString())
                                && "仓库名称不能为空".equals(violation.getMessage())));
            }
        }
    }

    private static ErpWarehouseSaveReqVO request(String name) {
        ErpWarehouseSaveReqVO request = new ErpWarehouseSaveReqVO();
        request.setName(name);
        request.setSort(1L);
        request.setStatus(0);
        return request;
    }
}
