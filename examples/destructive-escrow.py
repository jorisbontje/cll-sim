from sim import Block, Contract, Simulation, Tx, mktx, stop
from random import random

# Constants to modify before contract creation
CUSTOMER = "carol"
MERCHANT = "mike"

PRICE = 39950
CUSTOMER_STAKE=100  #==0 would be fine.
MERCHANT_STAKE=3000

EXPIRATION_DATE = 30 * 86400

SATISFACTION_MESSAGE="happy"

# Status enumeration
S_NEITHER_IN = 0
S_CUSTOMER_IN = 1
S_MERCHANT_IN = 2
S_BOTH_IN = 3

# Constract Storage indexes
I_STATUS = 1000

MIN_FEE = 1000

class DestructiveEscrow(Contract):
    """
    Escrow without third party. Really just insures it is in no-ones interest to fail.
    Destroys ether in case of failure.
    
    Weak counterexample of the idea that ethereum contracts cant do more than
    the real world can.

    TODO 'suicide' the script, reclaiming the script storage?
"""

    def run(self, tx, contract, block):
        if tx.value < MIN_FEE * block.basefee:
            stop("Insufficient fee")
        
        if block.timestamp > EXPIRATION_DATE :
            if status == S_CUSTOMER_IN :
                mktx(CUSTOMER, block.account_balance(contract.address), [])
                stop("Merchant didnt show up, all back to customer")
            if status == S_MERCHANT_IN :
                mktx(MERCHANT, block.account_balance(contract.address), [])
                stop("Customer didnt show up, all back to merchant")

        status = contract.storage[I_STATUS]
        if status < 3: #Joining of the parties.
            if tx.sender == CUSTOMER and tx.value >= PRICE + CUSTOMER_STAKE :
                contract.storage[I_STATUS] = status | S_CUSTOMER_IN
                stop("Customer in")
            if tx.sender == MERCHANT and tx.value >= MERCHANT_STAKE :
                contract.storage[I_STATUS] = status | S_MERCHANT_IN
                stop("Merchant in")
            stop("Donation")
        
        if tx.sender==CUSTOMER and tx.data[0]==SATISFACTION_MESSAGE :
            mktx(MERCHANT, PRICE + MERCHANT_STAKE, 0,[])
            mktx(CUSTOMER, block.account_balance(contract.address), 0,[])
            contract.storage[I_STATUS] = S_NEITHER_IN
            stop("Customer satisfied with result")
#If the customer is not happy, the ether is stuck in the contract forever.
        stop("Donation")
        

# Constants for test purposes
TS = 1392000000

def random_person():
    r=3*random()
    return (CUSTOMER if r<1 else (MERCHANT if r<2 else "anyone"))

DONATOR="silly bastard"
DONATOR_LATER="equally silly bastard"

class DestructiveEscrowRun(Simulation):

    contract = DestructiveEscrow()
    
    def run_tx(self, value=0,sender="",data=[]):
        self.run(Tx(value=value,sender=sender,data=data), self.contract)
    
    def test_insufficient_fee(self,whom= random_person()):
        self.run_tx(sender= whom, value=10)
        assert self.stopped == "Insufficient fee"

    def donation_resulting_test(self, whom,value):
        status_before = self.contract.storage[I_STATUS]
        self.run_tx(sender=whom, value= max(MIN_FEE,value))
        assert self.stopped == "Donation"
        assert status_before == self.contract.storage[I_STATUS]

    def test_outsider_or_too_little(self):
        self.donation_resulting_test("anyone", 2*random()*(PRICE+CUSTOMER_STAKE))
        self.donation_resulting_test(CUSTOMER, random()*(PRICE + CUSTOMER_STAKE)*0.9)
        self.donation_resulting_test(MERCHANT, random()*MERCHANT_STAKE*0.9)

    def test_customer_in(self):
        status_before = self.contract.storage[I_STATUS]
        self.run_tx(sender=CUSTOMER, value=PRICE + CUSTOMER_STAKE)
        assert self.stopped == "Customer in"
        assert self.contract.storage[I_STATUS] == (status_before | S_CUSTOMER_IN)
    
    def test_merchant_in(self):
        status_before = self.contract.storage[I_STATUS]
        self.run_tx(sender=MERCHANT, value= MERCHANT_STAKE)
        assert self.stopped == "Merchant in"
        assert self.contract.storage[I_STATUS] == (status_before | S_MERCHANT_IN)

    def test_reverse_order(self):
        self.contract = DestructiveEscrow()
        self.test_merchant_in()
        self.test_customer_in()

    def test_customer_happy(self):
        self.run_tx(sender=CUSTOMER, value=MIN_FEE, data=[SATISFACTION_MESSAGE])
        assert self.stopped == "Customer satisfied with result"
        assert self.contract.storage[I_STATUS] == S_NEITHER_IN

    def test_customer_random(self):
        self.test_reverse_order()
        self.run_tx(sender=CUSTOMER, value=MIN_FEE, data=[random()])
        assert self.stopped == "Donation"
        assert self.contract.storage[I_STATUS] == S_BOTH_IN
