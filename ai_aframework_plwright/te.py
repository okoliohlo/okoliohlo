import time
from collections import Counter
import re
import os
from functools import wraps



def timer(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        print("Start time: ", start_time)
        result = func(*args, **kwargs)
        end_time = time.time()
        print("End time: ", end_time)
        total_time = (end_time - start_time)
        print("Total time: ", total_time)
        return result
    return wrapper

class Me:
    def list_parser(self, data):
        result = [el for el in data if el % 2==0]
        return result

    def string_reversal(self, data):
        if isinstance(data, str):
            el = "".join(reversed(data))
            # el = el[::-1]
            return el
        else:
            raise ValueError("All elements must be strings")

    def get_factorial(self, data):
        if data <= 1:
            return 1
        return data * self.get_factorial(data - 1)

    def dict_counting(self, data):
        return dict(Counter(data))

    def palindrome_check(self, data: str):
        "best option: 0(n), two pointers approach"
        l, r = 0, len(data) -1
        while l < r:
            while l < r and not data[l].isalnum():
                l += 1
            while l < r and not data[r].isalnum():
                r -= 1
            if data[l].lower() != data[r].lower():
                return False
            l += 1
            r -= 1
        return True

        # "accepted option: join()"
        # res = "".join(ch.lower() for ch in data if ch.isalnum())
        # return res == res[::-1]

        # res = re.sub(r"\s+[a-zA-Z0-9]", "", data)
        # res = res[::-1]
        # return res

    def remove_duplicates(self, data):
        # r = []
        # s = set()
        # for i in data:
        #     if i not in r:
        #         r.append(i)
        #     s.add(i)
        r = list(dict.fromkeys(data))
        print(r)

    @timer
    def flut_list(self, data):
        res = []
        for el in data:
            if isinstance(el, list):
                res.extend(self.flut_list(el))
            elif isinstance(el, dict):
                res.extend(self.flut_list(el.values()))
            else:
                res.append(el)
        print(res)
        return res



from functools import wraps
import asyncio
class Concurrency:
    def __init__(self, url_data: list):
        self.url_data = url_data

    @staticmethod
    def exception_checker(func):
        @wraps(func)
        async def inner(self, url, *args):
            try:
                return await func(self, url, *args)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                if "ru" in url:
                    raise ValueError("URL is not valid. BLOCKED FOREVER !!!!") from e
                raise
        return inner

    @exception_checker
    async def fetch_url(self, url):
        await asyncio.sleep(2)
        print (f"Fetched {url} after 0.5 seconds")
        if "ru" in url:
            raise RuntimeError("URL is not valid. BLOCKED FOREVER !!!!")

    async def fetch_urls(self, urls):
        tasks = [self.fetch_url(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        print(results)

    def run(self):
        asyncio.run(self.fetch_urls(self.url_data))

from dataclasses import dataclass
@dataclass
class Data:
    url_google: str
    url_youtube: str

me = Me()
# print(me.list_parser([1,2,34,57,78,5])) # nested number
# print(me.string_reversal("Alex")) [::-1]. "".join(reversed())
# print(me.get_factorial(5))
# print(me.dict_counting("BANANA"))
# print(me.palindrome_check("rac eCar"))
# me.remove_duplicates([1, 10,2,3,4,5,6,4,6,7,7,8,9,10])
# me.flut_list([1,2,3,{"a": 1, "b": 2, "c": 3},4,5,[6],7,8,9,10])


# urls = ["https://google.com", "https://youtube.com"]
# data = Data("https://google.com", "https://youtube.com")
# conc = Concurrency([data.url_youtube, data.url_google])
# conc.run()

import os
import argparse
class Cli:
    def __init__(self, file, save, read):
        self.file = file
        self.save = save
        self.read = read

    @staticmethod
    def get_file_path(file):
        default_path = "D:\\Projects"
        file_path = os.path.join(default_path, file)
        print(file_path)
        if os.path.exists(file_path):
            return file_path
        else: raise FileNotFoundError("File not found")

    @staticmethod
    def __save(file):
        with open(file, "w") as f:
            f.write("Hello ALEX, found me!!!")

    @staticmethod
    def __read(file):
        with open(file, "r") as f:
            print(f.read())

    def run(self):
        file_path = self.get_file_path(self.file)

        if self.read:
            self.__read(file_path)

        if self.save:
            self.__save(file_path)


# parser = argparse.ArgumentParser()
# parser.add_argument("--file", "-f", required=True)
# parser.add_argument("--save" , "-s")
# parser.add_argument("--read", "-r")
# args = parser.parse_args()
# parser = Cli(args.file, args.save, args.read)
# parser.run()


# from collections import defaultdict
# w = ["eat", "tea", "tan", "ate", "nat", "bat"]
# res = defaultdict(list)
# for word in w:
#     r = "".join(sorted(word))
#     res[r].append(word)
#
# data = [
#     {"name": "Alex", "age": 25},
#     {"name": "Bob", "age": 17},
#     {"name": "Chris", "age": 30},
# ]
# res = sorted([el['name'] for el in data if el['age'] >= 18], reverse=True)
# # print(res)
#
#
# class Singleton:
#     _instance = None
#     def __new__(cls):
#         if cls._instance is None:
#             cls._instance = super().__new__(cls)
#         return cls._instance
#
#
# s =Singleton()
# s1 =Singleton()
# print(s is s1)

from selenium import webdriver
from playwright.sync_api import sync_playwright
import threading

class PlaywrightDriver:
    def __init__(self, start_url: str = None):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=False)
        self.context = self.browser.new_context()
        self.page = self.context.new_page()
        self.page.goto(start_url)

class SeleniumDriver:
    def __init__(self, start_url: str = None):
        self.driver = webdriver.Chrome()
        self.driver.maximize_window()
        self.driver.get(start_url)

class DriverFactory:
    _thread_local = threading.local()
    start_url = "https://profile.okoliohlo.com"
    
    def __init__(self, driver_type: str = "selenium"):
        self.driver_type = driver_type

    @classmethod
    def init_playwright(cls):
        """Initialize Playwright driver"""
        if not hasattr(cls._thread_local, 'playwright_driver') or cls._thread_local.playwright_driver is None:
            playwright_driver = PlaywrightDriver(cls.start_url)
            cls._thread_local.playwright_driver = playwright_driver.page

    @classmethod
    def init_selenium(cls):
        """Initialize Selenium driver"""
        if not hasattr(cls._thread_local, 'selenium_driver') or cls._thread_local.selenium_driver is None:
            selenium_driver = SeleniumDriver(cls.start_url)
            cls._thread_local.selenium_driver = selenium_driver.driver

    @classmethod
    def get_driver(cls, driver_type: str = None):
        """Get appropriate driver instance"""
        if not hasattr(cls._thread_local, 'current_driver') or cls._thread_local.current_driver is None:
            if driver_type == "playwright":
                cls.init_playwright()
                cls._thread_local.current_driver = cls._thread_local.playwright_driver
            elif driver_type == "selenium":
                cls.init_selenium()
                cls._thread_local.current_driver = cls._thread_local.selenium_driver
            else:
                raise ValueError("Unsupported driver type. Use 'playwright' or 'selenium'")
        
        return cls._thread_local.current_driver

class TestPlaywright:
    def __init__(self, dr_type):
        self.driver = DriverFactory(dr_type)
        self.dr = self.driver.get_driver(dr_type)
        if dr_type == "selenium":
            raise ValueError("Unsupported driver type. Use 'playwright'")

    def max_window(self):
        """Maximize window using viewport size"""
        self.dr.set_viewport_size({"width": 1920, "height": 1080})
        print("Window maximized to 1920x1080")

    def swipe_down(self):
        """Scroll down using mouse wheel"""
        self.dr.mouse.wheel(0, 500)  # Scroll down by 4000 pixels
        self.dr.wait_for_timeout(2000)


# t = TestPlaywright("playwright")
# t.max_window()
# t.swipe_down()

#
# def logger(func):
#     async def wrapper(*args, **kwargs):
#         print("Calling function")
#         return await func(*args, **kwargs)
#     return wrapper
#
# @logger
# async def fetch():
#     return 42

'''Finds the indices of two numbers that add up to the target using a hash map.
    Time Complexity: O(n), Space Complexity: O(n)
'''
def two_sum(nums: list[int], target: int):
    r = {}
    for i, num in enumerate(nums):
        diff = target - num
        if diff in r:
            return [r[diff], i]
        r[num] = i

# print(two_sum([1,3,5,7, 10], 10))

'''
move zero to the end
'''
def move_zero(nums: list)-> list:
    r = [el for el in nums if el != 0] + [0] * nums.count(0)
    return r

# print(move_zero([1,2,3,0,0,2,4,54,67,8,9,7]))

def merge(nums:list, nums2:list)->list:
    nums[:]= nums + nums2
    return sorted(nums)

# print(merge([1,2,5], [3,4]))



def rotate(nums, k):
    k %= len(nums)

    nums.reverse()
    print("--",nums[:k])
    print("==",nums[k:])
    nums[:k] = reversed(nums[:k])
    nums[k:] = reversed(nums[k:])
    return nums

# print(rotate([1,2,3,4,5], 1))


def max_sum(nums: list):
    r = max(nums)
    return r

# print(max_sum([1,2,3]))


def two_pointer_sorted(nums: list, target):
    nums.sort()
    l, r = 0, len(nums) -1
    while l < r:
        s = nums[l] + nums[r]
        if s == target:
            return nums[l], nums[r]
        elif s < target:
            l += 1
        else:
            r -= 1

# print(two_pointer_sorted([1,2,3,0,0,2,4,54,67,8,9,7], 5))


#longest substring without repeats chr
def long_substr(s:str):
    d = {}
    left = max_len = 0
    for right, ch in enumerate(s):
        if ch in d:
            left = max(left, d[ch] + 1)
        d[ch] = right
        max_len = max(max_len, right - left + 1)
    return max_len

# print(long_substr("abcabcbb"))

# intervals merging
def interval_merge(l: list):
    merged = []
    l_sorted = sorted(l, lambda x: x[0])
    for interval in l_sorted:
        if not merged or interval[0] > merged[-1][1]:
            merged.append(interval)
        else:
            merged[-1][1] = max(merged[-1][1], interval[1])

    return merged


class Truck:
    def axel(self):
        print("4x axel drive")

class Motorcycle:
    def axel(self):
        print("chain drive shaft")

def run(obj):
    obj.axel()

run(Truck())
run(Motorcycle())

