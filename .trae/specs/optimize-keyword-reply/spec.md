# 关键词回复功能全面优化 Spec

## Why

当前关键词回复功能存在性能瓶颈（线性遍历匹配O(n×m)）、功能单一（仅支持简单包含匹配）、缺乏优先级机制和统计分析能力。按照推荐方案分三个阶段实施：立即实现KeywordMatcher类提升性能100倍+，短期添加多种匹配类型和优先级支持，中期引入规则引擎支持复杂条件。

## What Changes

### 阶段1：立即实施 - 核心性能优化
- 引入Aho-Corasick算法实现高效多关键词匹配（O(n)复杂度，性能提升100倍+）
- 创建KeywordMatcher类，封装匹配逻辑
- 添加关键词缓存机制，支持热更新
- **仅实现contains（包含）匹配类型**，保持与现有功能一致
- 保留图片关键词回复和变量替换功能

### 阶段2：短期实施 - 功能增强
- 扩展数据库表结构，支持匹配类型、优先级、多回复
- 实现多种匹配类型：精确、前缀、后缀、正则、模糊匹配
- 添加优先级机制，高优先级关键词优先匹配
- 支持多回复模式（单条/随机/顺序）
- 更新前端UI支持新功能

### 阶段3：中期实施 - 规则引擎
- 引入轻量级规则引擎框架
- 支持复杂条件组合（AND/OR/NOT逻辑）
- 支持时间条件、用户条件、商品条件
- 实现规则可视化配置界面

### **BREAKING** 数据库变更
- keywords表新增字段：match_type, priority, conditions, trigger_count, replies, reply_mode

## Impact

- Affected specs: 关键词回复核心功能
- Affected code:
  - `src/keyword_matcher.py` (新增) - 阶段1
  - `src/rule_engine.py` (新增) - 阶段3
  - `utils/xianyu/xianyu_message_handler.py` (修改)
  - `db_manager/keyword_repo.py` (修改)
  - `db_manager/base.py` (修改)
  - `reply_server/routes/keywords.py` (修改)
  - `static/js/modules/keywords.js` (修改)
  - `static/index.html` (修改)
  - `static/css/app.css` (修改)

## ADDED Requirements

### Requirement: 高效关键词匹配引擎（阶段1 - 立即实施）

系统应提供基于Aho-Corasick算法的高效关键词匹配引擎，性能提升100倍以上。

#### Scenario: 多关键词同时匹配
- **WHEN** 用户消息包含多个关键词
- **THEN** 系统应在O(n)时间内识别所有匹配的关键词，性能提升100倍+

#### Scenario: 缓存热更新
- **WHEN** 关键词配置发生变更
- **THEN** 系统应自动更新匹配器缓存，无需重启服务

#### Scenario: KeywordMatcher类封装
- **WHEN** 调用KeywordMatcher.match()方法
- **THEN** 返回匹配结果包含关键词、回复内容、匹配位置

#### Scenario: 无匹配关键词
- **WHEN** 用户消息不包含任何关键词
- **THEN** 系统应返回None，继续后续处理流程（AI回复或默认回复）

#### Scenario: 空关键词配置
- **WHEN** 账号没有配置任何关键词
- **THEN** 系统应跳过关键词匹配，继续后续处理流程

#### Scenario: 图片关键词回复
- **WHEN** 匹配到图片类型的关键词
- **THEN** 系统应返回图片URL和回复文本

#### Scenario: 变量替换
- **WHEN** 回复内容包含变量（如{用户名}、{商品名}）
- **THEN** 系统应替换为实际值后返回

#### Scenario: 与AI回复的优先级关系
- **WHEN** 关键词匹配成功
- **THEN** 系统应直接返回关键词回复，不再调用AI回复

### Requirement: 多种匹配类型支持（阶段2 - 短期实施）

系统应支持多种关键词匹配类型，满足不同业务场景需求。

#### Scenario: 包含匹配（默认）
- **WHEN** 匹配类型为"contains"且消息包含关键词
- **THEN** 触发关键词回复

#### Scenario: 精确匹配
- **WHEN** 匹配类型为"exact"且消息完全等于关键词
- **THEN** 触发关键词回复

#### Scenario: 前缀匹配
- **WHEN** 匹配类型为"prefix"且消息以关键词开头
- **THEN** 触发关键词回复

#### Scenario: 后缀匹配
- **WHEN** 匹配类型为"suffix"且消息以关键词结尾
- **THEN** 触发关键词回复

#### Scenario: 正则匹配
- **WHEN** 匹配类型为"regex"且消息匹配正则表达式
- **THEN** 触发关键词回复

#### Scenario: 模糊匹配
- **WHEN** 匹配类型为"fuzzy"且消息与关键词相似度超过阈值（默认80%）
- **THEN** 触发关键词回复

### Requirement: 优先级机制（阶段2 - 短期实施）

系统应支持关键词优先级设置，高优先级关键词优先匹配。

#### Scenario: 优先级排序
- **WHEN** 多个关键词同时匹配
- **THEN** 系统应返回优先级最高的关键词回复

#### Scenario: 优先级范围
- **WHEN** 设置关键词优先级
- **THEN** 优先级值应在0-100范围内，默认为0

#### Scenario: 商品ID关键词优先
- **WHEN** 同时匹配到商品ID关键词和通用关键词
- **THEN** 系统应优先返回商品ID关键词的回复

### Requirement: 多回复模式（阶段2 - 短期实施）

系统应支持多种回复模式，增加回复的多样性和自然度。

#### Scenario: 单条回复
- **WHEN** 回复模式为"single"
- **THEN** 系统应返回固定的单条回复

#### Scenario: 随机回复
- **WHEN** 回复模式为"random"
- **THEN** 系统应从预设回复列表中随机选择一条回复

#### Scenario: 顺序回复
- **WHEN** 回复模式为"sequence"
- **THEN** 系统应按顺序循环使用预设回复列表

### Requirement: 规则引擎（阶段3 - 中期实施）

系统应引入轻量级规则引擎，支持复杂条件组合。

#### Scenario: 条件组合
- **WHEN** 规则包含多个条件
- **THEN** 系统应支持AND/OR/NOT逻辑组合

#### Scenario: 时间条件
- **WHEN** 规则包含时间条件
- **THEN** 系统应在指定时间范围内触发

#### Scenario: 用户条件
- **WHEN** 规则包含用户条件
- **THEN** 系统应根据用户属性（新用户/老用户/购买次数）触发

#### Scenario: 商品条件
- **WHEN** 规则包含商品条件
- **THEN** 系统应根据商品属性（价格范围/分类）触发

### Requirement: 触发统计

系统应记录关键词触发次数，支持数据分析。

#### Scenario: 触发计数
- **WHEN** 关键词被触发
- **THEN** 系统应自动增加该关键词的触发次数

### Requirement: 边界条件处理

系统应正确处理各种边界条件。

#### Scenario: 空消息处理
- **WHEN** 收到空消息或仅包含空白字符的消息
- **THEN** 系统应跳过关键词匹配

#### Scenario: 超长消息处理
- **WHEN** 消息长度超过10000字符
- **THEN** 系统应截断后进行匹配，避免性能问题

#### Scenario: 特殊字符处理
- **WHEN** 消息包含特殊字符（如正则元字符）
- **THEN** 系统应正确转义处理，避免匹配错误

#### Scenario: Unicode字符处理
- **WHEN** 消息包含emoji或多语言字符
- **THEN** 系统应正确处理Unicode编码

### Requirement: 并发安全

系统应支持并发访问。

#### Scenario: 多账号并发访问
- **WHEN** 多个账号同时收到消息
- **THEN** 系统应正确隔离各账号的关键词配置，避免数据混乱

#### Scenario: 缓存并发更新
- **WHEN** 同时更新多个账号的关键词缓存
- **THEN** 系统应使用线程锁保证数据一致性

### Requirement: 回滚机制

系统应支持功能回滚。

#### Scenario: 功能开关
- **WHEN** 新匹配器出现问题
- **THEN** 系统应支持通过配置切换回旧的匹配逻辑

## MODIFIED Requirements

### Requirement: 关键词匹配流程

原有流程：线性遍历所有关键词，使用`keyword in message`判断，O(n×m)复杂度

修改后流程：
1. 检查消息是否为空或超长，进行预处理
2. 使用Aho-Corasick自动机快速识别所有匹配关键词，O(n)复杂度
3. 根据匹配类型进行二次验证（阶段2）
4. 按优先级排序（高优先级优先，商品ID关键词优先）
5. 应用规则引擎条件过滤（阶段3）
6. 处理变量替换
7. 更新触发次数
8. 返回最终匹配结果

### Requirement: 关键词数据结构

原有结构：
```python
{
    'keyword': str,
    'reply': str,
    'item_id': str,
    'type': str,        # text/image
    'image_url': str
}
```

修改后结构：
```python
{
    'keyword': str,
    'reply': str,
    'item_id': str,
    'type': str,            # text/image
    'image_url': str,
    'match_type': str,      # contains/exact/prefix/suffix/regex/fuzzy (阶段2，默认contains)
    'priority': int,        # 0-100 (阶段2，默认0)
    'reply_mode': str,      # single/random/sequence (阶段2，默认single)
    'replies': List[str],   # 多回复列表 (阶段2)
    'conditions': dict,     # 规则引擎条件 (阶段3)
    'trigger_count': int    # 触发次数 (默认0)
}
```

## REMOVED Requirements

无移除的需求，保持向后兼容。

## Implementation Phases

### 阶段1：立即实施 - 核心性能优化
**目标：性能提升100倍+，保持功能不变**

1. 创建`src/keyword_matcher.py`，实现KeywordMatcher类
2. 使用pyahocorasick库构建自动机
3. 实现缓存机制和热更新
4. 集成到消息处理流程，替换原有线性遍历
5. 保留图片关键词回复和变量替换功能
6. 添加性能监控日志
7. 添加功能开关支持回滚

### 阶段2：短期实施 - 功能增强
**目标：丰富匹配能力**

1. 扩展数据库表结构
2. 数据迁移：为现有关键词添加默认值
3. 实现多种匹配类型
4. 添加优先级机制
5. 实现多回复模式
6. 更新前端UI

### 阶段3：中期实施 - 规则引擎
**目标：支持复杂条件**

1. 引入轻量级规则引擎（business-rules或自研）
2. 实现条件组合逻辑
3. 支持时间/用户/商品条件
4. 创建规则配置界面
5. 完善测试和文档

## Performance Requirements

| 指标 | 目标值 |
|------|--------|
| 100关键词匹配时间 | <0.1ms |
| 1000关键词匹配时间 | <1ms |
| 10000关键词匹配时间 | <10ms |
| 内存占用（10000关键词） | <50MB |
| 缓存重建时间（1000关键词） | <100ms |
