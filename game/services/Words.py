import game_util
import os
import random


class Words:

    def __init__(self, do_print_debug=False):
        self.corpi = {
            "commonautica": self.load("10k_common_words_english.txt", do_print_debug),
            "esoterica": self.load("english_words.txt", do_print_debug)
        }

    def load(self, file, do_print_debug):
        my_path = os.path.abspath(os.path.dirname(__file__))
        path = os.path.join(my_path, file)
        temp = []
        with open(path) as f:
            temp = f.readlines()
        temp = [x.strip() for x in temp]

        if do_print_debug:
            print("Initialized word databse with " + str(len(temp)) + " english words")

        self.words = []

        for word in temp:
            if game_util.is_isogram(word):
                self.words.append(word)

        if do_print_debug:
            print("From that databse, indexed " + str(len(self.words)) + " isograms")

        temp_words = []

        blacklist = ["-", "&", "_", "'", ".", "/"]
        for word in self.words:
            add = True
            for character in blacklist:
                if character in word:
                    add = False
                    break
            if add:
                temp_words.append(word)

        if do_print_debug:
            print("Pruned " + str(len(self.words) - len(temp_words)) + " words with invalid characters")
        self.words = temp_words

        self.iso_dict = {}

        largest = 0
        for word in self.words:
            this_length = len(word)
            if this_length > largest:
                largest = this_length

        if do_print_debug:
            print("Largest word is " + str(largest) + " characters long")

        for word_length in xrange(1, largest + 1):
            n_grams = []
            for word in self.words:
                this_length = len(word)
                if this_length == word_length:
                    n_grams.append(word)
            self.iso_dict[word_length] = n_grams

        fixed_dict = {}
        for level in self.iso_dict.keys():
            fixed_level = []
            for word in self.iso_dict[level]:
                if word.lower() not in fixed_level:
                    fixed_level.append(word.lower())
            fixed_dict[level] = fixed_level

        if do_print_debug:
            print("Removed " + str(
                self.count_size(self.iso_dict) - self.count_size(fixed_dict)) + " uppercase and duplicate words")

        if do_print_debug:
            print("Final length: " + str(self.count_size(self.iso_dict)))

            for word_length in xrange(1, largest + 1):
                print(word_length, "Amount: " + str(len(self.iso_dict[word_length])), self.iso_dict[word_length])

            print("Estimated that 100% completion would take " + str(
                self.estimate_completion_time(self.iso_dict)) + " seconds")

        return fixed_dict

    def get_word(self, n_size, corpus_name):
        return random.choice(self.corpi[corpus_name][n_size])

    def count_size(self, dict):
        total = 0
        for key in dict.keys():
            total += len(dict[key])
        return total

    def estimate_completion_time(self, word_dict):
        total_time_seconds = 0

        # Eventually pull this from data
        time_by_n_size = {
            1: 0,  # We want to disclude one and two grams, since they will not appear in the game
            2: 0,
            3: 60,
            4: 230,
            5: 600,
            6: 1200,
            7: 1500,
            8: 1800,
            9: 2400,
            10: 3600,
            11: 3875,
            12: 4000,
            13: 4360,
            14: 5000,
            15: 6000
        }

        for key in word_dict.keys():
            for word in word_dict[key]:
                total_time_seconds += time_by_n_size[key]

        return total_time_seconds
