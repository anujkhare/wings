# TODO: Have a metaclass generate such classes based on the schema. DRY!
import scrapy


class BasicItem(scrapy.Item):
    uid = scrapy.Field()
    entity_type = scrapy.Field()
    website = scrapy.Field()
    name = scrapy.Field()


# some fields need to be translated to corresponding names in the schema
class CompanyItem(BasicItem):
    market = scrapy.Field()
    location = scrapy.Field()
    product = scrapy.Field()
    size = scrapy.Field()
    location = scrapy.Field()
    founders = scrapy.Field()
    cur_employees = scrapy.Field()
    past_employees = scrapy.Field()
    investors = scrapy.Field()
    advisors = scrapy.Field()
    funding = scrapy.Field()


class PersonItem(BasicItem):
    college = scrapy.Field()
    skills = scrapy.Field()
    location = scrapy.Field()
    employee = scrapy.Field()
    founder = scrapy.Field()
    advisor = scrapy.Field()
    past_investor = scrapy.Field()
    board_member = scrapy.Field()
