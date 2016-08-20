# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
from scrapy.conf import settings
from graphdb.redis.graphlayer import GraphLayerRedis
from graphdb.schema.backlinks import BacklinksHelper


def translate_key(key):
    ' translates the attribute names used for scraping to those in schema '
    return {
        # general
        "location": "located in",
        "entity_type": "type",
        # person
        "college": "studied at",
        "employee": "worked at",
        "founder": "found company",
        # NOTE: not to be confused with "advisors" attr of company
        "advisor": "are advisor at",
        "past_investor": "invested in",
        "board_member": "board member of",
        # company
        "market": "markets",
        "cur_employees": "current employees",
        "past_employees": "past employees",
        "funding": "funding rounds"
    }.get(key, key)


class GraphdbPipeline(object):
    def __init__(self):
        host = settings.get('REDIS_HOST', 'localhost')
        port = settings.get('REDIS_PORT', '6379')
        path_to_schema = settings.get('GRAPH_SCHEMA')
        self.connection = GraphLayerRedis(host=host, port=port)
        self.back_helper = BacklinksHelper(path_to_schema)
        print("Connecting to redis on", host, port)

    def process_item(self, item, spider):
        translated_dict = {}
        for key, value in item.items():
            new_key = translate_key(key)
            translated_dict[new_key] = value

        # get the dicts with reverse attrs
        spider.logger.info('Translated dict is:')
        spider.logger.info(translated_dict)
        backlinks_dict = self.back_helper.get_backlinks(translated_dict)
        spider.logger.info('graphdb: backlinks:')
        spider.logger.info(backlinks_dict)
        # insert into the db
        uid = translated_dict['uid']
        self.connection.set_multiple_edges(**{uid: translated_dict})
        self.connection.set_multiple_edges(**backlinks_dict)

        return item
