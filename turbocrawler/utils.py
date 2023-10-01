import os


def create_file_path(file_path: str):
    directory = os.path.dirname(file_path)
    os.makedirs(directory, exist_ok=True)
    if not os.path.exists(file_path):
        with open(file_path, 'w'):
            ...


if __name__ == '__main__':
    path = '/home/jorge/Desktop/github/crawler_manager/a/b/c.txt'
    create_file_path(path)

    crawled_queue = ['v1a', 'v2', 'v2']

    with open(path, 'a') as file:
        for url in crawled_queue:
            file.writelines(crawled_queue)
