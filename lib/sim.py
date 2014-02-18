from collections import defaultdict
import inspect
import logging
from operator import itemgetter

def is_called_by_contract(stack=None, offset=2):
    if stack is None:
        stack = inspect.stack()
    caller_class = stack[offset][0].f_locals['self'].__class__
    return Contract in caller_class.__bases__


class Block(object):

    def __init__(self, timestamp=0):
        self.timestamp = timestamp
        self._storages = defaultdict(Storage)

    @property
    def basefee(self):
        return 1

    def contract_storage(self, key):
        if is_called_by_contract():
            logging.debug("Accessing contract_storage %s" % key)
        return self._storages[key]


class Stop(RuntimeError):
    pass


class Contract(object):

    @property
    def contract(self):
        return self

    def __init__(self, *args, **kwargs):
        self.log = logging.info
        self.warn = logging.warn
        self.error = logging.error
        self.storage = Storage()
        self.txs = []

        # initializing constants
        for (arg, value) in kwargs.iteritems():
            logging.debug("Initializing constant %s = %s" % (arg, value))
            setattr(self, arg, value)

    def mktx(self, recipient, amount, datan, data):
        logging.info("Sending tx to %s of %s" % (recipient, amount))
        self.txs.append((recipient, amount, datan, data))

    def run(self, tx, contract, block):
        raise NotImplementedError("Should have implemented this")

    def stop(self, reason):
        raise Stop(reason)


class Simulation(object):

    def __init__(self):
        self.log = logging.info
        self.warn = logging.warn
        self.error = logging.error

    def run_all(self):
        test_methods = [(name, method, method.im_func.func_code.co_firstlineno) for name, method in inspect.getmembers(self, predicate=inspect.ismethod)
                        if name.startswith('test_')]

        # sort by linenr
        for name, method, linenr in sorted(test_methods, key=itemgetter(2)):
            method()

    def run(self, tx, contract, block=None):
        self.stopped = False
        if block is None:
            block = Block()

        method_name = inspect.stack()[1][3]
        logging.info("RUN %s: %s" % (method_name, tx))

        contract.txs = []

        try:
            contract.run(tx, contract, block)
        except Stop as e:
            if e.message:
                logging.warn("Stopped: %s" % e.message)
                self.stopped = e.message
            else:
                logging.info("Stopped")
                self.stopped = True
        logging.info('-' * 20)


class Storage(object):

    def __init__(self):
        self._storage = defaultdict(int)

    def __getitem__(self, key):
        if is_called_by_contract():
            logging.debug("Accessing storage %s" % key)
        return self._storage[key]

    def __setitem__(self, key, value):
        if is_called_by_contract():
            logging.debug("Setting storage %s to %s" % (key, value))
        self._storage[key] = value

    def __repr__(self):
        return "<storage %s>" % repr(self._storage)


class Tx(object):

    def __init__(self, sender=None, value=0, fee=0, data=[]):
        self.sender = sender
        self.value = value
        self.fee = fee
        self.data = data
        self.datan = len(data)

    def __repr__(self):
        return '<tx sender=%s value=%d fee=%d data=%s datan=%d>' % (self.sender, self.value, self.fee, self.data, self.datan)
