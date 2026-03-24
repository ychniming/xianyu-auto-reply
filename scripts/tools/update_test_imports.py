#!/usr/bin/env python3
"""
更新测试文件中的导入路径
将旧的导入路径更新为新的模块结构
"""

import os
import re
from pathlib import Path

# 定义导入映射
IMPORT_MAPPINGS = [
    (r'from db_manager import', r'from app.repositories import '),
    (r'from db_manager\.', r'from app.repositories.'),
    (r'from reply_server import', r'from app.api import '),
    (r'from reply_server\.routes import', r'from app.api.routes import '),
    (r'from src\.', r'from app.core.'),
]

def update_file_imports(file_path: Path) -> bool:
    """更新单个文件的导入"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # 应用所有映射
        for old_import, new_import in IMPORT_MAPPINGS:
            content = content.replace(old_import, new_import)
        
        # 如果内容有变化，则写回文件
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"已更新: {file_path}")
            return True
        return False
    except Exception as e:
        print(f"处理文件 {file_path} 时出错: {e}")
        return False

def main():
    """主函数"""
    tests_dir = Path(__file__).parent.parent
    
    # 查找所有 Python 测试文件
    test_files = []
    for pattern in ['**/test_*.py', '**/*_test.py', 'conftest.py']:
        test_files.extend(tests_dir.glob(pattern))
    
    updated_count = 0
    for test_file in test_files:
        if update_file_imports(test_file):
            updated_count += 1
    
    print(f"\n总计更新了 {updated_count} 个文件的导入")

if __name__ == '__main__':
    main()
