# REVIEW-04

status: done

## THREAD-01 - resolved - Queue capacity expectation

Q-01: The task text says `test_queue_capacity_validation` should verify ValueError on capacity < 1, but the test only checks `capacity=-1` and explicitly asserts `capacity=0` is valid. Should this align with the task wording (i.e., should 0 raise), or is the intent that 0 maps to rendezvous and remains valid?
A-01: The task wording is shorthand for the overall constraint. The production code at `src/klever/channel.py:565-568` shows mode selection: `capacity == 0` routes to `_RendezvousChannel`, only positive values route to `_QueueChannel`. The `capacity < 1` validation inside `_QueueChannel.__init__` (line 166) never fires for `capacity=0` because that path creates rendezvous instead. So behavior is correct: `capacity=0` is valid (rendezvous), only negative values raise. The test accurately reflects the implementation contract.
