from app.api_requests import client
import time

def wait_on_run(run, thread):
    while run.status in ["queued", "in_progress"]:
        time.sleep(0.5)
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id,
        )
    return run