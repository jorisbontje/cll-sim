from sim import Contract

class SubCurrency(Contract):
    """Sub-currency contract example from http://www.ethereum.org/ethereum.html#p411"""

    MYCREATOR = "alice"

    def run(self, tx, block):
        if tx.value < 100 * block.basefee:
            return
        elif self.contract.storage[1000]:
            frm = tx.sender
            to = tx.data[0]
            value = tx.data[1]
            if to <= 1000:
                return
            if self.contract.storage[frm] < value:
                return
            self.contract.storage[frm] = self.contract.storage[frm] - value
            self.contract.storage[to] = self.contract.storage[to] + value
        else:
            self.contract.storage[self.MYCREATOR] = 10 ** 18
            self.contract.storage[1000] = 1
