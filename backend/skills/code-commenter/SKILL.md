---
name: code-commenter
description: Add clear, helpful comments to code to improve readability and maintainability. Use when user asks to add comments, explain code, or make code more understandable.
---

# Code Commenter Skill

You now have expertise in adding meaningful comments to code. Follow this structured approach to make code more readable and maintainable.

## Commenting Principles

### 1. Purpose of Comments
- **Explain WHY, not WHAT**: Code shows what it does, comments explain why it does it
- **Document assumptions**: What assumptions are being made about inputs, state, or environment
- **Clarify complex logic**: Break down intricate algorithms or business rules
- **Note limitations**: Document known issues, edge cases, or performance considerations
- **Provide context**: Explain the broader purpose or how this fits into the system

### 2. Types of Comments

#### File-level Comments
```python
"""
Module: data_processor.py
Purpose: Process and transform raw data into analysis-ready format
Author: Data Team
Created: 2024-01-15
Last Modified: 2024-03-20
Dependencies: pandas, numpy, scikit-learn
"""

# or for smaller files:
# Data validation utilities for customer records
```

#### Function/Method Comments
```python
def calculate_discount(price: float, customer_tier: str) -> float:
    """
    Calculate discount based on customer tier and price.
    
    Args:
        price: Original price before discount (must be positive)
        customer_tier: Customer loyalty tier - 'bronze', 'silver', 'gold', or 'platinum'
    
    Returns:
        Discounted price after applying tier-based discount
    
    Raises:
        ValueError: If price is negative or customer_tier is invalid
    
    Example:
        >>> calculate_discount(100.0, 'gold')
        85.0  # 15% discount for gold tier
    """
```

#### Inline Comments
```python
# Use for complex logic that needs explanation
result = (a * b) / (c - d)  # Calculate weighted average, avoid division by zero

# NOT for obvious code
x = x + 1  # Increment x by 1  ❌ Too obvious!
```

#### TODO/FIXME Comments
```python
# TODO: Implement caching for performance improvement
# FIXME: This workaround should be removed after API v2 is available
# HACK: Temporary solution for compatibility with legacy system
```

### 3. Language-Specific Guidelines

#### Python
```python
# Use docstrings for modules, classes, functions
def process_data(data: List[Dict]) -> pd.DataFrame:
    """
    Convert raw JSON data to pandas DataFrame with proper typing.
    
    Handles missing values and type conversion automatically.
    """
    
# Type hints reduce need for comments
def calculate_total(items: List[Item]) -> float:
    """Sum prices of all items with tax."""
    return sum(item.price * (1 + item.tax_rate) for item in items)
```

#### JavaScript/TypeScript
```javascript
/**
 * Fetches user data from API with retry logic
 * @param userId - Unique identifier for the user
 * @param maxRetries - Maximum number of retry attempts (default: 3)
 * @returns Promise resolving to user data object
 * @throws {NetworkError} If all retry attempts fail
 */
async function fetchUserData(userId: string, maxRetries = 3): Promise<User> {
  // Implementation with retry logic
}
```

#### Java
```java
/**
 * Service class for managing user authentication.
 * <p>
 * This class handles login, logout, and session management
 * using JWT tokens for stateless authentication.
 * </p>
 * 
 * @author Development Team
 * @version 1.2
 */
public class AuthService {
    /**
     * Authenticates user credentials and returns JWT token.
     * 
     * @param username the user's login name
     * @param password the user's password (plaintext, will be hashed)
     * @return JWT token if authentication succeeds
     * @throws AuthenticationException if credentials are invalid
     */
    public String authenticate(String username, String password) {
        // Implementation
    }
}
```

## Commenting Workflow

### 1. Analyze the Code
- Read the code to understand its purpose
- Identify complex or non-obvious logic
- Look for business rules or domain knowledge
- Check for edge cases or special handling

### 2. Determine What Needs Comments
- **Always comment**: Public APIs, complex algorithms, business logic
- **Sometimes comment**: Non-obvious implementations, workarounds
- **Rarely comment**: Simple getters/setters, obvious operations

### 3. Write Effective Comments
```python
# BAD: Redundant comment
x = x + 1  # Add 1 to x

# GOOD: Explains purpose
retry_count += 1  # Increment retry counter for exponential backoff

# BAD: Outdated comment
# This function sorts the list (actually now filters)
def process_data(data):
    return [x for x in data if x > 0]

# GOOD: Accurate and helpful
def filter_positive_numbers(data):
    """Return only positive numbers from the input list."""
    return [x for x in data if x > 0]
```

### 4. Review and Refine
- Ensure comments are up-to-date with code
- Remove obsolete comments
- Improve clarity and conciseness
- Check for consistency with project style

## Common Patterns

### Explaining Complex Algorithms
```python
def find_shortest_path(graph, start, end):
    """
    Find shortest path using Dijkstra's algorithm.
    
    Implementation details:
    1. Initialize distances with infinity for all nodes except start (0)
    2. Use priority queue to always expand the closest unvisited node
    3. Update distances when a shorter path is found
    4. Track previous nodes to reconstruct the path
    
    Time complexity: O((V + E) log V) where V=vertices, E=edges
    Space complexity: O(V) for distance and previous arrays
    """
```

### Documenting Business Rules
```python
def calculate_shipping_cost(weight, destination, customer_type):
    """
    Calculate shipping cost based on business rules:
    
    Rules:
    1. Base rate: $5 for first 0.5kg, $2 per additional 0.5kg
    2. International destinations: 50% surcharge
    3. Premium customers: 20% discount
    4. Free shipping for orders over $100 (handled separately)
    
    Note: These rates are updated quarterly - check rate_sheet.md
    """
```

### Warning About Side Effects
```python
def update_user_profile(user_id, data):
    """
    Update user profile and invalidate cache.
    
    WARNING: This function has side effects:
    1. Updates database record
    2. Invalidates Redis cache for this user
    3. Sends notification email if email changed
    
    Use transaction to ensure atomicity.
    """
```

## Tools and Commands

### Python Documentation Tools
```bash
# Generate documentation with pdoc
pdoc mymodule --html

# Check docstring coverage with interrogate
interrogate myproject/

# Lint docstrings with pydocstyle
pydocstyle mymodule.py
```

### JavaScript/TypeScript Tools
```bash
# Generate documentation with TypeDoc
typedoc --out docs src/

# Check JSDoc coverage
jsdoc -c jsdoc.json
```

### General Code Analysis
```bash
# Find TODO/FIXME comments
grep -rn "TODO\|FIXME\|HACK\|XXX" .

# Count comment lines vs code lines
cloc .

# Check comment quality (custom scripts)
python check_comments.py src/
```

## Output Format

When adding comments to code, provide:

```markdown
## Code with Added Comments

### File: [filename]

**Before:**
```[language]
[original code without comments]
```

**After:**
```[language]
[code with added comments]
```

### Summary of Changes:
1. **File-level comment**: Added module description and purpose
2. **Function comments**: Added docstrings explaining parameters, returns, and behavior
3. **Inline comments**: Added explanations for complex logic
4. **TODO comments**: Marked areas for future improvement

### Key Comments Added:
- [Brief description of important comment 1]
- [Brief description of important comment 2]
- [Brief description of important comment 3]

### Notes:
- Comments focus on explaining WHY, not WHAT
- Complex algorithms are broken down step-by-step
- Business rules are documented clearly
- Edge cases and limitations are noted
```

## Best Practices Checklist

- [ ] **Comments explain WHY, not WHAT**
- [ ] **Complex logic has step-by-step explanations**
- [ ] **Business rules are documented**
- [ ] **Function parameters and returns are described**
- [ ] **Edge cases and limitations are noted**
- [ ] **TODO/FIXME comments have clear next steps**
- [ ] **Comments are up-to-date with code**
- [ ] **No redundant or obvious comments**
- [ ] **Consistent style throughout codebase**
- [ ] **Public APIs have complete documentation**

Remember: Good comments make code maintainable. Bad comments can be worse than no comments at all. Always aim for comments that would help someone new understand the code in 6 months.