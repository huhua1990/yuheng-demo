#!/bin/bash
# Yuheng Demo - 同步模板更新脚本
# 用法: ./scripts/sync-template.sh

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

TEMPLATE_DIR="../yuheng-business-templates"

echo -e "${BLUE}🔄 同步业务模板库${NC}"
echo ""

if [ ! -d "$TEMPLATE_DIR" ]; then
    echo -e "${YELLOW}📦 模板库不存在，正在克隆...${NC}"
    git clone https://github.com/huhua1990/yuheng-business-templates.git "$TEMPLATE_DIR"
    echo -e "${GREEN}✓ 模板库克隆完成${NC}"
else
    echo -e "${YELLOW}📦 更新模板库...${NC}"
    cd "$TEMPLATE_DIR"

    # 检查是否有本地修改
    if [ -n "$(git status --porcelain)" ]; then
        echo -e "${YELLOW}⚠ 模板库有本地修改，请先处理${NC}"
        git status --short
        exit 1
    fi

    # 拉取最新代码
    BRANCH=$(git rev-parse --abbrev-ref HEAD)
    git pull origin "$BRANCH"

    cd - > /dev/null
    echo -e "${GREEN}✓ 模板库更新完成${NC}"
fi

echo ""
echo -e "${BLUE}📚 可用的模板:${NC}"
ls -1 "$TEMPLATE_DIR" | grep "^template-" | while read template; do
    echo -e "  ${GREEN}✓${NC} $template"
done

echo ""
echo -e "${GREEN}✅ 同步完成！${NC}"
