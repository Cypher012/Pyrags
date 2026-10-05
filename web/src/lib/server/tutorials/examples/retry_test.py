import inngest

from app.core.inngest import inngest_client
from app.embeddings.jobs import embed_and_store_batch, finish_job, prepare_chunks
from app.workflows.document_ingestion import ingestion_failed, parse_job_id
from app.workflows.retry_probe import fail_once


async def test_batch(job_id: str, batch_index: int) -> dict[str, int]:
    await fail_once(job_id)
    return await embed_and_store_batch(job_id, batch_index)


@inngest_client.create_function(
    fn_id="test-document-retry",
    trigger=inngest.TriggerEvent(event="pyrags/document.retry-test"),
    retries=4,
    on_failure=ingestion_failed,
    concurrency=[inngest.Concurrency(limit=1, key="event.data.job_id")],
)
async def test_document_retry(ctx: inngest.Context) -> dict[str, str]:
    job_id = parse_job_id(ctx.event.data.get("job_id"))
    manifest = await ctx.step.run("prepare-chunks", prepare_chunks, job_id)
    for batch_index in range(manifest["batch_count"]):
        await ctx.step.run(
            f"test-batch-{batch_index}", test_batch, job_id, batch_index
        )
    return await ctx.step.run("finish-document", finish_job, job_id)
