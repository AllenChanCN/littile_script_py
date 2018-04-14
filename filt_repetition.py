#!/usr/bin/env python

tfile = "/tmp/err.log"
sfile = "/tmp/error.log"

def main():
    file_list = []
    with open(tfile) as rfobj:
        with open(sfile, 'w') as wfobj:
            for line in rfobj:
                if line.strip() not in file_list or line.strip().strtswith("#"):
                    file_list.append(line.strip())
                    wfobj.write(line)
                else:
                    continue

if __name__ == "__main__":
    main()
