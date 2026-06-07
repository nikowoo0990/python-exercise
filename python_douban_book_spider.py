# 引入标准库及第三方库
import re

import requests
from bs4 import BeautifulSoup
from lxml import etree

# 定义爬虫目标网址
URL = "https://book.douban.com/subject/36319002/"

# 模拟浏览器请求头
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36"
}

# 作者、出版社、出品方位于页面模板同一模块，构造函数提取
def get_bs_text_by_label(soup, label_text, next_tag="a"):
    label = soup.find("span", class_="pl", string=lambda s: s and label_text in s)
    if not label:
        return None
    target = label.find_next(next_tag)
    return target.get_text(strip=True) if target else None


# 出版日期、页数和定价位于页面模板同一模块，构造函数提取
def get_xpath_tail(info_element, label_text):
    if info_element is None:
        return None
    elements = info_element.xpath(f".//span[@class='pl'][contains(text(), '{label_text}')]")
    return elements[0].tail.strip() if elements and elements[0].tail else None


# 豆瓣评分、评价人数和短评数量有类似数据类型，构造函数清洗
def get_first_text(text_list):
    return text_list[0].strip() if text_list else None

# 报错预估
try:
    # 使用requests请求、监测并赋值
    response = requests.get(URL, headers=HEADERS, timeout=(3, 10))
    response.raise_for_status()
    html = response.text

    # 使用BeautifulSoup解析html，提取出豆瓣图书详情页以下信息：书名、作者、出版社、出品方、副标题
    soup = BeautifulSoup(html, "html.parser")
    # 提取书名
    title_tag = soup.find("span", {"property": "v:itemreviewed"})
    title = title_tag.get_text(strip=True) if title_tag else None
    # 提取作者
    author = get_bs_text_by_label(soup, "作者")
    # 提取出版社
    press = get_bs_text_by_label(soup, "出版社")
    # 提取出品方
    producer = get_bs_text_by_label(soup, "出品方")
    # 提取副标题（若无副标题则不提取，或提取外文书原作名）
    original_title_label_tag = soup.find("span", class_="pl", string=lambda s: s and "原作名" in s)
    original_title_value_tag = original_title_label_tag.next_sibling if original_title_label_tag else None
    original_title = original_title_value_tag.strip() if original_title_value_tag and original_title_value_tag.strip() else None

    # 使用XPath解析html，提取出豆瓣图书详情页以下信息：出版日期、页数、定价、豆瓣评分、评价人数、短评数量
    tree = etree.HTML(html)
    if tree is None:
        raise ValueError("etree解析html失败")
    # 为提取出版日期、页数和定价进行前置解析
    info_elements = tree.xpath(".//div[@id='info']")
    info_element = info_elements[0] if info_elements else None
    # 提取出版日期
    publication_date = get_xpath_tail(info_element, "出版年")
    # 提取页数
    pages = get_xpath_tail(info_element, "页数")
    # 提取定价
    price = get_xpath_tail(info_element, "定价")
    # 提取豆瓣评分和评价人数
    rating_elements = tree.xpath("//div[@class='rating_self clearfix']")
    rating_element = rating_elements[0] if rating_elements else None
    # 提取豆瓣评分
    rating_num_text_list = rating_element.xpath(".//strong[contains(@class, 'rating_num')]/text()") if rating_element is not None else []
    rating_num = get_first_text(rating_num_text_list)
    # 提取评价人数
    rating_people_text_list = rating_element.xpath(".//a[@class='rating_people']/span/text()") if rating_element is not None else []
    rating_people = get_first_text(rating_people_text_list)
    # 提取短评数量
    comments_elements = tree.xpath("//div[@id='comments-section']//span[contains(text(),'短评')]")
    comments_label_element = comments_elements[0] if comments_elements else None
    comments_value_element = comments_label_element.getnext() if comments_label_element is not None else None
    comments_text_list = comments_value_element.xpath(".//a/text()") if comments_value_element is not None else []
    comments = get_first_text(comments_text_list)

    # 使用re进行正则匹配，提取出短评数量中的数字部分
    comments_num_match = re.search(r"\d+", comments) if comments else None
    comments_num = comments_num_match.group() if comments_num_match else None

    # 提取出对应信息后，按照字典格式进行打印
    book_info_items = [
        ("书名", title),
        ("作者", author),
        ("出版社", press),
        ("出品方", producer),
        ("原作名", original_title),
        ("出版年", publication_date),
        ("页数", pages),
        ("定价", price),
        ("豆瓣评分", rating_num),
        ("评价人数", rating_people),
        ("短评数量", comments_num),
    ]
    for key, value in book_info_items:
        print(f"{key}：{value}")

# 报错返回
except requests.RequestException as e:
    print(f"请求失败：{e}")
except Exception as e:
    print(f"发生错误：{e}")