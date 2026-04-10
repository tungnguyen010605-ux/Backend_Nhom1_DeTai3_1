from __future__ import annotations

import asyncio
from collections import defaultdict
from pathlib import Path
from typing import Awaitable, Callable
from uuid import uuid4

from PIL import Image, ImageDraw

from app.schemas import TaskStatus


class TaskManager:
    def __init__(
        self,
        output_dir: Path,
        max_concurrent_jobs: int = 2,
        on_task_completed: Callable[[int, int, str], None | Awaitable[None]] | None = None,
    ) -> None:
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.max_concurrent_jobs = max_concurrent_jobs
        self.on_task_completed = on_task_completed
        self._semaphore = asyncio.Semaphore(max_concurrent_jobs)
        self._tasks: dict[str, TaskStatus] = {}
        self._listeners: dict[str, set[asyncio.Queue]] = defaultdict(set)

    def create_task(self, user_id: int, clothing_item_id: int) -> TaskStatus:
        task_id = uuid4().hex
        status = TaskStatus(task_id=task_id, status="pending", progress=0, message="Queued")
        self._tasks[task_id] = status
        asyncio.create_task(self._run_task(task_id, user_id, clothing_item_id))
        return status

    def get_task(self, task_id: str) -> TaskStatus | None:
        return self._tasks.get(task_id)

    async def subscribe(self, task_id: str) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue()
        self._listeners[task_id].add(queue)
        return queue

    def unsubscribe(self, task_id: str, queue: asyncio.Queue) -> None:
        listeners = self._listeners.get(task_id)
        if not listeners:
            return
        listeners.discard(queue)

    async def _emit(self, task: TaskStatus) -> None:
        listeners = self._listeners.get(task.task_id, set())
        for queue in listeners:
            await queue.put(task.model_dump())

    async def _update_task(self, task_id: str, status: str, progress: int, message: str, output_url: str | None = None) -> None:
        current = self._tasks[task_id]
        updated = TaskStatus(
            task_id=task_id,
            status=status,
            progress=progress,
            message=message,
            output_url=output_url,
        )
        self._tasks[task_id] = updated
        await self._emit(updated)

    async def _persist_completed_output(self, user_id: int, clothing_item_id: int, output_url: str) -> None:
        if not self.on_task_completed:
            return

        result = self.on_task_completed(user_id, clothing_item_id, output_url)
        if asyncio.iscoroutine(result):
            await result

    async def _run_task(self, task_id: str, user_id: int, clothing_item_id: int) -> None:
        async with self._semaphore:
            try:
                await self._update_task(task_id, "running", 10, "Starting texture generation")
                await asyncio.sleep(0.3)
                await self._update_task(task_id, "running", 50, "Rendering lightweight mock texture")

                image_path = self.output_dir / f"generated_{task_id}.png"
                self._create_mock_texture(image_path, user_id, clothing_item_id)

                await asyncio.sleep(0.2)
                output_url = f"/textures/{image_path.name}"
                await self._persist_completed_output(user_id, clothing_item_id, output_url)
                await self._update_task(task_id, "completed", 100, "Finished", output_url=output_url)
            except Exception as exc:
                await self._update_task(task_id, "failed", 100, f"Failed: {exc}")

    @staticmethod
    def _create_mock_texture(path: Path, user_id: int, clothing_item_id: int) -> None:
        image = Image.new("RGB", (512, 512), color=(36, 36, 46))
        draw = ImageDraw.Draw(image)
        draw.rectangle((32, 32, 480, 480), outline=(124, 198, 255), width=3)
        draw.text((52, 70), f"user_id={user_id}", fill=(235, 235, 245))
        draw.text((52, 110), f"cloth_id={clothing_item_id}", fill=(235, 235, 245))
        draw.text((52, 150), "cpu-safe texture", fill=(157, 216, 255))
        image.save(path, format="PNG", optimize=True)

