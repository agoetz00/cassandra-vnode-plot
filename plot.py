#!/usr/bin/python
import re
import sys
import math
from itertools import tee, izip
from decimal import Decimal
import histogram

DATACENTER_SEPERATOR = re.compile("""^Datacenter\\: """, re.MULTILINE)
IP_REGEX = re.compile("""^(?:[0-9]{1,3}\.){3}[0-9]{1,3}""")
WHITESPACE_REGEX = re.compile("\s+")
BIG = math.pow(2, 64)

class Color:
   PURPLE = '\033[95m'
   CYAN = '\033[96m'
   DARKCYAN = '\033[36m'
   BLUE = '\033[94m'
   GREEN = '\033[92m'
   YELLOW = '\033[93m'
   RED = '\033[91m'
   BOLD = '\033[1m'
   UNDERLINE = '\033[4m'
   END = '\033[0m'

def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return izip(a, b)


if __name__ == """__main__""":
    ring_input = re.split(DATACENTER_SEPERATOR, sys.stdin.read())
    ring_input.pop(0) # pop the whitepsace

    dc_data = []

    for dc_input in ring_input:
        host_to_tokens = {}
        token_to_host = {}
        token_list = []
        token_ownership = {}
        host_ownership = {}

        dc_lines = dc_input.split("\n")
        dc_name = dc_lines.pop(0)
        for line in dc_lines:
            node = IP_REGEX.match(line)
            if node:
                node_data = line.split()
                ip = node_data[0]
                token = int(node_data[-1])

                host_data = host_to_tokens.get(ip, [])
                host_data.append(token)
                host_to_tokens[ip] = host_data

                token_to_host[token] = ip
                token_list.append(token)

        token_list = sorted(token_list)

        for x, token in pairwise(token_list):
            ownership = ((token + BIG) - (x + BIG))
            token_ownership[token] = (ownership / BIG)

        token_ownership[token_list[0]] = (((BIG - token_list[-1]) + (BIG + token_list[0])) / BIG) - 1

        for (host, tokens) in host_to_tokens.items():
            ownership = 0
            for token in tokens:
                ownership += token_ownership[token]

            host_ownership[host] = histogram.DataPoint(Decimal(ownership * 100), 1)

        (options, args) = histogram.build_options()

        print "==============================================="
        print "Ownership for DC:", dc_name
        print "total ownership: ", reduce(lambda x, y: x+y, token_ownership.values()) * 100

        print "\nhost ownership histogram:"
        (mean, variance, standard_deviation, median) = histogram.histogram(host_ownership.values(), options)
        standard_deviation = Decimal(standard_deviation)

        print "\nper host ownership percentage:"
        print "address        \ttokens\tpercent\t\tdeviantion"
        for i in sorted(host_ownership.items(), lambda x, y: cmp(x[1][0], y[1][0])):
            host = i[0]
            percentage = i[1][0]
            highlight = False
            tokens = len(host_to_tokens[host])

            if percentage > median + standard_deviation \
               or percentage < median - standard_deviation:
                highlight = True

            output = "%s\t%s\t%s\t%s" % (host.ljust(15), tokens, float(percentage), float(percentage / median))

            if highlight:
                print(Color.RED + output + Color.END)
            else:
                print(output)
