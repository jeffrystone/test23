import time
from concurrent.futures import ProcessPoolExecutor
from common.db.engine import init_db

from _logging import *
from container import envs, get_conn
from use_cases import process_fl

INTERVAL = envs.POLLING_INTERVAL  # in seconds
PLATFORMS = [process_fl]
logger = logging.getLogger(__name__)


def main():
    init_db(get_conn())

    next_launch_time = time.time()

    with ProcessPoolExecutor(max_workers=len(PLATFORMS)) as pool:
        while True:
            now = time.time()
            if now >= next_launch_time:
                futures = []

                for pl in PLATFORMS:
                    futures.append(pool.submit(pl))

                for f in futures:
                    try:
                        f.result()
                    except Exception as e:
                        logger.critical(e, exc_info=True)

                next_launch_time = now + INTERVAL

            time.sleep(5)


if __name__ == "__main__":
    if not envs.DEBUG:
        main()
    else:
        init_db(get_conn())
        # Не переопределять TELEGRAM_CHANNEL_ID — брать из src/.env
        # envs.TELEGRAM_CHANNEL_ID = "258365292"
        process_fl()
