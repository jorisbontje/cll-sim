from sim import Block, Contract, Simulation, Tx, mktx, stop
from random import random
import inspect

# Constants to modify before contract creation.
CUSTOMER = "carol"
MERCHANT = "mike"

MIN_FEE = 1000
MIN_BALANCE = 3000  # Merchants stake.

PRICE = 39950
INCENTIVE = 10000
TOTAL = PRICE+INCENTIVE

# Merchant can:
C_ALLOW  = 1  # Allows a customer to use the script.
C_REFUND = 2  # Refund initiated by merchant.

# Customer can:
C_SATISFIED = 1  # Indicate satisfaction.
# (failing to do so will lock up the funds)

# Constract Storage indexes
I_CUSTOMER  = "customer"   # 1000
I_INCENTIVE = "incentive"  # 1001
I_TOTAL     = "total"      # 1002
I_PAID      = "paid"       # 1003


class LockinEscrow(Contract):
    """
    Escrow without third party. Really just insures it is in no-ones interest
    to fail.

    If the customer doesnt indicate he is happy, the only way to make the
    contract usable for the merchant is to refund more than was ever paid into.

    Counterexample of the idea that ethereum contracts cant do more than the
    real world can, even though it is clearly less desirable than 'real'
    escrow.

    NOTE: 'Offered refunds' might be nice; those would have to be accepted by
    the customer, but dont involve any MIN_BALANCE being taken away from the
    merchant.
"""

    def run(self, tx, contract, block):
        if tx.value < MIN_FEE * block.basefee:
            stop("Insufficient fee")

        customer = contract.storage[I_CUSTOMER]

        if tx.sender == MERCHANT:
            if block.account_balance(contract.address) < MIN_BALANCE:
                stop("Below funds of operation")
            if tx.data[0] == C_ALLOW:
                if customer != 0:  # ..when earlier customer still busy.
                    stop("Customer change blocked")
                contract.storage[I_CUSTOMER]  = tx.data[1]
                contract.storage[I_TOTAL]     = tx.data[2]
                contract.storage[I_INCENTIVE] = tx.data[3]
                stop("Customer allowed")
            if tx.data[0] == C_REFUND and customer != 0:
                refund =  contract.storage[I_PAID]
                refund += contract.storage[I_PAID]*MIN_BALANCE/contract.storage[I_TOTAL]

                mktx(customer, min(refund, contract.storage[I_TOTAL]+MIN_BALANCE), 0, [])
                contract.storage[I_CUSTOMER]  = 0
                contract.storage[I_TOTAL]     = 0
                contract.storage[I_INCENTIVE] = 0
                contract.storage[I_PAID]      = 0
                stop("Customer refunded")
            stop("Merchant topping up")

        if tx.sender == customer:
            contract.storage[I_PAID] = contract.storage[I_PAID] + tx.value - MIN_FEE*block.basefee
            if tx.datan == 1 and tx.data[0] == C_SATISFIED:
                if contract.storage[I_PAID] <= contract.storage[I_TOTAL]:
                    stop("Customer didnt pay enough")
                incentive = contract.storage[I_INCENTIVE]
                mktx(MERCHANT, contract.storage[I_PAID]-incentive, 0, [])
                mktx(customer, incentive, 0, [])
                contract.storage[I_CUSTOMER]  = 0
                contract.storage[I_TOTAL]     = 0
                contract.storage[I_INCENTIVE] = 0
                contract.storage[I_PAID]      = 0
                stop("Customer paid and happy")
            stop("Customer paid(part)")
        stop("Donation")

def random_incentive():
    return INCENTIVE*(0.1 + random())

class LockinEscrowRun(Simulation):

    contract = LockinEscrow()
    block = Block()

    total     = 0
    incentive = 0
    paid      = 0

    def reset(self):
        self.contract  = LockinEscrow()
        self.total     = 0
        self.incentive = 0
        self.paid      = 0

    def run_tx(self, value=0, sender="", data=[]):
        self.run(Tx(value=value, sender=sender, data=data), self.contract, self.block,
                 method_name=inspect.stack()[1][3])

    def test_donate(self, value=max(MIN_FEE, random()*TOTAL)):
        self.run_tx(sender="anyone", value=value)
        assert self.stopped == "Donation"

    def test_merchant_under_balance(self):
        self.contact = LockinEscrow()
        self.run_tx(sender=MERCHANT, value=random()*MIN_BALANCE*0.9)
        self.stopped == "Below funds of operation"

    def test_merchant_allow(self):
        #Test intended when contract not busy.
        assert self.contract.storage[I_CUSTOMER] == 0

        self.block.set_account_balance(self.contract.address, MIN_BALANCE)
        self.incentive = random_incentive()
        self.total     = PRICE + self.incentive
        self.run_tx(sender=MERCHANT, value=MIN_BALANCE + MIN_FEE,
                    data=[C_ALLOW, CUSTOMER, self.total, self.incentive])
        assert self.stopped == "Customer allowed"
        assert self.contract.storage[I_CUSTOMER]  == CUSTOMER
        assert self.contract.storage[I_TOTAL]     == self.total
        assert self.contract.storage[I_INCENTIVE] == self.incentive
        assert self.contract.storage[I_PAID]      == 0

    def test_customer_change_blocked(self):
        r_incentive = random_incentive()
        self.run_tx(sender=MERCHANT, value=MIN_BALANCE + MIN_FEE,
                    data=[C_ALLOW, CUSTOMER, 2*TOTAL, r_incentive])
        assert self.stopped == "Customer change blocked"
        assert self.contract.storage[I_TOTAL]     == self.total
        assert self.contract.storage[I_INCENTIVE] == self.incentive

    def test_customer_pay(self):
        self.paid = random()*PRICE
        self.run_tx(sender=CUSTOMER, value=self.paid + MIN_FEE)
        assert self.stopped == "Customer paid(part)"

    def test_customer_pay_too_little(self):
        self.reset()
        self.test_merchant_allow()
        self.paid = random()*0.9*self.total
        self.run_tx(sender=CUSTOMER, value=self.paid + MIN_FEE, data=[C_SATISFIED])
        assert self.stopped == "Customer didnt pay enough"
        assert len(self.contract.txs) == 0

    def assert_reset(self):
        assert self.contract.storage[I_CUSTOMER]  == 0
        assert self.contract.storage[I_TOTAL]     == 0
        assert self.contract.storage[I_INCENTIVE] == 0
        assert self.contract.storage[I_PAID]      == 0

    def assert_happy(self):
        assert self.stopped == "Customer paid and happy"
        self.assert_reset()

    def test_customer_pay_and_happy(self):
        self.reset()
        self.test_merchant_allow()
        self.paid = self.total + 1
        self.run_tx(sender=CUSTOMER, value=self.paid + MIN_FEE, data=[C_SATISFIED])
        assert self.contract.txs[0][0] == MERCHANT
        assert self.contract.txs[0][1] == self.paid - self.incentive
        assert self.contract.txs[1][0] == CUSTOMER
        assert self.contract.txs[1][1] == self.incentive
        self.assert_happy()

    def test_customer_pay_part(self):
        self.assert_reset()
        self.test_merchant_allow()
        self.paid = self.total + 1
        self.run_tx(sender=CUSTOMER, value=self.paid + MIN_FEE)
        assert self.stopped == "Customer paid(part)"  # (all, actually)
        assert self.contract.storage[I_PAID] == self.total + 1

    def test_customer_happy(self):  # depends on the pay one being run first.
        self.paid += 1
        self.run_tx(sender=CUSTOMER, value=MIN_FEE + 1, data=[C_SATISFIED])
        assert self.contract.txs[0][0] == MERCHANT
        assert self.contract.txs[0][1] == self.paid - self.incentive
        assert self.contract.txs[1][0] == CUSTOMER
        assert self.contract.txs[1][1] == self.incentive
        self.assert_happy()

    def test_refund(self):
        self.test_customer_pay_part()
        self.run_tx(sender=MERCHANT, value=MIN_FEE, data=[C_REFUND])
        assert self.stopped == "Customer refunded"
        assert self.contract.txs[0][0] == CUSTOMER
        assert self.contract.txs[0][1] == min(self.paid*(1 + MIN_BALANCE/self.total),
                                              self.total + MIN_BALANCE)
        self.assert_reset()
