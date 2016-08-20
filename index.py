# I forgot to create an index by entity type in the initial run, so post
# processin now.. In future addition queries, the value will be indexed
# automatically.
#
# Ex: person -> set of all person type uids in db
import redis

r = redis.StrictRedis()
uid_keys = r.keys("*:uid")
num_failed = 0
types_count = {}

for key in uid_keys:
    key_str = key.decode('utf-8')
    uid = key_str.split(':')[0]
    try:
        key_type = uid + ':type'
        # print(key_type)
        entity_type = r.smembers(key_type).pop()
        # print(entity_type)
        r.sadd(entity_type, uid)
        if entity_type not in types_count:
            types_count[entity_type] = 0
        types_count[entity_type] = types_count[entity_type] + 1
    except:
        # print(uid, 'failed')
        num_failed += 1

print(len(uid_keys), 'total uids read')
print(num_failed, 'failed')
for key, value in types_count.items():
    print('{}: {}'.format(key.decode('utf-8'), value))
