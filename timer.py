from datetime import datetime


class Timer:

    def __init__(self, total):
        self.init_time = datetime.timestamp(datetime.now())
        self.curr_time = self.init_time
        self.left_time = 0
        self.item_time = 0
        self.done = 0
        self.total = total
        self.left = total

    def start(self):
        self.init_time = datetime.timestamp(datetime.now())
        self.curr_time = self.init_time

    def add_done(self):
        self.done += 1
        self.left = self.total - self.done
        self.curr_time = datetime.timestamp(datetime.now())
        self.item_time = (self.curr_time - self.init_time) / self.done
        self.left_time = self.item_time * self.left

    def get_time_left(self):
        return self.left_time

    def get_formatted_time_left(self):
        m = int(self.left_time / 60)
        s = int(self.left_time % 60)
        return "{} min. {} sec.".format(str(m), str(s))

    def get_formatted_items_left(self):
        return "{}/{}".format(self.done, self.total)

    def print_left(self, new_line=True):
        print("{}\tleft\t|\t{}\tdone".format(self.get_formatted_time_left(), self.get_formatted_items_left()),
              end=('\n' if new_line else '\r'), flush=True)
