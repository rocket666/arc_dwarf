# 快速上手

## 安装

```bash
pip install -e ".[dev]"
```

## 基本用法

### 解析 ELF/DWARF 类型信息

```python
from arc_dwarf import DwarfTypeExplorer, TypeTreeDumper, DumpOptions

with DwarfTypeExplorer("your_binary.elf") as ex:
    dumper = TypeTreeDumper(ex)
    out = dumper.dump("YourStruct_t", options=DumpOptions(max_depth=6))
    print(out.text())
```

### 获取变量物理地址

```python
from arc_dwarf import DwarfTypeExplorer

with DwarfTypeExplorer("your_binary.elf") as ex:
    info = ex.get_variable_info("gMyVariable")
    if info:
        addr, size = info
        print(f"地址: 0x{addr:08X}, 大小: {size} bytes")
```

### 解析 A2L 标定文件

```python
from arc_dwarf import A2lParser

parser = A2lParser("calibration.a2l")
variables = parser.get_variables()
for v in variables:
    print(f"{v['name']}: {v['type']} ({v['block']})")
```

### 解析成员路径偏移

通过 `resolve_member_offset()` 可沿点分路径逐层解析结构体成员的偏移量：

```python
from arc_dwarf import DwarfTypeExplorer

with DwarfTypeExplorer("your_binary.elf") as ex:
    offset, type_str, sizeof = ex.resolve_member_offset(
        "Rsp_Params_t",
        "RspFastTimeCmbCtrlParam.FftCtrl.cfg_fft_size"
    )
    print(f"偏移: 0x{offset:04X}, 类型: {type_str}, 大小: {sizeof} bytes")
```

### 获取成员物理地址

`get_member_address()` 将变量基地址与成员偏移相加，直接返回运行时物理地址：

```python
from arc_dwarf import DwarfTypeExplorer

with DwarfTypeExplorer("your_binary.elf") as ex:
    result = ex.get_member_address(
        var_name="gRspCfg",
        member_path="RspFastTimeCmbCtrlParam.FftCtrl.cfg_fft_win_addr",
        type_name="Rsp_Params_t"  # 可选，省略时自动从 DWARF 推断
    )
    print(f"基地址:   0x{result.base_address:08X}")
    print(f"成员偏移: 0x{result.member_offset:04X}")
    print(f"物理地址: 0x{result.address:08X}")
    print(f"类型: {result.type_str}, 大小: {result.sizeof} bytes")
```

路径支持数组下标访问，例如 `"arr[2].field"`。

返回值为 `MemberAddress` 数据对象，包含以下字段：

| 字段 | 说明 |
|------|------|
| `var_name` | 全局变量名 |
| `member_path` | 点分成员路径 |
| `base_address` | 变量基地址（来自符号表） |
| `member_offset` | 成员在结构体内的累计偏移 |
| `address` | 物理地址（`base_address + member_offset`） |
| `type_str` | 最终成员的类型名 |
| `sizeof` | 最终成员的字节大小 |

## CLI 工具

```bash
arc-dwarf calibration.a2l binary.elf
```

进入交互式终端后，输入变量名即可查询物理地址和结构体布局。
