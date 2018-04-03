def count_bulls_cows(word, guess):
    bull_count = 0
    cow_count = 0

    bulls = []

    cindex = 0
    for char in word:
        if char == guess[cindex]:
            bull_count += 1
            bulls.append(char)
        cindex+=1

    for char in word:
        if char in bulls:
            continue
        if char in guess:
            cow_count += 1

    return bull_count, cow_count

def is_isogram(string):
    string = string.lower()
    for char in string:
        if string.count(char) > 1:
            return False
    return True

def range_inclusive(start, end):
    list = []
    for i in xrange(start, end + 1):
        list.append(i)
    return list

def strange_inclusive(start, end):
    stri = ""
    for i in xrange(start, end + 1):
        stri = stri + str(i)
        if i != end:
            stri = stri + ","
    return stri
