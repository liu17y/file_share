"""
测试真实场景：模拟前端的分片大小计算
"""
import asyncio
import os
import sys

# 添加 backend 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from upload_manager import upload_manager
from config import settings


async def test_real_world_scenario():
    """测试真实场景：6017601 字节的文件，2MB chunkSize"""
    print("=" * 60)
    print("测试真实场景：模拟前端上传 PDF 文件")
    print("=" * 60)
    
    # 初始化上传管理器
    await upload_manager.start_processor()
    
    # 真实文件信息（来自日志）
    file_id = "test_real_pdf"
    file_name = "test_document.pdf"
    file_size = 6017601  # 实际文件大小
    chunk_size = 2 * 1024 * 1024  # 2MB，与前端一致
    
    # 计算分片数量（向上取整）
    total_chunks = (file_size + chunk_size - 1) // chunk_size
    print(f"\n文件信息:")
    print(f"  文件大小：{file_size} bytes")
    print(f"  Chunk 大小：{chunk_size} bytes (2MB)")
    print(f"  总分数：{total_chunks} 个")
    
    # 计算每个分片的实际大小
    for i in range(total_chunks):
        start = i * chunk_size
        end = min(start + chunk_size, file_size)
        actual_chunk_size = end - start
        print(f"  分片 {i}: {actual_chunk_size} bytes (位置：{start}-{end})")
    
    # 初始化上传
    print("\n1. 初始化上传...")
    init_result = await upload_manager.init_upload(
        file_id=file_id,
        file_name=file_name,
        file_size=file_size,
        target_path="",
        total_chunks=total_chunks
    )
    print(f"初始化结果：{init_result}")
    
    # 获取记录的 chunk_size
    upload_info = upload_manager.uploads.get(file_id)
    recorded_chunk_size = upload_info.get("chunk_size") if upload_info else None
    print(f"后端计算的 chunk_size: {recorded_chunk_size}")
    
    # 模拟前端上传每个分片
    print(f"\n2. 上传 {total_chunks} 个分片...")
    
    for i in range(total_chunks):
        # 模拟前端的 slice 逻辑
        start = i * chunk_size
        end = min(start + chunk_size, file_size)
        chunk_data = bytes([i % 256] * (end - start))
        
        print(f"   - 上传分片 {i}: start={start}, end={end}, size={len(chunk_data)}")
        
        result = await upload_manager.save_chunk(file_id, i, chunk_data)
        print(f"     状态：{result.get('file_id')} - 分片 {i} 已接收")
    
    # 等待处理完成
    print("\n3. 等待后台处理完成...")
    await asyncio.sleep(2)
    
    # 检查最终文件
    final_path = os.path.join(settings.base_dir, file_name)
    
    if os.path.exists(final_path):
        actual_size = os.path.getsize(final_path)
        print(f"\n✓ 最终文件存在：{final_path}")
        print(f"  预期大小：{file_size} bytes")
        print(f"  实际大小：{actual_size} bytes")
        
        if actual_size == file_size:
            print(f"  ✓ 文件大小完全匹配！")
            
            # 验证文件内容
            with open(final_path, 'rb') as f:
                content = f.read()
                
            # 验证每个分片的内容
            all_correct = True
            for i in range(total_chunks):
                start = i * chunk_size
                end = min(start + chunk_size, file_size)
                expected_byte = i % 256
                chunk_content = content[start:end]
                
                # 检查分片内容是否正确
                if len(set(chunk_content)) != 1 or chunk_content[0] != expected_byte:
                    print(f"  ✗ 分片 {i} 内容错误！")
                    all_correct = False
            
            if all_correct:
                print(f"  ✓ 所有分片内容正确！文件完好无损！")
                print(f"  ✓ 修复成功！")
            else:
                print(f"  ✗ 文件内容损坏！")
                
            # 清理测试文件
            os.remove(final_path)
            print(f"  已清理测试文件")
        else:
            print(f"  ✗ 文件大小不匹配！差异：{abs(actual_size - file_size)} bytes")
    else:
        print(f"\n✗ 文件不存在")
    
    # 清理
    print("\n4. 清理上传任务...")
    await upload_manager.cancel_upload(file_id)
    print("测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_real_world_scenario())
