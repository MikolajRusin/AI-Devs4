from collections.abc import Iterator


def create_batch(
    id2job_desc: dict[int, str],
    batch_size: int = 10,
) -> Iterator[dict[int, str]]:
    batch = {}
    for id, job_desc in id2job_desc.items():
        batch[id] = job_desc
        if len(batch) == batch_size:
            yield batch
            batch = {}
    if batch:
        yield batch
