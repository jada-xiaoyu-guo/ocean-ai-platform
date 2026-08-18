"""
PyTorch CPU 推理加速工具
为所有模块提供统一的 CPU 优化配置，包括线程控制、inference_mode、MKLDNN 等。
"""
import os
import torch


def setup_cpu_acceleration(num_threads: int = None, interop_threads: int = 2) -> None:
    """
    配置 PyTorch CPU 推理加速。

    调用时机：在模型加载之前调用一次即可。

    参数:
        num_threads: 运算符内并行线程数。默认取 CPU 逻辑核心数，上限 16。
        interop_threads: 运算符间并行线程数。默认 2。
    """
    if num_threads is None:
        cpu_count = os.cpu_count() or 4
        num_threads = min(cpu_count, 16)

    # 运算符内并行（矩阵乘法、卷积等）
    torch.set_num_threads(num_threads)

    # 运算符间并行（不同 op 的并行执行）
    torch.set_num_interop_threads(interop_threads)

    # 环境变量也一并设置，确保 numpy / MKL / OpenBLAS 统一
    threads_str = str(num_threads)
    os.environ.setdefault("OMP_NUM_THREADS", threads_str)
    os.environ.setdefault("MKL_NUM_THREADS", threads_str)
    os.environ.setdefault("OPENBLAS_NUM_THREADS", threads_str)
    os.environ.setdefault("NUMEXPR_NUM_THREADS", threads_str)
    os.environ.setdefault("VECLIB_MAXIMUM_THREADS", threads_str)

    # 启用 MKLDNN（oneDNN）— PyTorch ≥ 1.0 默认开启，显式确认
    if hasattr(torch.backends, "mkldnn"):
        torch.backends.mkldnn.enabled = True

    # 对于不使用 autograd 的推理场景，推荐 inference_mode 而非 no_grad
    # 各模块需要在 with torch.inference_mode(): 块中执行推理

    print(f"[CPU加速] 已启用: threads={num_threads}, interop={interop_threads}, "
          f"MKLDNN={getattr(torch.backends, 'mkldnn', type('', (), {'enabled': 'unknown'})()).enabled}")


def inference_context():
    """
    返回推理上下文管理器。

    用法:
        with inference_context():
            output = model(input)
    """
    return torch.inference_mode()
