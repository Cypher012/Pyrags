import inngest

from app.core.inngest import inngest_clent
from app.embeddings.jobs import dispatch_pending_jobs


@inngest_clent.create_function(
    fn_id="dispatch-pending-documents",
    trigger=inngest.TriggerCron(cron="* * * * *"),
    retries=4,
    concurrency=[inngest.Concurrency(limit=1)],
)
async def dispatch_ingestion(ctx: inngest.Context) -> dict[str, int]:
    return await ctx.step.run("dispatch-pending-jobs", dispatch_pending_jobs)
