# Yuheng 代码生成使用指南

## 概述

Yuheng 提供基于数据库表的标准 CRUD 代码生成能力，生成 8 类产物。

---

## 8 类产物

| 产物 | 文件名 | 说明 |
|------|--------|------|
| DO | `XxxDO.java` | 数据对象，映射数据库表 |
| Mapper | `XxxMapper.java` | MyBatis Mapper 接口 |
| Mapper.xml | `XxxMapper.xml` | MyBatis XML 映射文件 |
| Service | `XxxService.java` | 服务层，业务逻辑 |
| Controller | `XxxController.java` | 控制器，REST API |
| DTO | `XxxCreateReqDTO.java` 等 | 请求参数对象 |
| VO | `XxxRespVO.java` | 响应数据对象 |
| Convert | `XxxConvert.java` | 对象转换器（MapStruct） |

---

## 使用方式

### 方式 1: 通过 API

```java
@Resource
private CodegenService codegenService;

// 1. 创建代码生成配置
Long tableId = codegenService.createTable(new CodegenCreateReqVO()
    .setTableName("biz_product")
    .setModuleName("product"));

// 2. 生成代码
Map<String, String> codeMap = codegenService.generateCode(tableId);

// 3. 保存到文件
codeMap.forEach((filename, content) -> {
    // 保存文件...
});
```

### 方式 2: 通过 AI

```
用户："根据 biz_product 表生成 CRUD 代码"

AI：
1. 读取表结构
2. 分析字段
3. 调用 CodegenService 生成代码
4. 输出 8 类产物
```

---

## 生成规范

### DO（数据对象）

```java
@Data
@TableName("biz_product")
public class ProductDO extends BaseDO {
    
    @TableId(type = IdType.ASSIGN_ID)
    private Long id;
    
    private String name;
    private BigDecimal price;
    private Integer status;
}
```

### Mapper

```java
@Mapper
public interface ProductMapper extends BaseMapperX<ProductDO> {
    
    default PageResult<ProductDO> selectPage(ProductPageReqDTO reqDTO) {
        return selectPage(reqDTO, new LambdaQueryWrapperX<ProductDO>()
            .likeIfPresent(ProductDO::getName, reqDTO.getName())
            .eqIfPresent(ProductDO::getStatus, reqDTO.getStatus()));
    }
}
```

### Service

```java
@Service
public class ProductService extends ServiceImpl<ProductMapper, ProductDO> {
    
    public PageResult<ProductRespVO> getPage(ProductPageReqDTO reqDTO) {
        PageResult<ProductDO> pageResult = baseMapper.selectPage(reqDTO);
        return ProductConvert.INSTANCE.convertPage(pageResult);
    }
    
    @Transactional(rollbackFor = Exception.class)
    public Long create(ProductCreateReqDTO reqDTO) {
        ProductDO product = ProductConvert.INSTANCE.convert(reqDTO);
        baseMapper.insert(product);
        return product.getId();
    }
}
```

### Controller

```java
@RestController
@RequestMapping("/product")
public class ProductController {
    
    @Resource
    private ProductService productService;
    
    @PostMapping("/page")
    public CommonResult<PageResult<ProductRespVO>> page(@RequestBody ProductPageReqDTO reqDTO) {
        return CommonResult.success(productService.getPage(reqDTO));
    }
    
    @PostMapping("/create")
    public CommonResult<Long> create(@RequestBody ProductCreateReqDTO reqDTO) {
        return CommonResult.success(productService.create(reqDTO));
    }
}
```

---

## 配置选项

```java
CrudGeneratorConfig config = new CrudGeneratorConfig();
config.setTableName("biz_product");
config.setEntityName("Product");
config.setModuleName("product");
config.setPackageName("com.yuheng.platform.module.product");
config.setAuthor("yuheng");
config.setGenerateMapperXml(true);  // 是否生成 Mapper.xml
config.setGenerateTest(true);       // 是否生成测试
```

---

## AI 集成

AI 可以自动调用代码生成服务：

1. **分析表结构**：读取数据库表的字段、类型、注释
2. **构建配置**：自动构建 `CrudGeneratorConfig`
3. **生成代码**：调用 `CrudGenerator.generate()`
4. **输出结果**：返回生成的代码

---

**版本**: 0.1.0-SNAPSHOT  
**更新时间**: 2026-11-09
