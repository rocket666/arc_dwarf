# API 参考

## `DwarfTypeExplorer`

ELF/DWARF 解析引擎，支持上下文管理器协议。

### 构造函数

```python
DwarfTypeExplorer(elf_path: str)
```

### 方法

- `open()` — 打开 ELF 文件并索引 DWARF 类型信息
- `close()` — 关闭文件句柄
- `find_type_die(type_name: str)` — 根据类型名查找 DWARF DIE
- `parse_struct_or_union_members(die)` — 解析结构体/联合体成员列表
- `type_byte_size(die)` — 计算类型字节大小
- `type_display_name(die)` — 获取类型可读名称
- `get_variable_info(var_name: str)` — 从符号表查找变量地址和大小，返回 `(address, size)` 元组
- `resolve_member_offset(type_name: str, member_path: str)` — 沿点分路径逐层解析成员偏移，返回 `(offset, type_str, sizeof)` 元组
- `get_member_address(var_name: str, member_path: str, type_name: str = None)` — 计算成员的运行时物理地址，返回 `MemberAddress` 对象

---

## `MemberAddress`

成员地址解析结果，由 `get_member_address()` 返回。

```python
@dataclass
class MemberAddress:
    var_name: str          # 全局变量名
    member_path: str       # 点分成员路径
    base_address: int      # 变量基地址（来自符号表）
    member_offset: int     # 成员在结构体内的累计字节偏移
    address: int           # base_address + member_offset
    type_str: str          # 最终成员的类型名
    sizeof: int            # 最终成员的字节大小
```

### `resolve_member_offset()`

```python
resolve_member_offset(type_name: str, member_path: str) -> Tuple[int, str, int]
```

沿点分成员路径逐层解析结构体成员的偏移量。支持数组下标访问（如 `"arr[2].field"`）。

**参数：**

- `type_name` — 顶层类型名，如 `"Rsp_Params_t"`
- `member_path` — 点分成员路径，如 `"RspFastTimeCmbCtrlParam.FftCtrl.cfg_fft_size"`

**返回：** `(accumulated_offset, final_type_str, final_sizeof)`

**异常：** 类型未找到或路径中成员不存在时抛出 `RuntimeError`

### `get_member_address()`

```python
get_member_address(var_name: str, member_path: str, type_name: str = None) -> MemberAddress
```

获取全局变量中某个嵌套成员的运行时物理地址。

**参数：**

- `var_name` — 全局变量名，如 `"gRspCfg"`
- `member_path` — 点分成员路径，如 `"RspFastTimeCmbCtrlParam.FftCtrl.cfg_fft_win_addr"`
- `type_name` — 可选，变量的类型名。省略时从 DWARF 调试信息自动推断

**返回：** `MemberAddress` 数据对象

**异常：** 变量未在符号表中找到、类型无法推断或成员路径无效时抛出 `RuntimeError`

---

## `A2lParser`

A2L (ASAP2) 标定文件解析器。

### 构造函数

```python
A2lParser(filepath: str)
```

### 方法

- `get_variables()` — 提取所有 MEASUREMENT/CHARACTERISTIC/INSTANCE/TYPEDEF_STRUCTURE 变量
- `get_variable_type(var_name: str)` — 根据变量名快速查询数据类型

---

## `TypeTreeDumper`

类型树可视化工具。

### 构造函数

```python
TypeTreeDumper(explorer: DwarfTypeExplorer)
```

### 方法

- `dump(type_name, *, options=None, emitter=None)` — 渲染类型树为文本表格
- `build(type_name, *, options=None)` — 构建 JSON 可序列化的类型树字典

---

## `DumpOptions`

类型树展开配置。

```python
@dataclass
class DumpOptions:
    max_depth: int = 20
    recursive: bool = True
    show_notes: bool = True
    expand_type_names: Optional[Set[str]] = None
    expand_member_names: Optional[Set[str]] = None
    case_insensitive_filters: bool = False
```
