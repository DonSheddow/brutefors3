import subprocess
import tempfile
import sys
import argparse
from enum import Enum

class Result(Enum):
    Success = "Success!"
    AccessDenied = "Access Denied"
    NoSuchBucket = "No Such Bucket"


class Bucket(object):
    def __init__(self, name):
        if not name.startswith("s3://"):
            name = "s3://" + name
        self.name = name

    def parse_output(self, p):
        if p.returncode == 0:
            return Result.Success
        elif b'AccessDenied' in p.stderr:
            return Result.AccessDenied
        elif b'NoSuchBucket' in p.stderr:
            return Result.NoSuchBucket
        else:
            raise ValueError("Error when accessing bucket: " + p.stderr)

    def list_files(self):
        p = subprocess.run(["aws", "s3", "ls", self.name], stderr=subprocess.PIPE)
        return self.parse_output(p)

    def upload_file(self, filename):
        p = subprocess.run(["aws", "s3", "mv", filename, self.name], stderr=subprocess.PIPE)
        return self.parse_output(p)


class BucketTester(object):
    def __init__(self):
        self.test_file = tempfile.mkdtemp() + "/test.txt"
        with open(self.test_file, 'w') as f:
            f.write("Hello, world!\n")

    def test_bucket(self, bucket):
        print("Testing bucket '%s'" % word)
        read_res = bucket.list_files()
        if read_res == Result.NoSuchBucket:
            print("\t" + read_res.value)
        else:
            print("\tRead: " + read_res.value)
            write_res = bucket.upload_file(self.test_file)
            print("\tWrite: " + write_res.value)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Search for readable/writeable S3 buckets.")
    parser.add_argument("wordfile", type=argparse.FileType('r'), help="File containing bucket names to test")

    args = parser.parse_args()
    words = list(map(str.strip, args.wordfile.readlines()))

    tester = BucketTester()

    for word in words:
        b = Bucket(word)
        tester.test_bucket(b)
