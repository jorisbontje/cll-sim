from sim import Contract, Tx, Simulation

class DataFeed(Contract):
    """DataFeed contract example from http://www.ethereum.org/ethereum.html#p412"""

    def run(self, tx, contract, block):
        if tx.sender != self.FEEDOWNER:
            self.stop('Sender is not feed owner')
        contract.storage[tx.data[0]] = tx.data[1]

class DataFeedRun(Simulation):

    contract = DataFeed(FEEDOWNER='alice')

    def test_invalid_sender(self):
        tx = Tx(sender='bob')
        self.run(tx, self.contract)
        assert self.stopped == 'Sender is not feed owner'

    def test_valid_sender(self):
        tx = Tx(sender='alice', data=['Temperature', '53.2'])
        self.run(tx, self.contract)
        assert self.contract.storage['Temperature'] == '53.2'
