# arc_dwarf/a2l_parser.py
from __future__ import annotations

import re
from typing import Dict, List, Optional


class A2lParser:
    def __init__(self, filepath: str):
        self.filepath = filepath
        # A2L 文件常有特殊字符，忽略即可
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            self.content = f.read()

    def get_variables(self) -> List[Dict[str, str]]:
        """
        解析 A2L 文件，获取测量/标定变量。
        返回列表: [{"name": "变量名", "type": "数据类型", "block": "MEASUREMENT"}, ...]
        """
        results = []

        # 1. 匹配整个配置块 (支持 MEASUREMENT / CHARACTERISTIC / INSTANCE / TYPEDEF_STRUCTURE)
        # re.DOTALL 使得 (.*?) 能够跨行匹配
        block_pattern = re.compile(
            r'/begin\s+(MEASUREMENT|CHARACTERISTIC|INSTANCE|TYPEDEF_STRUCTURE)\s+([a-zA-Z0-9_]+)\s+(.*?)/end\s+\1',
            re.DOTALL
        )

        for match in block_pattern.finditer(self.content):
            block_type = match.group(1)      # 例如 'MEASUREMENT'
            var_name = match.group(2)        # 例如 'gRspCfg'
            body = match.group(3)            # 块内部的多行文本

            data_type = "UNKNOWN"

            # 2. 在块内容中提取 DataType
            # 匹配如: DataType       Rsp_Params_t
            type_match = re.search(r'DataType\s+([a-zA-Z0-9_]+)', body)
            
            if type_match:
                data_type = type_match.group(1)
            else:
                # 3. 回退机制：处理标准的纯基于位置的 A2L
                # 如: /begin MEASUREMENT gRspCfg "描述" Rsp_Params_t ...
                # 变量名后紧跟包含在双引号内的字符串，接着就是类型名
                fallback_match = re.search(r'^\s*"(?:[^"\\]|\\.)*"\s+([a-zA-Z0-9_]+)', body)
                if fallback_match:
                    data_type = fallback_match.group(1)

            results.append({
                "block": block_type,
                "name": var_name,
                "type": data_type
            })

        return results

    def get_variable_type(self, var_name: str) -> Optional[str]:
        """快速根据变量名查询对应的数据类型"""
        for v in self.get_variables():
            if v["name"] == var_name:
                return v["type"]
        return None
