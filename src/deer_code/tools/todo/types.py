from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class TodoStatus(str, Enum):
    """TODO 的状态枚举。

    注意：这里用 str + Enum，方便序列化到 JSON（以及在提示词中稳定呈现）。
    """

    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"


class TodoPriority(str, Enum):
    """TODO 的优先级枚举。"""

    low = "low"
    medium = "medium"
    high = "high"


class TodoItem(BaseModel):
    """TODO 条目数据结构（写入到 Agent 的 state 中）。

    这里使用 Pydantic：
    - 为 tool schema 提供更明确的字段约束（例如 id 非负、title 非空）；
    - 便于在多轮对话中稳定地序列化/反序列化。
    """

    id: int = Field(..., ge=0)
    title: str = Field(..., min_length=1)
    priority: TodoPriority = Field(default=TodoPriority.medium)
    status: TodoStatus = Field(default=TodoStatus.pending)
