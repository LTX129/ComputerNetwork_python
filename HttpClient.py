import requests


def fetch_file_and_print(url):
    """
        Fetches a file from the given URL and prints its content.

        Args:
            url (str): The URL of the file to fetch.

        Returns:
            None
        """
    try:
        # Send an HTTP GET request
        response = requests.get(url)

        # Check the response status code
        if response.status_code == 200:
            file_content = response.text
            print("HTTP response message:")
            print(f"status code: {response.status_code}")
            print(f"Response header:\n{response.headers}\n")
            # Get the file content and print it
            file_content = response.text
            print("file content:")
            print(file_content)
        else:
            print(f"HTTP request failed, status code: {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"Request exception occurred: {e}")


if __name__ == "__main__":
    # Gets the file URL entered by the user
    file_url = input("Please enter the URL of the file: ")
    fetch_file_and_print(file_url)
