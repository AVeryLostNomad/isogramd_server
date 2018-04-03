import string
import itertools
import random
import game_util

initial_consonants = (set(string.ascii_lowercase) - set('aeiou')
                      # remove those easily confused with others
                      - set('qxc')
                      # add some crunchy clusters
                      | set(['bl', 'th', 'tn', 'ph', 'rh', 'mhr', 'shr', 'sh'])
                      )

final_consonants = (set(string.ascii_lowercase) - set('aeiou')
                    # confusable
                    - set('qxcsj')
                    # crunchy clusters
                    | set(['ct', 'ft', 'mp', 'nd', 'ng', 'nk', 'nt',
                           'pt', 'sk', 'sp', 'ss', 'st'])
                    )

vowels = 'aeiou' # we'll keep this simple

# each syllable is consonant-vowel-consonant "pronounceable"
syllables = map(''.join, itertools.product(initial_consonants,
                                           vowels,
                                           final_consonants))

# you could trow in number combinations, maybe capitalized versions...

def gibberish(wordcount, wordlist=syllables):
    return ' '.join(random.sample(wordlist, wordcount))

def generate_isogramic_username():
    matches = False
    while not matches:
        username = ""

        for values in xrange(0, 2):
            username += random.choice(gibberish(5).split())

        if game_util.is_isogram(username):
            matches = True
    return username.title()


