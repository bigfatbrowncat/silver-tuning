import io
import subprocess
from collections.abc import Callable
from typing import List

class RNCutter:
    def __init__(self):
        self.buf = ""

    def push(self, chars):
        """
        Appends buffer with new characters
        """
        self.buf += chars

    def cut(self):
        """
        Cuts the first part uf the collected buffer terminated with \n or \r
        :return: The cut part of the buffer
        """
        for i, c in enumerate(self.buf):
            if c == "\n" or c == "\r":
                res = self.buf[:i+1]
                self.buf = self.buf[i+1:]
                return res
        return None

    def tail(self):
        res = self.buf
        self.buf = []
        return res


def run_app(args: List[str], process_out_line=None, process_err_line=None, print_out=True, print_err=True):
    """

    :param args: The subprocess to run and the arguments to pass to it.
    :param process_out_line: A function that will process each stdout line.
    :param process_err_line: A function that will process each stderr line.
    :param print_out: Either print each stdout line automatically or not
    :param print_err: Either print each stderr line automatically or not
    :return: The return code of the subprocess.
    """
    proc = subprocess.Popen(args=args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    BUF_SIZE = 1

    bout = io.BufferedReader(proc.stdout, BUF_SIZE)
    berr = io.BufferedReader(proc.stderr, BUF_SIZE)
    out_rncut = RNCutter()
    err_rncut = RNCutter()


    def _do_line(breader: io.BufferedReader, rncutter: RNCutter, processor: Callable[[str], None], oe: str):
        read_something = False
        while breader.peek(BUF_SIZE):
            rncutter.push(breader.read(BUF_SIZE).decode("utf-8", errors="ignore"))
            line = rncutter.cut()
            if line:
                line = line.rstrip()
                if print_out:
                    print(f"\r  {oe}: {line}", flush=True, end='\n')
                if processor: processor(line)
                read_something = True
        return read_something


    while proc.poll() is None:
        _do_line(bout, out_rncut, process_out_line, 'O')
        _do_line(berr, err_rncut, process_err_line, 'E')

    while _do_line(bout, out_rncut, process_out_line, 'O'):
        pass

    while _do_line(berr, err_rncut, process_err_line, 'E'):
        pass

    returncode = proc.wait()

    return returncode
