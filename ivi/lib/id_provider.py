
class IdProvider(object):

    def __init__(self, start_with_id=0):
        self.current_id = start_with_id
        self.id_to_item = dict()
        self.item_to_id = dict()

    def next_id(self):
        next_id = self.current_id
        self.current_id += 1
        return next_id

    def is_registered(self, item):
        return item in self.item_to_id

    def register(self, item):
        if self.is_registered(item):
            raise Exception("item %r is already registered" % item)
        assigned_id = self.current_id
        self.set_(assigned_id, item)
        self.current_id += 1
        return assigned_id

    def set_(self, id_, item):
        self.id_to_item[id_] = item
        self.item_to_id[item] = id_

    def unregister(self, item):
        if not self.is_registered(item):
            raise Exception("can not remove item %r as it is not registered yet" % item)
        id_ = self.lookup_id(item)
        del self.id_to_item[id_]
        del self.item_to_id[item]
        return id_

    def lookup_id(self, item):
        return self.item_to_id.get(item)

    def lookup_item(self, id_):
        return self.id_to_item.get(id_)

    def get_items_iter(self):
        return self.item_to_id.iterkeys()

