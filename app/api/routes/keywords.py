"""关键字管理路由模块

提供关键字的增删改查接口
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import pandas as pd
import io
from loguru import logger

from app.api.dependencies import get_current_user, check_cookie_owner
from app.api.response import success, error, created, updated, deleted

router = APIRouter(prefix="", tags=["关键字管理"])

# -------------------- 请求/响应模型 --------------------
class KeywordImportRequest(BaseModel):
    keywords: List[Dict[str, str]]


class DefaultReplyIn(BaseModel):
    enabled: bool
    reply_content: Optional[str] = None


class KeywordAdvancedIn(BaseModel):
    """关键词高级输入模型"""
    keyword: str
    reply: str
    item_id: Optional[str] = None
    match_type: Optional[str] = 'contains'  # contains/exact/regex/prefix/suffix/fuzzy
    priority: Optional[int] = 0
    reply_mode: Optional[str] = 'single'  # single/random/sequence
    replies: Optional[str] = None  # JSON字符串，多回复列表
    
    def validate_fields(self):
        """验证字段值"""
        valid_match_types = {'contains', 'exact', 'regex', 'prefix', 'suffix', 'fuzzy'}
        if self.match_type not in valid_match_types:
            raise ValueError(f"无效的 match_type 值: {self.match_type}，有效值为: {valid_match_types}")
        
        if self.priority is not None and (self.priority < 0 or self.priority > 100):
            raise ValueError(f"priority 必须在 0-100 之间，当前值: {self.priority}")
        
        valid_reply_modes = {'single', 'random', 'sequence'}
        if self.reply_mode not in valid_reply_modes:
            raise ValueError(f"无效的 reply_mode 值: {self.reply_mode}，有效值为: {valid_reply_modes}")
        
        return True


class KeywordAdvancedListIn(BaseModel):
    """关键词列表输入模型"""
    keywords: List[KeywordAdvancedIn]


# -------------------- 关键字路由 --------------------
@router.get("/keywords/{cid}")
def get_keywords(cid: str, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """获取账号的关键字列表"""
    try:
        from app.repositories import db_manager
        return success(data=db_manager.get_keywords(cid))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/keywords-with-item-id/{cid}")
def get_keywords_with_item_id(cid: str, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """获取账号的关键字列表（包含商品ID）"""
    try:
        from app.repositories import db_manager
        return success(data=db_manager.get_keywords_with_item_id(cid))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/keywords-with-type/{cid}")
def get_keywords_with_type(cid: str, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """获取账号的关键字列表（包含类型和新字段）
    
    返回字段：
    - keyword: 关键词
    - reply: 回复内容
    - item_id: 商品ID
    - type: 类型 (text/image)
    - image_url: 图片URL
    - match_type: 匹配类型 (contains/exact/regex/prefix/suffix/fuzzy)
    - priority: 优先级 (0-100)
    - reply_mode: 回复模式 (single/random/sequence)
    - replies: 多回复列表JSON
    - sequence_index: 顺序回复当前索引
    - trigger_count: 触发次数
    """
    try:
        from app.repositories import db_manager
        return success(data=db_manager.get_keywords_with_type(cid))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/keywords/{cid}")
def save_keywords(cid: str, keywords: List[List[str]], current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """保存关键字列表"""
    try:
        from app.repositories import db_manager
        # keywords格式: [[keyword, reply], ...]
        kw_list = [(kw[0], kw[1]) for kw in keywords]
        db_manager.save_keywords(cid, kw_list)
        return success(message="关键词保存成功")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/keywords-with-item-id/{cid}")
def save_keywords_with_item_id(cid: str, request: KeywordAdvancedListIn, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """保存关键字列表（支持所有新字段）
    
    支持的字段：
    - keyword: 关键词 (必填)
    - reply: 回复内容 (必填)
    - item_id: 商品ID (可选)
    - match_type: 匹配类型 contains/exact/regex/prefix/suffix/fuzzy (默认contains)
    - priority: 优先级 0-100 (默认0)
    - reply_mode: 回复模式 single/random/sequence (默认single)
    - replies: 多回复列表JSON (可选)
    """
    try:
        from app.repositories import db_manager
        # 转换为数据库格式
        keywords_advanced = []
        for kw in request.keywords:
            # 验证每个关键词的字段
            try:
                kw.validate_fields()
            except ValueError as ve:
                raise HTTPException(status_code=400, detail=str(ve))
            
            keywords_advanced.append({
                'keyword': kw.keyword,
                'reply': kw.reply,
                'item_id': kw.item_id,
                'match_type': kw.match_type or 'contains',
                'priority': kw.priority or 0,
                'reply_mode': kw.reply_mode or 'single',
                'replies': kw.replies,
                'conditions': None
            })
        
        db_manager.save_keywords_advanced(cid, keywords_advanced)
        return success(data={'count': len(keywords_advanced)}, message="关键词保存成功")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/keywords/{cid}/{index}")
def delete_keyword(cid: str, index: int, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """删除指定索引的关键字"""
    try:
        from app.repositories import db_manager
        if db_manager.delete_keyword_by_index(cid, index):
            return deleted(message="关键词删除成功")
        else:
            raise HTTPException(status_code=404, detail="关键字索引无效")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/keywords/stats/{cid}")
def get_keyword_stats(cid: str, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """获取关键词统计信息
    
    返回字段：
    - total_count: 关键词总数
    - type_stats: 按类型统计 {text: count, image: count}
    - match_type_stats: 按匹配类型统计 {contains: count, exact: count, ...}
    - total_triggers: 总触发次数
    """
    try:
        from app.repositories import db_manager
        return success(data=db_manager.get_keyword_stats(cid))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class KeywordTestIn(BaseModel):
    """关键词测试输入模型"""
    message: str
    item_id: Optional[str] = None
    user_id: Optional[str] = None
    user_name: Optional[str] = None


class KeywordTestResult(BaseModel):
    """关键词测试结果模型"""
    matched: bool
    keyword: Optional[str] = None
    reply: Optional[str] = None
    match_type: Optional[str] = None
    item_id: Optional[str] = None
    position: Optional[tuple] = None
    reply_mode: Optional[str] = None
    reply_index: Optional[int] = None


@router.post("/keywords/test/{cid}", response_model=KeywordTestResult)
def test_keyword_match(
    cid: str,
    request: KeywordTestIn,
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
):
    """测试关键词匹配（不发送真实消息）

    用于在前端配置关键词后验证匹配逻辑是否正确。

    Args:
        cid: 账号ID
        request: 测试请求，包含：
            - message: 测试消息内容
            - item_id: 商品ID（可选）
            - user_id: 用户ID（可选）
            - user_name: 用户名（可选）

    Returns:
        KeywordTestResult: 匹配结果，包含：
            - matched: 是否匹配到关键词
            - keyword: 匹配的关键词
            - reply: 将要回复的内容
            - match_type: 匹配类型
            - item_id: 关联的商品ID
            - position: 匹配位置
            - reply_mode: 回复模式
            - reply_index: 顺序回复索引
    """
    try:
        from app.core.keyword_matcher import keyword_matcher
        from app.repositories import db_manager

        # 构建变量字典（用于变量替换）
        variables = {
            'send_user_name': request.user_name or '测试用户',
            'send_user_id': request.user_id or 'test_user',
            'send_message': request.message,
            'item_id': request.item_id or '',
        }

        # 执行匹配
        result = keyword_matcher.match(
            cookie_id=cid,
            message=request.message,
            item_id=request.item_id,
            variables=variables
        )

        if result:
            return KeywordTestResult(
                matched=True,
                keyword=result.get('keyword'),
                reply=result.get('reply'),
                match_type=result.get('match_type'),
                item_id=result.get('item_id'),
                position=result.get('position'),
                reply_mode=result.get('reply_mode'),
                reply_index=result.get('reply_index')
            )
        else:
            return KeywordTestResult(matched=False)

    except Exception as e:
        logger.error(f"关键词测试失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/keywords/cache-refresh/{cid}")
def refresh_keyword_cache(cid: str, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """刷新关键词匹配器缓存
    
    当关键词数据发生变更时，调用此接口刷新内存中的关键词匹配器缓存。
    通常在以下情况需要手动刷新：
    - 直接修改数据库中的关键词数据
    - 批量导入关键词后
    - 缓存与数据库不一致时
    """
    try:
        from app.core.keyword_matcher import keyword_matcher
        from app.repositories import db_manager
        
        # 获取该账号的所有关键词
        keywords = db_manager.get_keywords_with_type(cid)
        
        if keywords:
            # 重建自动机
            result = keyword_matcher.rebuild(cid, keywords)
            if result:
                return success(data={'keyword_count': len(keywords)}, message="缓存刷新成功")
            else:
                raise HTTPException(status_code=500, detail="缓存刷新失败")
        else:
            # 没有关键词，清除缓存
            keyword_matcher.clear(cid)
            return success(data={'keyword_count': 0}, message="缓存已清除")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/keywords-export/{cid}")
def export_keywords(cid: str, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """导出账号的关键字为Excel（支持所有新字段）"""
    try:
        from app.repositories import db_manager
        keywords = db_manager.get_keywords_with_type(cid)

        if not keywords:
            return success(message="没有关键词可导出")

        df = pd.DataFrame(keywords)
        output = io.BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)

        from fastapi.responses import StreamingResponse
        return StreamingResponse(
            output,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition': f'attachment;filename=keywords_{cid}.xlsx'}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/keywords-import/{cid}")
async def import_keywords(cid: str, file: UploadFile = File(...), current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """从Excel导入关键字（支持所有新字段）
    
    支持的列：
    - keyword: 关键词 (必填)
    - reply: 回复内容 (必填)
    - item_id: 商品ID (可选)
    - match_type: 匹配类型 (可选，默认contains)
    - priority: 优先级 (可选，默认0)
    - reply_mode: 回复模式 (可选，默认single)
    - replies: 多回复列表JSON (可选)
    """
    try:
        from app.repositories import db_manager

        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents), engine='openpyxl')

        keywords = []
        for _, row in df.iterrows():
            if 'keyword' in row and 'reply' in row:
                keyword_data = {
                    'keyword': row['keyword'],
                    'reply': row['reply'],
                    'item_id': row.get('item_id') if pd.notna(row.get('item_id')) else None,
                    'match_type': row.get('match_type', 'contains') if pd.notna(row.get('match_type')) else 'contains',
                    'priority': int(row.get('priority', 0)) if pd.notna(row.get('priority')) else 0,
                    'reply_mode': row.get('reply_mode', 'single') if pd.notna(row.get('reply_mode')) else 'single',
                    'replies': row.get('replies') if pd.notna(row.get('replies')) else None,
                    'conditions': None
                }
                keywords.append(keyword_data)

        if keywords:
            db_manager.save_keywords_advanced(cid, keywords)

        return success(data={'count': len(keywords)}, message="关键词导入成功")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/keywords/{cid}/image")
async def upload_keyword_image(cid: str, keyword: str, file: UploadFile = File(...), current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """上传关键字配图"""
    try:
        from app.utils.image_uploader import upload_image
        from app.repositories import db_manager

        contents = await file.read()
        image_url = await upload_image(contents)

        if image_url:
            db_manager.save_image_keyword(cid, keyword, image_url)
            return success(data={'image_url': image_url}, message="图片上传成功")
        else:
            raise HTTPException(status_code=500, detail="图片上传失败")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/debug/keywords-table-info")
def debug_keywords_table(current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """调试：获取keywords表结构信息"""
    try:
        from app.repositories import db_manager
        cursor = db_manager.conn.cursor()
        cursor.execute("PRAGMA table_info(keywords)")
        columns = cursor.fetchall()
        cursor.execute("SELECT COUNT(*) FROM keywords")
        count = cursor.fetchone()[0]
        return success(data={'columns': columns, 'count': count})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/default-replies/{cid}')
def get_default_reply(cid: str, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """获取账号的默认回复设置"""
    try:
        from app.repositories import db_manager
        return success(data=db_manager.get_default_reply(cid) or {'enabled': False, 'reply_content': ''})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put('/default-replies/{cid}')
def update_default_reply(cid: str, request: DefaultReplyIn, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """更新账号的默认回复设置"""
    try:
        from app.repositories import db_manager
        db_manager.save_default_reply(cid, request.enabled, request.reply_content)
        return updated(message="默认回复设置更新成功")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get('/default-replies')
def get_all_default_replies(current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """获取所有默认回复设置"""
    try:
        from app.repositories import db_manager
        return success(data=db_manager.get_all_default_replies())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete('/default-replies/{cid}')
def delete_default_reply(cid: str, current_user: Optional[Dict[str, Any]] = Depends(get_current_user)):
    """删除账号的默认回复设置"""
    try:
        from app.repositories import db_manager
        db_manager.delete_default_reply(cid)
        return deleted(message="默认回复设置删除成功")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
