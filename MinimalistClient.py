import requests


def fetch_file_and_print(url):
    try:
        # 发送HTTP GET请求
        response = requests.get(url)

        # 检查响应状态码
        if response.status_code == 200:
            print("HTTP response message:")
            print(f"status code: {response.status_code}")
            print(f"Response header:\n{response.headers}\n")

            # 获取文件内容并打印
            file_content = response.text
            print("file content:")
            print(file_content)
        else:
            print(f"HTTP request failed, status code: {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"Request exception occurred: {e}")


if __name__ == "__main__":
    # 获取用户输入的文件URL
    file_url = input("Please enter the URL of the file: ")
    fetch_file_and_print(file_url)
