# Tasks

## 阶段1：立即实施 - 核心性能优化（性能提升100倍+）

- [x] Task 1: 创建KeywordMatcher类
  - [x] SubTask 1.1: 创建src/keyword_matcher.py模块
  - [x] SubTask 1.2: 实现KeywordMatcher类，使用pyahocorasick构建自动机
  - [x] SubTask 1.3: 实现match方法，返回匹配结果（关键词、回复、位置）
  - [x] SubTask 1.4: 实现缓存机制，支持多账号独立缓存
  - [x] SubTask 1.5: 实现热更新方法，关键词变更时自动重建自动机
  - [x] SubTask 1.6: 添加性能监控日志
  - [x] SubTask 1.7: 添加线程锁保证并发安全
  - [x] SubTask 1.8: 实现图片关键词回复支持
  - [x] SubTask 1.9: 实现变量替换功能（{用户名}、{商品名}等）

- [x] Task 2: 集成KeywordMatcher到消息处理流程
  - [x] SubTask 2.1: 修改xianyu_message_handler.py，导入KeywordMatcher
  - [x] SubTask 2.2: 替换原有的线性遍历匹配逻辑
  - [x] SubTask 2.3: 保持向后兼容，支持旧数据格式
  - [x] SubTask 2.4: 添加匹配结果日志记录
  - [x] SubTask 2.5: 实现空消息和超长消息预处理
  - [x] SubTask 2.6: 实现功能开关配置，支持回滚到旧匹配逻辑

- [x] Task 3: 更新关键词仓储层
  - [x] SubTask 3.1: 在keyword_repo.py中添加缓存刷新触发逻辑
  - [x] SubTask 3.2: 添加关键词变更通知机制

- [x] Task 4: 添加依赖和配置
  - [x] SubTask 4.1: 更新requirements.txt添加pyahocorasick
  - [x] SubTask 4.2: 在config.py添加功能开关配置项
  - [x] SubTask 4.3: 测试依赖安装

- [x] Task 1.5: 阶段1代码审查
  - [x] SubTask 1.5.1: 检查功能缺陷
  - [x] SubTask 1.5.2: 检查代码质量问题
  - [x] SubTask 1.5.3: 检查并发安全
  - [x] SubTask 1.5.4: 修复发现的问题

## 阶段2：短期实施 - 功能增强

- [x] Task 5: 扩展数据库表结构
  - [x] SubTask 5.1: 在base.py中为keywords表添加match_type字段（默认'contains'）
  - [x] SubTask 5.2: 添加priority字段（默认0，范围0-100）
  - [x] SubTask 5.3: 添加reply_mode字段（默认'single'）
  - [x] SubTask 5.4: 添加replies字段（TEXT，存储JSON数组）
  - [x] SubTask 5.5: 添加trigger_count字段（默认0）
  - [x] SubTask 5.6: 添加数据库迁移逻辑，为现有关键词设置默认值
  - [x] SubTask 5.7: 验证数据迁移无数据丢失

- [x] Task 6: 实现多种匹配类型
  - [x] SubTask 6.1: 在KeywordMatcher中实现exact匹配（精确匹配）
  - [x] SubTask 6.2: 实现prefix匹配（前缀匹配）
  - [x] SubTask 6.3: 实现suffix匹配（后缀匹配）
  - [x] SubTask 6.4: 实现regex匹配（正则表达式），添加安全限制
  - [x] SubTask 6.5: 实现fuzzy匹配（模糊匹配，使用rapidfuzz库）
  - [x] SubTask 6.6: 添加rapidfuzz依赖到requirements.txt
  - [x] SubTask 6.7: 实现匹配类型二次验证逻辑

- [x] Task 7: 实现优先级机制
  - [x] SubTask 7.1: 在匹配结果中按priority降序排序
  - [x] SubTask 7.2: 商品ID关键词优先于通用关键词
  - [x] SubTask 7.3: 同优先级时按匹配位置排序

- [x] Task 8: 实现多回复模式
  - [x] SubTask 8.1: 实现single模式（返回单条回复）
  - [x] SubTask 8.2: 实现random模式（随机选择一条回复）
  - [x] SubTask 8.3: 实现sequence模式（顺序循环回复），需要持久化计数
  - [x] SubTask 8.4: 更新keyword_repo.py支持replies字段存储

- [x] Task 9: 实现触发统计
  - [x] SubTask 9.1: 关键词触发时自动更新trigger_count
  - [x] SubTask 9.2: 添加触发次数查询API

- [x] Task 10: 更新API路由
  - [x] SubTask 10.1: 修改keywords.py路由支持新字段
  - [x] SubTask 10.2: 更新导入导出功能支持新字段
  - [x] SubTask 10.3: 添加关键词缓存刷新API

- [x] Task 11: 前端UI优化
  - [x] SubTask 11.1: 在index.html添加匹配类型选择器
  - [x] SubTask 11.2: 添加优先级输入框
  - [x] SubTask 11.3: 添加回复模式选择器
  - [x] SubTask 11.4: 添加多回复配置文本框
  - [x] SubTask 11.5: 更新keywords.js支持新字段提交
  - [x] SubTask 11.6: 优化关键词列表显示，展示匹配类型、优先级、触发次数

- [x] Task 11.5: 阶段2代码审查
  - [x] SubTask 11.5.1: 检查功能缺陷
  - [x] SubTask 11.5.2: 检查数据迁移正确性
  - [x] SubTask 11.5.3: 检查前后端数据流
  - [x] SubTask 11.5.4: 修复发现的问题

## 阶段3：中期实施 - 规则引擎

- [x] Task 12: 引入规则引擎框架
  - [x] SubTask 12.1: 评估并选择规则引擎（business-rules或自研）
  - [x] SubTask 12.2: 创建src/rule_engine.py模块
  - [x] SubTask 12.3: 定义规则数据结构

- [x] Task 13: 实现条件组合逻辑
  - [x] SubTask 13.1: 实现AND逻辑（所有条件满足）
  - [x] SubTask 13.2: 实现OR逻辑（任一条件满足）
  - [x] SubTask 13.3: 实现NOT逻辑（条件不满足）
  - [x] SubTask 13.4: 实现嵌套条件组合

- [x] Task 14: 实现条件类型
  - [x] SubTask 14.1: 实现时间条件（生效时间段）
  - [x] SubTask 14.2: 实现用户条件（新用户/老用户）
  - [x] SubTask 14.3: 实现商品条件（价格范围/分类）
  - [x] SubTask 14.4: 实现排除关键词条件

- [x] Task 15: 数据库扩展
  - [x] SubTask 15.1: 在keywords表添加conditions字段（TEXT，存储JSON）
  - [x] SubTask 15.2: 更新keyword_repo.py支持conditions字段
  - [x] SubTask 15.3: 数据迁移，为现有关键词设置空conditions

- [x] Task 16: 前端规则配置界面
  - [x] SubTask 16.1: 创建高级条件设置面板（折叠显示）
  - [x] SubTask 16.2: 添加时间范围选择器
  - [x] SubTask 16.3: 添加排除关键词输入
  - [x] SubTask 16.4: 添加触发次数限制设置

- [x] Task 16.5: 阶段3代码审查
  - [x] SubTask 16.5.1: 检查规则引擎逻辑正确性
  - [x] SubTask 16.5.2: 检查条件组合边界情况
  - [x] SubTask 16.5.3: 修复发现的问题

## 功能测试

- [x] Task 17: 单元测试
  - [x] SubTask 17.1: KeywordMatcher类单元测试
  - [x] SubTask 17.2: 匹配类型测试（6种类型）
  - [x] SubTask 17.3: 优先级机制测试
  - [x] SubTask 17.4: 多回复模式测试
  - [x] SubTask 17.5: 规则引擎单元测试
  - [x] SubTask 17.6: 边界条件测试（空消息、超长消息、特殊字符、Unicode）
  - [x] SubTask 17.7: 并发安全测试

- [x] Task 18: 集成测试
  - [x] SubTask 18.1: 消息处理流程集成测试
  - [x] SubTask 18.2: API接口测试
  - [x] SubTask 18.3: 前端交互测试
  - [x] SubTask 18.4: 多账号隔离测试

- [x] Task 19: 性能测试
  - [x] SubTask 19.1: 100关键词匹配性能测试（目标<0.1ms）
  - [x] SubTask 19.2: 1000关键词匹配性能测试（目标<1ms）
  - [x] SubTask 19.3: 10000关键词匹配性能测试（目标<10ms）
  - [x] SubTask 19.4: 内存占用测试（目标<50MB）
  - [x] SubTask 19.5: 缓存重建性能测试（目标<100ms）

- [x] Task 20: 端到端测试
  - [x] SubTask 20.1: 完整业务流程测试
  - [x] SubTask 20.2: 回归测试（现有功能无影响）
  - [x] SubTask 20.3: 回滚功能测试

# Task Dependencies

- [Task 2] depends on [Task 1] (需要KeywordMatcher类)
- [Task 3] depends on [Task 1] (需要KeywordMatcher类)
- [Task 1.5] depends on [Task 1, Task 2, Task 3, Task 4] (阶段1完成后审查)
- [Task 6] depends on [Task 5] (需要数据库字段)
- [Task 7] depends on [Task 5] (需要数据库字段)
- [Task 8] depends on [Task 5] (需要数据库字段)
- [Task 9] depends on [Task 5] (需要数据库字段)
- [Task 10] depends on [Task 5, Task 6, Task 7, Task 8, Task 9] (需要后端功能)
- [Task 11] depends on [Task 10] (需要API支持)
- [Task 11.5] depends on [Task 5-11] (阶段2完成后审查)
- [Task 13] depends on [Task 12] (需要规则引擎框架)
- [Task 14] depends on [Task 13] (需要条件组合逻辑)
- [Task 15] depends on [Task 5] (需要数据库迁移)
- [Task 16] depends on [Task 14, Task 15] (需要条件和数据库)
- [Task 16.5] depends on [Task 12-16] (阶段3完成后审查)
- [Task 17] depends on [Task 1.5] (阶段1审查后可开始)
- [Task 18] depends on [Task 11.5] (阶段2审查后可开始)
- [Task 19] depends on [Task 1.5] (阶段1审查后可开始)
- [Task 20] depends on [Task 16.5, Task 17, Task 18, Task 19] (所有测试完成后)

# Parallelizable Tasks

以下任务可以并行执行：
- Task 1, Task 4 (KeywordMatcher和依赖安装)
- Task 5, Task 6, Task 7, Task 8, Task 9 (阶段2后端任务可并行)
- Task 12, Task 13 (规则引擎框架和逻辑)
- Task 17, Task 19 (单元测试和性能测试可并行)
