import requests


def fetch_file_and_print(url):
    try:
        # 发送HTTP GET请求
        response = requests.get(url)

        # 检查响应状态码
        if response.status_code == 200:
            print("HTTP 响应信息:")
            print(f"状态码: {response.status_code}")
            print(f"响应头:\n{response.headers}\n")

            # 获取文件内容并打印
            file_content = response.text
            print("文件内容:")
            print(file_content)
        else:
            print(f"HTTP 请求失败，状态码: {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"发生请求异常: {e}")


if __name__ == "__main__":
    # 获取用户输入的文件URL
    file_url = input("请输入文件的URL地址: ")
    fetch_file_and_print(file_url)
