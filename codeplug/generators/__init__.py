class Sequence:
    def __init__(self, start=0):
        self.i = start

    def next(self):
        self.i += 1
        return self.i
