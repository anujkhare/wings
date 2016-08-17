from fake_useragent import UserAgent
import random


class CustomLoggerMiddleware():
    ' Just to verify that we are getting random user agents and proxies set.. '
    def __init__(self):
        pass

    def process_request(self, request, spider):
        # Add desired logging message here.
        spider.logger.info(request.headers)
        spider.logger.info(
            u'User-Agent: {}'.format(request.headers.get('User-Agent'))
        )
        spider.logger.info('Proxy: {}'.format(request.meta.get('proxy', None)))


class RandomUserAgentMiddleware(object):
    def __init__(self):
        print('RandomUserAgent INIT\n')
        super(RandomUserAgentMiddleware, self).__init__()
        self.ua = UserAgent()

    def process_request(self, request, spider):
        random_ua = self.ua.random
        print('Setting random user-agent\n')
        print(str(random_ua))
        spider.logger.info('RandomUserAgentMiddleware set: ' + str(random_ua))
        request.headers.setdefault('User-Agent', self.ua.random)


class RandomProxyMiddleware(object):
    ''' Based on the code by Aivars Kalvans '''
    def __init__(self, settings):
        file_name = settings.get('PROXY_LIST', None)
        if not file_name:
            print('Proxy file not found!')
            raise(ValueError)

        with open(file_name) as infile:
            self.proxies = infile.readlines()

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler.settings)

    def process_request(self, request, spider):
        if 'proxy' in request.meta:
            return
        proxy = random.choice(self.proxies)
        request.meta['proxy'] = proxy
        # check if the proxy will work later!

    def process_exception(self, request, exception, spider):
        proxy = request.meta.get('proxy', '')
        spider.logger.info('Removing failed proxy {}.'.format(proxy))
        try:
            self.proxies.remove(proxy)
        except:
            pass
        if len(self.proxies) == 0:
            print('No more proxies left!')
            raise(ValueError)
