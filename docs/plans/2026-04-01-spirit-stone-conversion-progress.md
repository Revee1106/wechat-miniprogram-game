# 灵石流转与资源转化进度说明

**日期：** 2026-04-01

本次主要补齐灵石相关的后端能力，覆盖基础资源出售、灵石转修为，以及对应的 API 与测试。

## 本次已完成

### 1. 资源出售规则

- `sell_resource` 继续作为统一出售入口
- `herb` 固定售价调整为 `1 药草 = 2 灵石`
- 保留基础资源出售白名单与数量校验

### 2. 灵石转化修为

- 新增 `resource_conversion_service.py`
- 新增灵石转修为能力：`1 灵石 = 5 修为`
- 资源不足、非法数量等情况会抛出明确错误

### 3. API 接口补充

- 新增 `POST /api/run/resource/convert-cultivation`
- 新增 `ResourceConversionRequest`
- `RunService` 已接入新的转化动作

### 4. 测试覆盖

- 补充资源出售价格断言
- 补充灵石转修为服务测试
- 补充灵石转修为 API round-trip 测试

## 当前范围外

- 未加入动态价格或游商系统
- 未把更多资源类型接入修为转化
- 未提供后端持久化的洞府月结历史

## 本次验证

已执行：

```bash
python -m pytest tests/backend -q
```

结果：

- 后端：`123 passed`
