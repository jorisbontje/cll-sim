from sim import Contract, Tx, Simulation

class FinancialDerivative(Contract):
    """Financial derivatives contract example from https://www.ethereum.org/whitepaper/ethereum.html#p412"""

    A = "alice"
    D = "datafeed"
    I = "USD"

    def run(self, tx, contract, block):
        if tx.value < 200 * block.basefee:
            self.stop("Insufficient fee")
        if contract.storage[1000] == 0:
            if tx.value < 1000 * 10 ** 18:
                self.stop("Insufficient value")
            contract.storage[1000] = 1
            contract.storage[1001] = 998 * block.contract_storage(self.D)[self.I]
            contract.storage[1002] = block.timestamp + 30 * 86400
            contract.storage[1003] = tx.sender
            self.log("Contract initialized")
        else:
            ethervalue = contract.storage[1001] / block.contract_storage(self.D)[self.I]
            if ethervalue >= 5000 * 10 ** 18:
                self.mktx(contract.storage[1003], 5000 * 10 ** 18, 0, 0)
            elif block.timestamp > contract.storage[1002]:
                self.mktx(contract.storage[1003], ethervalue, 0, 0)
                self.mktx(self.A, 5000 - ethervalue, 0, 0)


class HedgingRun(Simulation):

    contract = FinancialDerivative()

    def test_insufficient_fee(self):
        tx = Tx(sender='alice', value=10)
        self.run(tx, self.contract)
        assert self.stopped == 'Insufficient fee'

    def test_insufficient_value(self):
        tx = Tx(sender='alice', value=1000)
        self.run(tx, self.contract)
        assert self.stopped == 'Insufficient value'
        assert self.contract.storage[1000] == 0

    def test_creation(self):
        tx = Tx(sender='alice', value=1000 * 10 ** 18)
        self.run(tx, self.contract)
        assert self.contract.storage[1000] == 1
