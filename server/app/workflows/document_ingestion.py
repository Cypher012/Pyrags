from uuid import UUID

import inngest

from app.core.inngest import inngest_clent


@inngest_clent.create_function(
    fn_id="process_task",
    trigger=inngest.TriggerEvent(event="app/task.created"),
    retries=4,
)
async def process_document(ctx: inngest.Context) -> dict[str, str]:
    raw_job_id = ctx.event.data.get("job_id")

    if not isinstance(raw_job_id, str):
        raise TypeError("job_id must be a string")

    job_id = UUID(raw_job_id)
    return {"job_id": str(job_id)}
