#!/usr/bin/env python

import argparse
import imp
import inspect
import os.path
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), 'lib'))

from sim import Block, Contract, Tx

def get_subclasses(mod, cls):
    """Yield the classes in module ``mod`` that inherit from ``cls``"""
    for name, obj in inspect.getmembers(mod):
        if hasattr(obj, "__bases__") and cls in obj.__bases__:
            yield obj

def load_contract_class(script):
    contract_name = os.path.splitext(os.path.basename(script))[0]
    contract_module = imp.load_source(contract_name, script)

    contracts = list(get_subclasses(contract_module, Contract))
    if len(contracts) < 1:
        raise RuntimeError("No Contract found in %s" % script)
    elif len(contracts) > 1:
        raise RuntimeError("Multiple Contracts found in %s" % script)

    return contracts[0]

def main(script):
    contract_class = load_contract_class(script)
    contract = contract_class()

    block = Block()
    tx = Tx()
    contract.run(tx, block)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("script")
    args = parser.parse_args()
    main(args.script)
