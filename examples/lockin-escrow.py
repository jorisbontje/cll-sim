from sim import Block, Contract, Simulation, Tx, mktx, stop
from random import random
import inspect

# Constants to modify before contract creation
CUSTOMER = "carol"
MERCHANT = "mike"

MIN_FEE = 1000
MIN_BALANCE=3000 #Merchants stake.

PRICE = 39950
INCENTIVE = 10000
TOTAL = PRICE+INCENTIVE

#Merchant can:
C_ALLOW = 1 #Allows a customer to use the script.
C_REFUND= 2 #Refund initiated by merchant

# Customer can:
C_SATISFIED = 1 #Indicate satisfaction.
#(failing to do so will lock up the funds)

# Constract Storage indexes
I_CUSTOMER  = "customer"   #1000
I_INCENTIVE = "incentive"  #1001
I_TOTAL     = "total"      # 1002
I_PAID      = "paid"       #1003

class LockinEscrow(Contract):
    """
    Escrow without third party. Really just insures it is in no-ones interest to
    fail.

    If the customer doesnt indicate he is happy, the only way to make the
    contract usable for the merchant is to refund more than was ever paid into.
    
    Counterexample of the idea that ethereum contracts cant do more than the
    real world can, even though it is clearly less desirable than 'real' escrow.
"""

    def run(self, tx, contract, block):
        if tx.value < MIN_FEE * block.basefee:
            stop("Insufficient fee")
        
        customer = contract.storage[I_CUSTOMER]
        
        if tx.sender == MERCHANT :
            if block.account_balance(contract.address) < MIN_BALANCE :
                stop("Below funds of operation")
            if tx.data[0] == C_ALLOW and customer == 0 :
                contract.storage[I_CUSTOMER] = tx.data[1]
                contract.storage[I_TOTAL]    = tx.data[2]
                contract.storage[I_INCENTIVE]= tx.data[3]
                stop("Customer allowed")
            if tx.data[0] == C_REFUND and customer != 0 :
                mktx(customer, contract.storage[I_TOTAL] + MIN_BALANCE,0,[])
                contract.storage[I_CUSTOMER] = 0
                contract.storage[I_TOTAL] = 0
                contract.storage[I_INCENTIVE] = 0
                contract.storage[I_PAID] = 0
                stop("Customer refunded")
            stop("Merchant topping up")
        
        if tx.sender == customer :
            contract.storage[I_PAID] = contract.storage[I_PAID] + tx.value - MIN_FEE*block.basefee
            if tx.datan ==1 and tx.data[0] == C_SATISFIED :
                if contract.storage[I_PAID] <= contract.storage[I_TOTAL] :
                    stop("Customer didnt pay enough")
                mktx(MERCHANT, contract.storage[I_PAID],0,[])
                mktx(customer, contract.storage[I_INCENTIVE],0,[])
                contract.storage[I_CUSTOMER] = 0
                contract.storage[I_TOTAL] = 0
                contract.storage[I_INCENTIVE] = 0
                contract.storage[I_PAID] = 0
                stop("Customer paid and happy")
            stop("Customer paid(part)")
        stop("Donation")

class LockinEscrowRun(Simulation):

    contract = LockinEscrow()
    block = Block()
    
    def run_tx(self, value=0,sender="",data=[]) :
        self.run(Tx(value=value,sender=sender,data=data), self.contract,self.block,
                 method_name= inspect.stack()[1][3])
    
    def test_donate(self, value=max(MIN_FEE,random()*TOTAL)) :
        self.run_tx(sender="anyone", value=value)
        assert self.stopped == "Donation"

    def test_merchant_under_balance(self) :
        self.contact = LockinEscrow()
        self.run_tx(sender=MERCHANT, value= random()*MIN_BALANCE*0.9)
        self.stopped == "Below funds of operation"
    
    def test_merchant_allow(self) :
        self.block.set_account_balance(self.contract.address, MIN_BALANCE)
        self.run_tx(sender=MERCHANT, value= MIN_BALANCE + MIN_FEE,
                   data=[C_ALLOW,CUSTOMER,TOTAL,INCENTIVE])
        self.stopped == "Customer allowed"
        assert self.contract.storage[I_CUSTOMER] == CUSTOMER
        assert self.contract.storage[I_TOTAL] == TOTAL
        assert self.contract.storage[I_INCENTIVE] == INCENTIVE
        assert self.contract.storage[I_PAID] == 0

    def test_customer_pay(self) :
        self.run_tx(sender=CUSTOMER, value= random()*PRICE)
        assert self.stopped =="Customer paid(part)"

    def test_customer_pay_too_little(self) :
        self.contract= LockinEscrow()
        self.test_merchant_allow()
        self.run_tx(sender=CUSTOMER, value= random()*TOTAL, data=[C_SATISFIED])
        assert self.stopped =="Customer didnt pay enough"

    def assert_reset(self) :
        assert self.contract.storage[I_CUSTOMER] == 0
        assert self.contract.storage[I_TOTAL] == 0
        assert self.contract.storage[I_INCENTIVE] == 0
        assert self.contract.storage[I_PAID] == 0

    def assert_happy(self) :
        assert self.stopped =="Customer paid and happy"
        self.assert_reset()

    def test_customer_pay_and_happy(self) :
        self.contract= LockinEscrow()
        self.test_merchant_allow()
        self.run_tx(sender=CUSTOMER, value= TOTAL+MIN_FEE+1, data=[C_SATISFIED])
        self.assert_happy()

    def test_customer_pay(self) :
        #self.contract= LockinEscrow() #not neccesary, happiness should restart.
        self.test_merchant_allow()
        self.run_tx(sender=CUSTOMER, value= TOTAL+MIN_FEE)
        assert self.stopped == "Customer paid(part)" #(all, actually)
        assert self.contract.storage[I_PAID] == TOTAL
        
    def test_customer_happy(self) : #depends on the pay one being run first.
        self.run_tx(sender=CUSTOMER, value= MIN_FEE+1, data=[C_SATISFIED])
        self.assert_happy()

    def test_refund(self) :
        self.test_merchant_allow()
        self.test_customer_pay()
        self.run_tx(sender=MERCHANT, value= MIN_FEE,data=[C_REFUND])
        assert self.stopped == "Customer refunded"
        self.assert_reset()
