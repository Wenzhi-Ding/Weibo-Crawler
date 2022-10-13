import sys
import os
sys.path.append(os.path.dirname(__file__) + '/..')

from util.summary import format_summary

if __name__ == '__main__':
    print(format_summary())