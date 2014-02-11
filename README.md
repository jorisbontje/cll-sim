# Ethereum CLL Contract Emulator

## Usage

`./run.py examples/subcurrency.py`

## Example Output

```
sim          INFO    RUN test_insufficient_fee: <tx sender=alice value=10 fee=0 data=[] datan=0>
subcurrency  WARNING Insufficient basefee
sim          INFO    --------------------
sim          INFO    RUN test_creation: <tx sender=alice value=100 fee=0 data=[] datan=0>
sim          DEBUG   Accessing storage 1000
subcurrency  INFO    Initializing storage for creator alice
sim          DEBUG   Setting storage alice to 1000000000000000000
sim          DEBUG   Setting storage 1000 to 1
sim          INFO    --------------------
sim          INFO    RUN test_alice_to_bob: <tx sender=alice value=100 fee=0 data=['bob', 1000] datan=2>
sim          DEBUG   Accessing storage 1000
sim          DEBUG   Accessing storage alice
subcurrency  INFO    Transfering 1000 from alice to bob
sim          DEBUG   Accessing storage alice
sim          DEBUG   Setting storage alice to 999999999999999000
sim          DEBUG   Accessing storage bob
sim          DEBUG   Setting storage bob to 1000
sim          INFO    --------------------
sim          INFO    RUN test_bob_to_charlie_invalid: <tx sender=bob value=100 fee=0 data=['charlie', 1001] datan=2>
sim          DEBUG   Accessing storage 1000
sim          DEBUG   Accessing storage bob
sim          DEBUG   Accessing storage bob
subcurrency  WARNING Insufficient funds, bob has 1000 needs 1001
sim          INFO    --------------------
sim          INFO    RUN test_bob_to_charlie_valid: <tx sender=bob value=100 fee=0 data=['charlie', 1000] datan=2>
sim          DEBUG   Accessing storage 1000
sim          DEBUG   Accessing storage bob
subcurrency  INFO    Transfering 1000 from bob to charlie
sim          DEBUG   Accessing storage bob
sim          DEBUG   Setting storage bob to 0
sim          DEBUG   Accessing storage charlie
sim          DEBUG   Setting storage charlie to 1000
sim          INFO    --------------------
subcurrency  INFO    <storage defaultdict(<type 'int'>, {1000: 1, 'charlie': 1000, 'bob': 0, 'alice': 999999999999999000})>
```

## License
Released under the MIT License.
