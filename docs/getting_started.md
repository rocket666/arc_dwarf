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

## CLI 工具

```bash
arc-dwarf calibration.a2l binary.elf
```

进入交互式终端后，输入变量名即可查询物理地址和结构体布局。
