from src.config import database
from src.utils import gather_full_html, jobs_snapshot, create_database, append_to_database


def main() -> None:

    # 1. gather jobs snapshot @ run time 
    html = gather_full_html()
    data = jobs_snapshot(html = html)

    # 2. append to existing database if it exists already, else create it and then append the data
    if database:
        append_to_database(data = data)
    else:
        create_database()
        append_to_database(data = data)

    return None


if __name__ == '__main__':
    main()
