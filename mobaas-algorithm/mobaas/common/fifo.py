'''
Class to express a fifoqueue
'''
class FifoQueue:
    def __init__(self, starting_queue):
        if starting_queue:
            self.queue = starting_queue
        else:
            self.queue = []

    def append(self, item):
        self.queue.append(item)

    def pop_first(self):
        first = self.queue[0]
        del self.queue[0]

        return first