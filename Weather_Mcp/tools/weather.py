import sys
import urllib.parse
import urllib.request




def get_weather_data(location:str)->str:
    """
    Fetches The Weather For Given Location.

    Args:
        Location (str): The City Of Location Name(e.g:London,New York,Amsterdam)
    Returns:
        str: Consise Weather Information For Location.


    """

    try:
        url=f"https://wttr.in/{urllib.parse.quote(location)}?format=3"
        request = urllib.request.Request(url, headers={"User-Agent": "curl/8.0"})
        with urllib.request.urlopen(request, timeout=10) as response:
            result = response.read().decode('utf-8')
            return result.strip()
    except Exception as e:
        return f"Error:{str(e)}"


if __name__ == "__main__":   
    print(get_weather_data("London"))