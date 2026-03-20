# 验证分片计算逻辑
file_size = 6011026
chunk_size = 2 * 1024 * 1024  # 2MB

import math
total_chunks = math.ceil(file_size / chunk_size)

print(f"文件大小：{file_size} bytes")
print(f"Chunk 大小：{chunk_size} bytes (2MB)")
print(f"总分数：{total_chunks} 个\n")

total_calculated = 0
for i in range(total_chunks):
    start = i * chunk_size
    end = min(start + chunk_size, file_size)
    actual_size = end - start
    total_calculated += actual_size
    print(f"分片{i}: start={start}, end={end}, size={actual_size} bytes")

print(f"\n计算总和：{total_calculated} bytes")
print(f"原始大小：{file_size} bytes")
print(f"匹配：{total_calculated == file_size}")
