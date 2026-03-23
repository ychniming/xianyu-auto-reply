"""
变量替换模块

负责处理消息中的变量替换，支持预定义变量和自定义变量。
"""

from typing import Dict, Any

from loguru import logger


class VariablesHandler:
    """变量处理器

    支持的变量：
    - {用户名} / {send_user_name}
    - {用户ID} / {send_user_id}
    - {消息内容} / {send_message}
    - {商品ID} / {item_id}
    - 以及自定义变量
    """

    def apply(
        self,
        result: Dict[str, Any],
        variables: Dict[str, str]
    ) -> Dict[str, Any]:
        """应用变量替换

        Args:
            result: 匹配结果
            variables: 变量字典

        Returns:
            Dict: 替换后的结果
        """
        if result.get('type') == 'image':
            return result

        reply = result.get('reply', '')
        if not reply:
            return result

        try:
            standard_vars = {
                '用户名': variables.get('send_user_name', variables.get('用户名', '')),
                '用户ID': variables.get('send_user_id', variables.get('用户ID', '')),
                '消息内容': variables.get('send_message', variables.get('消息内容', '')),
                '商品ID': variables.get('item_id', variables.get('商品ID', '')),
            }

            all_vars = {**standard_vars, **variables}

            safe_vars = {}
            for key, value in all_vars.items():
                if value is None:
                    safe_vars[key] = ''
                else:
                    safe_vars[key] = str(value).replace('{', '{{').replace('}', '}}')

            formatted_reply = reply.format(**safe_vars)
            result['reply'] = formatted_reply

        except KeyError as e:
            logger.warning(f"变量替换失败，缺少变量: {e}")
        except Exception as e:
            logger.error(f"变量替换异常: {e}")

        return result
