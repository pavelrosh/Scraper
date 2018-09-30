import requests
import re
import time
from bs4 import BeautifulSoup
from mongoengine import *
from datetime import datetime
from model import *
# from selenium import webdriver


class Scrapper:
    def __init__(self, category):
        self.category = category
        self.start_scrapping(category)

    @staticmethod
    def get_page(url):
        page = requests.get(url)
        if page.status_code is not 200:
            print("Can't load page, code: {}".format(page.status_code))
            exit(1)
        return BeautifulSoup(page.content, 'html.parser')

    def grab_links(self, url):
        link_list = []
        head = "https://trud.ua"
        page = self.get_page(url)
        while True:
            for i in page.find_all('a', class_="item-link"):
                link_list.append("https://trud.ua{}".format(i.get('href')))
            if page.find('span', class_='next-p disabled') is not None:
                break
            if page.find('a', class_="next-p") is not None:
                page = self.get_page(head + page.find('a', class_="next-p").get('href'))
            else:
                break
        print(len(link_list))
        return link_list

    @staticmethod
    def match_exact_element(element, attr, attr_name):
        return lambda tag: tag.name == element and tag.get(attr) == [attr_name]

    def grab_user(self, url):
        title = ""
        fullname = ""
        age = ""
        ubo = ""
        salary = 0

        page = self.get_page(url)
        title = page.find('div', class_="sub-titl position-t").get_text().strip()
        fullname = page.find('div', class_="head-titl").get_text()\
            .replace("Ищу работу", "").strip()
        age = page.find('td', class_="lbl-gray", text=" Дата рождения ")\
            .find_next_sibling('td').get_text().strip()
        ubo = page.find('td', class_="lbl-gray", text=" Дата размещения ")\
            .find_next_sibling('td').get_text().strip()
        ubo = datetime.strptime(ubo, "%d.%m.%Y").date().isoformat()
        if page.find(self.match_exact_element('div', 'class', 'salary')) is not None:
            salary = int(page.find(self.match_exact_element('div', 'class', 'salary'))
                         .get_text().replace("грн", "").strip())
            u = User(title=title, fullname=fullname, cv_url=url,
                     age=age, updated_by_owner=ubo, salary_amount=salary).save()
        else:
            u = User(title=title, fullname=fullname, cv_url=url,
                     age=age, updated_by_owner=ubo, salary_amount=0).save()
        return self.grab_experience(page)

    @staticmethod
    def grab_experience(page):
        position = ""
        start_date = ""
        end_date = ""
        company_description = ""
        company_name = ""
        job_description = ""
        date_str = ""
        company_tmp = ""
        tmp_parent = ""
        obj_list = []

        tmp_parent = page.find('div', class_="inf-titl no-marg")
        if tmp_parent is None:
            print("This user have no experience")
            return obj_list
        tmp_parent = tmp_parent.parent
        if tmp_parent is not None and tmp_parent.find('div', class_="clearfix") is None:
            for item in tmp_parent.find_all('div', class_="sub-item"):
                position = item.find('div', class_="sub-titl").get_text().strip()
                date_str = item.find('div', class_="lbl-gray").get_text().strip()
                date_str = re.findall(r'\d{2}.\d{4}', date_str)
                start_date = datetime.strptime(date_str[0], "%m.%Y").date().isoformat()
                # print(start_date)
                if len(date_str) > 1:
                    end_date = datetime.strptime(date_str[1], "%m.%Y").date().isoformat()
                else:
                    end_date = None
                company_tmp = item.find('span', class_="view-bold").get_text().strip()
                company_tmp = re.findall("([^\)]+)\((.*)\)", company_tmp)
                company_description = company_tmp[0][1]
                company_name = company_tmp[0][0].strip()
                job_description = item.find('div', class_="txt-inf").get_text().strip()
                exp = WorkExperience(position=position, start_date=start_date,
                                     end_date=end_date, job_description=job_description,
                                     company_description=company_description, company_name=company_name)
                obj_list.append(exp)
        return obj_list

    @staticmethod
    def del_db():
        for u in User.objects:
            u.delete()

    def start_scrapping(self, category):
        connect('Scrupper')
        self.del_db()
        url = "https://trud.ua/search.cv/results/jobcategory/{}.html".format(category)
        link_list = self.grab_links(url)
        counter = 0
        if len(link_list) > 0:
            for link in link_list:
                tmp = self.grab_user(link)
                if len(tmp) > 0:
                    u = User.objects.get(cv_url=link)
                    for exp in tmp:
                        u.list_of_exp.append(exp)
                    u.save()
                counter += 1
                print("User {} was saved".format(counter))
            print("Scrapping {} category is successfully finished.".format(self.category))
        else:
            print("Wrong category name. Please, put another parameter")


if __name__ == '__main__':
    start_time = time.time()
    scrappy = Scrapper("sport")
    # scrappy = Scrapper("proizvodstvo")
    print("--- %s seconds ---" % (time.time() - start_time))
    # scrappy.start_scrapping('')
    # start_scrapping("sport")
    # driver = webdriver.Chrome("D:\Download\chromedriver_win32/chromedriver.exe")
    # driver.get("https://trud.ua/profile/card/id/1181821.html")
    # button = driver.find_element_by_class_name("show-contacts")
    # button.click()
