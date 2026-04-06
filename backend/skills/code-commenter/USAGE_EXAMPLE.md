# Code Commenter Skill 使用示例

## 技能概述
Code Commenter skill 专门用于为代码添加清晰、有用的注释，提高代码的可读性和可维护性。

## 使用场景

### 1. 为新代码添加注释
当用户提供一段没有注释的代码时，你可以：
- 添加文件级注释说明模块用途
- 为函数添加详细的docstring
- 在复杂逻辑处添加行内注释
- 标记TODO/FIXME项

### 2. 改进现有注释
当现有注释质量不高时，你可以：
- 将冗余注释替换为有意义的解释
- 更新过时的注释
- 补充缺失的重要注释
- 统一注释风格

### 3. 解释复杂代码
当代码逻辑复杂难懂时，你可以：
- 分解复杂算法为步骤说明
- 解释业务规则和约束
- 说明设计决策和权衡
- 标注性能考虑和限制

## 使用示例

### 示例1：Python代码注释
**用户请求**："请为这段Python代码添加注释"

```python
def calculate_bonus(salary, years, performance):
    if years < 1:
        return 0
    base = salary * 0.1
    if years >= 5:
        base *= 1.5
    if performance == 'excellent':
        base *= 2
    elif performance == 'good':
        base *= 1.5
    return min(base, salary * 2)
```

**应用skill后的响应**：
```markdown
## 代码注释添加完成

### 文件：bonus_calculator.py

**添加的注释：**

```python
def calculate_bonus(salary, years, performance):
    """
    计算员工年终奖金
    
    奖金计算规则：
    1. 工作不满1年无奖金
    2. 基础奖金为年薪的10%
    3. 工龄5年以上，基础奖金增加50%
    4. 根据绩效评级调整奖金：
       - 优秀：奖金翻倍
       - 良好：奖金增加50%
    5. 奖金上限为年薪的2倍
    
    Args:
        salary: 年薪（正数）
        years: 工作年限（整数）
        performance: 绩效评级 ('excellent', 'good', 或其他）
    
    Returns:
        计算出的奖金金额
    """
    # 工作不满1年无资格获得奖金
    if years < 1:
        return 0
    
    # 基础奖金：年薪的10%
    base = salary * 0.1
    
    # 工龄补贴：5年以上工龄增加50%基础奖金
    if years >= 5:
        base *= 1.5  # 增加50%
    
    # 绩效奖金调整
    if performance == 'excellent':
        base *= 2  # 优秀绩效：奖金翻倍
    elif performance == 'good':
        base *= 1.5  # 良好绩效：奖金增加50%
    
    # 奖金上限：不超过年薪的2倍
    return min(base, salary * 2)
```

### 关键注释说明：
1. **函数docstring**：详细说明了奖金计算规则和业务逻辑
2. **参数说明**：明确了每个参数的含义和期望值
3. **行内注释**：解释了关键计算步骤的目的
4. **数值说明**：解释了1.5、2等乘数的含义
```

### 示例2：JavaScript代码注释
**用户请求**："请解释这段JavaScript代码"

```javascript
function filterAndSort(products, category, minPrice, maxPrice) {
    return products
        .filter(p => p.category === category && p.price >= minPrice && p.price <= maxPrice)
        .sort((a, b) => b.rating - a.rating || a.price - b.price);
}
```

**应用skill后的响应**：
```markdown
## 代码注释添加完成

### 文件：productUtils.js

**添加的注释：**

```javascript
/**
 * 根据条件筛选产品并按规则排序
 * 
 * 筛选条件：
 * 1. 产品类别匹配指定类别
 * 2. 价格在指定范围内（包含边界值）
 * 
 * 排序规则（优先级顺序）：
 * 1. 评分降序（评分高的在前）
 * 2. 价格升序（评分相同时，价格低的在前）
 * 
 * @param {Array} products - 产品数组
 * @param {string} category - 目标产品类别
 * @param {number} minPrice - 最低价格（包含）
 * @param {number} maxPrice - 最高价格（包含）
 * @returns {Array} 筛选并排序后的产品数组
 */
function filterAndSort(products, category, minPrice, maxPrice) {
    return products
        // 筛选：类别匹配且价格在范围内
        .filter(p => p.category === category && p.price >= minPrice && p.price <= maxPrice)
        // 排序：先按评分降序，评分相同则按价格升序
        .sort((a, b) => b.rating - a.rating || a.price - b.price);
}
```

### 关键注释说明：
1. **JSDoc注释**：提供了完整的函数文档
2. **筛选逻辑说明**：解释了filter条件的具体含义
3. **排序规则说明**：明确了排序的优先级顺序
4. **参数类型说明**：帮助理解函数接口
```

## 最佳实践提示

1. **优先解释WHY**：代码展示WHAT，注释解释WHY
2. **保持简洁**：注释应该简洁明了，避免冗长
3. **及时更新**：代码修改时同步更新相关注释
4. **避免重复**：不要重复代码已经明确表达的内容
5. **使用标准格式**：遵循语言的注释规范（如Python的docstring，JS的JSDoc）

## 常见问题

**Q: 应该为所有代码都添加注释吗？**
A: 不是。应该为：
- 公共API和接口
- 复杂算法和业务逻辑
- 非显而易见的实现
- 重要的设计决策
- 已知的限制和问题

**Q: 如何判断注释是否足够？**
A: 想象一个新手开发者6个月后阅读这段代码，能否理解：
- 这段代码的目的是什么？
- 为什么这样实现？
- 有哪些需要注意的地方？
- 如何正确使用它？

**Q: 注释应该用中文还是英文？**
A: 根据团队约定。通常：
- 开源项目：英文
- 国内团队：中文
- 混合团队：主要语言+关键术语保持英文