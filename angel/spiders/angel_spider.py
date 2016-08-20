from scrapy.spiders import CrawlSpider  # , Rule
# from scrapy.linkextractors.sgml import SgmlLinkExtractor
from scrapy.selector import Selector
from scrapy import Request
import json

from angel.items import BasicItem, CompanyItem, PersonItem

FILE_NAME = 'company_urls.txt'


def get_name_url_uid(sel):
    name = sel.xpath('./text()').extract()[0]
    url = sel.xpath('./@href').extract()[0].strip('"\\')
    uid = url.split('/')[-1]
    return name, url, uid


class AngelSpider(CrawlSpider):
    name = "angel"
    allowed_domains = ["angel.co"]
    start_urls = []
    base_path = 'https://angel.co/'

    def __init__(self):
        self.uid_seen = set([])
        self.__class__.get_company_urls()

    @classmethod
    def get_company_urls(cls):
        with open(FILE_NAME, 'r') as infile:
            cls.start_urls = infile.readlines()

    def parse(self, response):
        sel = Selector(response)
        company = CompanyItem()

        # TAGS
        company['entity_type'] = 'company'
        company['uid'] = response.url.split('?')[0].split('/')[-1]
        path_name = '//h1[contains(@class, "js-startup_name")]/text()'
        company['name'] = sel.xpath(path_name).extract()[0].strip('\n')
        path = '//span[@class="js-{}_tags"]/a'

        # Ensure others don't process this copmany
        self.uid_seen.add(company['uid'])
        print(response.url)

        for tag in ["market", "location"]:
            tags = sel.xpath(path.format(tag))
            for item in self.process_attr(tag, tag, tags, company):
                yield item

        s = sel.xpath('//span[@class="js-company_size"]/text()')
        company['size'] = s.extract()[0].strip('\n')
        company['website'] = response.url  # we only store the angel link
        # s = sel.xpath('//a[@class="u-uncoloredLink company_url"]/@href')
        # company['website'] = s.extract()[0]

        # founders
        path = '//div[contains(@class,"founders")]//div[@class="name"]/a'
        founders = sel.xpath(path)
        for item in self.process_attr('founders', 'person', founders, company):
            yield item

        # employees, past employees and investors
        for role, attr in zip(['employee', 'past_employee', 'past_investor'],
                              ['cur_employees', 'past_employees', 'investors']
                              ):
            role_div = sel.xpath('//div[@data-role="{}"]'.format(role))
            for item in self.get_company_attr_by_role(role_div, attr, company):
                yield item

        # advisors
        # funding_rounds
        rounds = sel.xpath('//ul[@class="startup_rounds with_rounds"]/li')
        company['funding'] = set()
        for r in rounds:
            path_stage = './/div[contains(@class,"type")]/text()'
            stage = r.xpath(path_stage).extract()[0].strip('\n')
            sel_amt = r.xpath('.//div[contains(@class, "raised")]')
            if len(sel_amt.xpath('./a')) > 0:
                amt = sel_amt.xpath('./a/text()').extract()[0].strip('\n')
            else:
                amt = sel_amt.xpath('./text()').extract()[0].strip('\n')
            company['funding'].add((stage, amt))

        # PORTFOLIO! (companies invest as well)
        print("\n", company)
        yield company

    def get_investor_dtype(self, sel):
        dtype_class = sel.xpath('./@data-type').extract()
        if len(dtype_class) > 0:
            val = dtype_class[0].strip('"\\')
            dtype = {
                'User': 'person',
                'Startup': 'company',
            }.get(val, 'person')
        else:       # assume a person by default
            dtype = 'person'
        return dtype

    def process_attr(self, attr, type_to, values, company):
        ''' attr: the name of the attribute in the entity
            type_to: the type of the value of the attribute
            values: a list of <a> tags containing the url and name of value
            company: the dict in which the attr is to be stored
        '''
        if len(values) == 0:
            return
        company[attr] = set([])
        for f in values:
            name, url, uid = get_name_url_uid(f)
            company[attr].add(uid)
            if attr == 'investors':
                type_to = self.get_investor_dtype(f)
            if uid not in self.uid_seen:
                self.uid_seen.add(uid)
                # We only want to process 'person' type
                if type_to == 'person':
                    yield Request(url, callback=self.parse_persons)
                else:
                    yield BasicItem(entity_type=type_to, name=name,
                                    website=url, uid=uid)

    def get_company_attr_by_role(self, role_div, attr, company):
        # check if there is a view all button!
        path = './/a[@class="view_all"]/@href'
        view_all_link = role_div.xpath(path)
        if len(view_all_link) == 0:
            employees = role_div.xpath('.//div[@class="name"]/a')
            for item in self.process_attr(attr, 'person', employees, company):
                yield item
        else:
            # more people, send a request, parse the reply!
            request_link = self.base_path + view_all_link.extract()[0]
            args = {'uid': company['uid'], 'attr': attr}
            yield Request(request_link,
                          callback=lambda event, args=args:
                          self.parse_view_all(event, args))

    def parse_view_all(self, response, args):
        ''' The js button "view_all" will return html data about all people.
            We will return additional item for the company with these attrs.
        '''
        company = CompanyItem(uid=args['uid'], entity_type='company')
        attr = args['attr']
        company[attr] = set()

        sel = Selector(response)
        people = sel.xpath('//div[@class="name"]/a')
        for item in self.process_attr(attr, 'person', people, company):
            yield item
        # print(company)
        yield(company)

    def parse_persons(self, response):
        # print(response.url)
        person = PersonItem()
        sel = Selector(response)

        path = '//h1[@itemprop="name"]/text()'
        person['name'] = sel.xpath(path).extract()[0].strip('\n')
        person['website'] = response.url
        person['uid'] = response.url.split('/')[-1]
        person['entity_type'] = 'person'
        roles = ['founder', 'employee', 'past_investor', 'advisor',
                 'board_member']    # using only a subset of roles possible
        path_role = '//div[@data-role="{}"]//a'
        for role in roles:
            companies = sel.xpath(path_role.format(role))
            for item in self.process_attr(role, 'company',
                                          companies, person):
                yield item

        path_skills = '//div[@data-field="tags_skills"]//a'
        skills = sel.xpath(path_skills)
        for item in self.process_attr('skills', 'skill', skills, person):
            yield item

        # Get colleges from 'education' section
        path_ed = '//div[contains(@class,"profile_college_tagger")]/@data-taggings'
        college_data = sel.xpath(path_ed)
        if len(college_data) > 0:
            person['college'] = set()
            colleges = json.loads(college_data.extract()[0])
            for college in colleges:
                name = college['name']
                url = college['tag_url']
                uid = url.split('/')[-1]
                person['college'].add(uid)
                if uid not in self.uid_seen:
                    yield BasicItem(name=name, website=url,
                                    uid=uid, entity_type='college')

        # many pages don't have the section, but have college listed in tags
        path_tag = '//span[span[contains(@class, "{}")]]//a'
        ed_tag = sel.xpath(path_tag.format("collge"))
        if len(ed_tag):
            name, url, uid = get_name_url_uid(ed_tag)
            person['college'].add([uid])
            if uid not in self.uid_seen:
                yield BasicItem(entity_type='college', name=name,
                                website=url, uid=uid)

        location_tag = sel.xpath(path_tag.format("location"))
        if len(location_tag):
            name, url, uid = get_name_url_uid(location_tag)
            person['location'] = set([uid])
            if uid not in self.uid_seen:
                yield BasicItem(entity_type='location', name=name,
                                website=url, uid=uid)

        # print(person)
        yield person
