from scrapy.spiders import Spider
from scrapy.selector import Selector
from scrapy.http import FormRequest
from scrapy import Request
import json

# from angel.items import CompanyListItem

# angel.co allows only 20 entries per page (JS container, infinite scrolling), and a maximum of 20
# pages to be loaded per query. This makes it impossible to directly scrape the list of all startups
# in India (~1600) since the max we can get is 400.
# So, we extract the startups by market. I will use the list of markets that we got from the first
# 400 companies, and expect it to contain a good sample containing most market types.
# Each company can have multiple market tags, and hence it is required to store the ids of the
# companies we have already extracted to prevent duplication.
COMPANIES_PER_PAGE = 20

search_headers = {
    'Host': 'angel.co',
    'Connection': 'keep-alive',
    'Origin': 'https://angel.co',
    'X-CSRF-Token': 'lyKZto35B/QCfa8X2Zxtg1y9wsCUnihaDeouhQADbGk=',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'Accept': '*/*',
    'X-Requested-With': 'XMLHttpRequest',
    'Referer': 'https://angel.co/companies?locations[]=India&company_types[]=Startup',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US,en;q=0.8'
}

request_headers = {
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Encoding': 'gzip, deflate, sdch, br',
    'Accept-Language': 'en-US,en;q=0.8',
    'Connection': 'keep-alive',
    'Host': 'angel.co',
    'Referer': 'https://angel.co/companies?locations[]=India&company_types[]=Startup',
    'X-CSRF-Token': 'ws0MivY1n8F3JG1IKaL+5n6fytuC1097Uehu8l5jNLI=',
    'X-Requested-With': 'XMLHttpRequest'
}

class CompanyListSpider(Spider):
    name = "companylist"
    allowed_domains = ["angel.co"]
    start_urls = [
        "https://angel.co/companies?locations[]=India&company_types[]=Startup"
    ]
    companies_base_url = 'https://angel.co/companies/startups?{}'
    form_request_url = 'https://angel.co/company_filters/search_data'

    completed = False

    def __init__(self):
        with open('markets.csv', 'r') as infile:
            self.markets = infile.read()
            self.markets = self.markets.split(',')
        if len(self.markets) == 0:
            print('No markets found!')
            raise(ValueError)

        self.markets = self.markets
        self.companies_seen = set([])
        self.cur_market_ind = 0
        self.next_page_num = 1
        self.first_page = True

    def parse(self, response):
        ''' The initial page is the form page with infinite scrolling. We need
            to get the id's of the next items by submitting the form, and then
            load them by submitting another POST request.
        '''

        # Process the html data received from self.parse_search_data
        if not self.first_page:
            print('PROCESSING COMPANIES', self.next_page_num - 1)
            self.parse_companies(response)
            for company in self.parse_companies(response):
                yield company

        # Make a form request for the set of ids on the next page of results
        if not self.completed:
            formdata = {
              'filter_data[locations][]': 'India',
              'filter_data[company_types][]': 'Startup',
              'sort': 'signal'
            }
            if self.next_page_num > 1:
                formdata['page'] = str(self.next_page_num)

            formdata['filter_data[markets][]'] = self.markets[self.cur_market_ind]
            self.logger.info(formdata)
            print('\nREQUESTING PAGE', self.next_page_num - 1)
            yield FormRequest(self.form_request_url,
                              formdata=formdata,
                              headers=search_headers,
                              dont_filter=True,
                              callback=self.parse_search_data)

        self.next_page_num += 1

    def parse_search_data(self, response):
        ''' The search form returns a list of ids in json, using which another
            request is made, returning html info about the companies..'''
        self.logger.info(response.text)
        jsonresponse = json.loads(response.text)
        page = jsonresponse['page']
        total = jsonresponse['total']
        ids = jsonresponse['ids']

        params_list = ['ids%5B%5D={}'.format(id) for id in ids]
        params_list.append('total={}'.format(total))
        params_list.append('page={}'.format(page))
        params_list.append('sort={}'.format(jsonresponse['sort']))
        params_list.append('new={}'.format(jsonresponse['new']))
        params_list.append('hexdigest={}'.format(jsonresponse['hexdigest']))
        params = '&'.join(params_list)

        # angel.co only allows you to view first 20 pages for any query
        # if page >= 20:
        if page >= 20 or page * COMPANIES_PER_PAGE >= total:
            print('MARKET', self.markets[self.cur_market_ind], 'IS DONE!\n')
            self.cur_market_ind += 1
            self.next_page_num = 1
            if self.cur_market_ind >= len(self.markets):
                self.completed = True
            else:
                print('STARTING market', self.markets[self.cur_market_ind])

        # print(self.companies_base_url.format(params))
        self.first_page = False
        yield Request(self.companies_base_url.format(params),
                      headers=request_headers)

    def parse_companies(self, response):
        sel = Selector(response)
        companies = sel.xpath('//div[@class="base startup"]')
        for company in companies:
            try:
                attrs = {}
                attrs['name'] = company.xpath('.//div[@class="name"]/a/text()').extract()[0]
                if attrs['name'] in self.companies_seen:
                    continue
                attrs['website'] = company.xpath('.//div[@class="website"]/a/@href').extract()[0]
                attrs['pitch'] = company.xpath('.//div[@class="pitch"]/text()').extract()[0]
                attrs['img'] = company.xpath('.//div[@class="photo"]//img/@src').extract()[0]
                attrs['link'] = company.xpath('.//div[@class="name"]/a/@href').extract()[0]
                attrs['market'] = company.xpath('.//div[@data-column="market"]//a/text()').extract()[0]
                value_path = './/div[@data-column="{}"]/div[@class="value"]/text()'
                attr_list = ['stage', 'raised', 'company_size', 'joined']
                for attr in attr_list:
                    attrs[attr] = company.xpath(value_path.format(attr)).extract()[0]

                self.companies_seen.add(attrs['name'])
                yield attrs
            except:
                print('SOMETHING went wrong!')
                print(response.text)
