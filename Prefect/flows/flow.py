from prefect import flow, task, get_run_logger

@task
def hello_world(text="Hello World"):
    print(text)
    return text

@flow(retries = 3)
def write_text():
    logger = get_run_logger()

    result = hello_world("hello_world!")

    logger.info(result)

if __name__ == "__main__":

    write_text()

