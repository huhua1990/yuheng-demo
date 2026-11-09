#!/bin/bash
# Yuheng Demo - 添加业务模块脚本
# 用法: ./scripts/add-module.sh <module-name> [template-name]
# 示例: ./scripts/add-module.sh member

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

MODULE_NAME=$1
TEMPLATE_NAME=${2:-template-$MODULE_NAME}

if [ -z "$MODULE_NAME" ]; then
    echo -e "${RED}❌ 用法: ./scripts/add-module.sh <module-name> [template-name]${NC}"
    echo -e "${YELLOW}示例: ./scripts/add-module.sh member${NC}"
    exit 1
fi

echo -e "${BLUE}🚀 开始添加业务模块: ${MODULE_NAME}${NC}"
echo ""

# 1. 检查模板库
TEMPLATE_DIR="../yuheng-business-templates"
if [ ! -d "$TEMPLATE_DIR" ]; then
    echo -e "${YELLOW}📦 模板库不存在，正在克隆...${NC}"
    git clone https://github.com/huhua1990/yuheng-business-templates.git "$TEMPLATE_DIR"
    echo -e "${GREEN}✓ 模板库克隆完成${NC}"
else
    echo -e "${GREEN}✓ 模板库已存在${NC}"
    # 更新模板库
    echo -e "${YELLOW}📦 更新模板库...${NC}"
    cd "$TEMPLATE_DIR"
    git pull origin main || git pull origin master || true
    cd - > /dev/null
fi

echo ""

# 2. 检查模板是否存在
if [ ! -d "$TEMPLATE_DIR/$TEMPLATE_NAME" ]; then
    echo -e "${RED}❌ 模板 ${TEMPLATE_NAME} 不存在${NC}"
    echo -e "${YELLOW}可用的模板:${NC}"
    ls -1 "$TEMPLATE_DIR" | grep "^template-" || echo "  (模板库中暂无模板)"
    exit 1
fi

echo -e "${GREEN}✓ 找到模板: ${TEMPLATE_NAME}${NC}"
echo ""

# 3. 拷贝后端代码
echo -e "${BLUE}📋 拷贝后端代码...${NC}"
BACKEND_SRC="$TEMPLATE_DIR/$TEMPLATE_NAME/src/main/java/com/yuheng/template/$MODULE_NAME"
BACKEND_DEST="src/main/java/com/yuheng/demo/$MODULE_NAME"

if [ -d "$BACKEND_SRC" ]; then
    mkdir -p "$BACKEND_DEST"
    cp -r "$BACKEND_SRC/"* "$BACKEND_DEST/" 2>/dev/null || true
    echo -e "${GREEN}✓ 后端代码拷贝完成${NC}"
else
    echo -e "${YELLOW}⚠ 模板中没有后端代码，跳过${NC}"
fi

# 4. 拷贝数据库脚本
echo -e "${BLUE}📋 拷贝数据库脚本...${NC}"
SQL_SRC="$TEMPLATE_DIR/$TEMPLATE_NAME/src/main/resources/sql"
SQL_DEST="src/main/resources/db/changelog/$MODULE_NAME"

if [ -d "$SQL_SRC" ]; then
    mkdir -p "$SQL_DEST"
    cp -r "$SQL_SRC/"* "$SQL_DEST/" 2>/dev/null || true
    # 重命名 SQL 文件
    for file in "$SQL_DEST"/*.sql; do
        if [ -f "$file" ]; then
            basename=$(basename "$file")
            if [[ ! "$basename" =~ ^[0-9] ]]; then
                mv "$file" "$SQL_DEST/001-$MODULE_NAME-init.sql"
            fi
        fi
    done
    echo -e "${GREEN}✓ 数据库脚本拷贝完成${NC}"
else
    echo -e "${YELLOW}⚠ 模板中没有数据库脚本，跳过${NC}"
fi

# 5. 拷贝前端代码
echo -e "${BLUE}📋 拷贝前端代码...${NC}"
UI_SRC="$TEMPLATE_DIR/$TEMPLATE_NAME/ui/views/$MODULE_NAME"
UI_DEST="yuheng-demo-ui/src/views/$MODULE_NAME"

if [ -d "$UI_SRC" ]; then
    mkdir -p "$UI_DEST"
    cp -r "$UI_SRC/"* "$UI_DEST/" 2>/dev/null || true
    echo -e "${GREEN}✓ 前端代码拷贝完成${NC}"
else
    echo -e "${YELLOW}⚠ 模板中没有前端代码，跳过${NC}"
fi

# 6. 拷贝前端 API
API_SRC="$TEMPLATE_DIR/$TEMPLATE_NAME/ui/api/$MODULE_NAME"
API_DEST="yuheng-demo-ui/src/api/demo"

if [ -d "$API_SRC" ]; then
    mkdir -p "$API_DEST"
    cp -r "$API_SRC/"* "$API_DEST/" 2>/dev/null || true
    echo -e "${GREEN}✓ 前端 API 拷贝完成${NC}"
fi

echo ""

# 7. 批量替换包名
echo -e "${BLUE}🔄 更新 Java 包名...${NC}"
if [ -d "$BACKEND_DEST" ]; then
    find "$BACKEND_DEST" -type f -name "*.java" \
        -exec sed -i '' "s/com\.yuheng\.template\.$MODULE_NAME/com.yuheng.demo.$MODULE_NAME/g" {} + 2>/dev/null || \
        find "$BACKEND_DEST" -type f -name "*.java" \
        -exec sed -i "s/com\.yuheng\.template\.$MODULE_NAME/com.yuheng.demo.$MODULE_NAME/g" {} + 2>/dev/null || true

    # 更新导入语句
    find "$BACKEND_DEST" -type f -name "*.java" \
        -exec sed -i '' 's/import com\.yuheng\.template/import com.yuheng.demo/g' {} + 2>/dev/null || \
        find "$BACKEND_DEST" -type f -name "*.java" \
        -exec sed -i 's/import com\.yuheng\.template/import com.yuheng.demo/g' {} + 2>/dev/null || true

    echo -e "${GREEN}✓ Java 包名更新完成${NC}"
fi

# 8. 更新前端 API 路径
echo -e "${BLUE}🔄 更新前端 API 路径...${NC}"
if [ -d "$UI_DEST" ] || [ -d "$API_DEST" ]; then
    find "$UI_DEST" "$API_DEST" -type f \( -name "*.vue" -o -name "*.ts" \) 2>/dev/null | while read file; do
        sed -i '' "s|/template/$MODULE_NAME|/demo/$MODULE_NAME|g" "$file" 2>/dev/null || \
        sed -i "s|/template/$MODULE_NAME|/demo/$MODULE_NAME|g" "$file" 2>/dev/null || true
    done
    echo -e "${GREEN}✓ 前端 API 路径更新完成${NC}"
fi

echo ""

# 9. 更新数据库变更日志
echo -e "${BLUE}🔄 更新数据库变更日志...${NC}"
CHANGELOG_FILE="src/main/resources/db/changelog/db.changelog-master.yaml"

if [ -f "$CHANGELOG_FILE" ]; then
    if ! grep -q "db/changelog/$MODULE_NAME" "$CHANGELOG_FILE" 2>/dev/null; then
        echo "  - include:" >> "$CHANGELOG_FILE"
        echo "      file: db/changelog/$MODULE_NAME/001-$MODULE_NAME-init.sql" >> "$CHANGELOG_FILE"
        echo -e "${GREEN}✓ 数据库变更日志已更新${NC}"
    else
        echo -e "${YELLOW}⚠ 变更日志中已存在该模块，跳过${NC}"
    fi
else
    echo -e "${YELLOW}⚠ 数据库变更日志文件不存在，跳过${NC}"
fi

echo ""

# 10. 编译检查
echo -e "${BLUE}🔨 编译检查...${NC}"
if command -v mvn &> /dev/null; then
    if mvn clean compile -DskipTests -q; then
        echo -e "${GREEN}✓ 编译成功${NC}"
    else
        echo -e "${YELLOW}⚠ 编译失败，请手动检查代码${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Maven 未安装，跳过编译检查${NC}"
fi

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✅ 模块 ${MODULE_NAME} 添加成功！${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}📂 生成的文件:${NC}"
[ -d "$BACKEND_DEST" ] && echo -e "  ${GREEN}✓${NC} src/main/java/com/yuheng/demo/$MODULE_NAME/"
[ -d "$SQL_DEST" ] && echo -e "  ${GREEN}✓${NC} src/main/resources/db/changelog/$MODULE_NAME/"
[ -d "$UI_DEST" ] && echo -e "  ${GREEN}✓${NC} yuheng-demo-ui/src/views/$MODULE_NAME/"
[ -d "$API_DEST" ] && echo -e "  ${GREEN}✓${NC} yuheng-demo-ui/src/api/demo/"
echo ""
echo -e "${BLUE}🚀 下一步:${NC}"
echo -e "  1. ${YELLOW}查看并完善业务逻辑${NC}: src/main/java/com/yuheng/demo/$MODULE_NAME/"
echo -e "  2. ${YELLOW}查看并调整数据库脚本${NC}: src/main/resources/db/changelog/$MODULE_NAME/"
echo -e "  3. ${YELLOW}查看并完善前端页面${NC}: yuheng-demo-ui/src/views/$MODULE_NAME/"
echo -e "  4. ${YELLOW}运行应用${NC}: mvn spring-boot:run"
echo ""
echo -e "${BLUE}💡 提示:${NC}"
echo -e "  - 你可以使用 AI 来进一步完善这个模块"
echo -e "  - 参考 docs/ 目录下的开发文档"
echo -e "  - API 文档: ${YELLOW}http://localhost:48080/doc.html${NC}"
echo ""
