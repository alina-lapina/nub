"""Utilities for comparing files and directories.

filecmp library mod by Alina Lapina

Classes:
    dircmp

Functions:
    cmp(f1, f2, shallow=True) -> int
    cmpfiles(a, b, common) -> ([], [], [])
    clear_cache()

"""

import os
import stat
from itertools import filterfalse
import datetime

__all__ = ['clear_cache', 'cmp', 'dircmp', 'cmpfiles', 'DEFAULT_IGNORES']

_cache = {}
BUFSIZE = 8*1024

DEFAULT_IGNORES = [
    'RCS', 'CVS', 'tags', '.git', '.hg', '.bzr', '_darcs', '__pycache__']

def to_file(list, file):
    for item in list:
        file.write('\t' + item + '\n')
    file.write('\n\n')
    
def clear_cache():
    """Clear the filecmp cache."""
    _cache.clear()

def cmp(f1, f2, shallow=True):
    """Compare two files.

    Arguments:

    f1 -- First file name

    f2 -- Second file name

    shallow -- Just check stat signature (do not read the files).
               defaults to True.

    Return value:

    True if the files are the same, False otherwise.

    This function uses a cache for past comparisons and the results,
    with cache entries invalidated if their stat information
    changes.  The cache may be cleared by calling clear_cache().

    """
    s1 = _sig(os.stat(f1))
    s2 = _sig(os.stat(f2))
    print('Decide:')
    print(f1)
    print(f2)
    if s1[0] != stat.S_IFREG or s2[0] != stat.S_IFREG:
        return False
    if shallow and _is_similar(os.stat(f1).st_size, os.stat(f2).st_size):
        return True
    if s1[1] != s2[1]:
        return False

    outcome = _cache.get((f1, f2, s1, s2))
    if outcome is None:
        outcome = _do_cmp(f1, f2)
        if len(_cache) > 100:      # limit the maximum size of the cache
            clear_cache()
        _cache[f1, f2, s1, s2] = outcome
    return outcome

def _sig(st):
    return (stat.S_IFMT(st.st_mode),
            st.st_size,
            st.st_mtime)

def _is_similar(s1, s2):
    print('Sizes: ', s1, ' byte and ', s2, ' byte')
    print('Difference: ', (100 - s1/s2*100),' %', 'same? ', (s1/s2 >= 0.8) and (s1/s2 <= 1.25))
    return (s1/s2 >= 0.8) and (s1/s2 <= 1.25) # +-20%
			
def _do_cmp(f1, f2):
    bufsize = BUFSIZE
    with open(f1, 'rb') as fp1, open(f2, 'rb') as fp2:
        while True:
            b1 = fp1.read(bufsize)
            b2 = fp2.read(bufsize)
            if b1 != b2:
                return False
            if not b1:
                return True

# Directory comparison class.
#
class dircmp:
    """A class that manages the comparison of 2 directories.

    dircmp(a, b, ignore=None, hide=None)
      A and B are directories.
      IGNORE is a list of names to ignore,
        defaults to DEFAULT_IGNORES.
      HIDE is a list of names to hide,
        defaults to [os.curdir, os.pardir].

    High level usage:
      x = dircmp(dir1, dir2)
      x.report() -> prints a report on the differences between dir1 and dir2
       or
      x.report_partial_closure() -> prints report on differences between dir1
            and dir2, and reports on common immediate subdirectories.
      x.report_full_closure() -> like report_partial_closure,
            but fully recursive.

    Attributes:
     left_list, right_list: The files in dir1 and dir2,
        filtered by hide and ignore.
     common: a list of names in both dir1 and dir2.
     left_only, right_only: names only in dir1, dir2.
     common_dirs: subdirectories in both dir1 and dir2.
     common_files: files in both dir1 and dir2.
     common_funny: names in both dir1 and dir2 where the type differs between
        dir1 and dir2, or the name is not stat-able.
     same_files: list of identical files.
     diff_files: list of filenames which differ.
     funny_files: list of files which could not be compared.
     subdirs: a dictionary of dircmp objects, keyed by names in common_dirs.
     """

    def __init__(self, a, b, ignore=None, hide=None): # Initialize
        self.left = a
        self.right = b
        if hide is None:
            self.hide = [os.curdir, os.pardir] # Names never to be shown
        else:
            self.hide = hide
        if ignore is None:
            self.ignore = DEFAULT_IGNORES
        else:
            self.ignore = ignore

    def phase0(self): # Compare everything except common subdirectories
        self.left_list = _filter(os.listdir(self.left),
                                 self.hide+self.ignore)
        self.right_list = _filter(os.listdir(self.right),
                                  self.hide+self.ignore)
        self.left_list.sort()
        self.right_list.sort()

    def phase1(self): # Compute common names
        a = dict(zip(map(os.path.normcase, self.left_list), self.left_list))
        b = dict(zip(map(os.path.normcase, self.right_list), self.right_list))
        self.common = list(map(a.__getitem__, filter(b.__contains__, a)))
        self.left_only = list(map(a.__getitem__, filterfalse(b.__contains__, a)))
        self.right_only = list(map(b.__getitem__, filterfalse(a.__contains__, b)))

    def phase2(self): # Distinguish files, directories, funnies
        self.common_dirs = []
        self.common_files = []
        self.common_funny = []

        for x in self.common:
            a_path = os.path.join(self.left, x)
            b_path = os.path.join(self.right, x)

            ok = 1
            try:
                a_stat = os.stat(a_path)
            except OSError as why:
                # print('Can\'t stat', a_path, ':', why.args[1])
                ok = 0
            try:
                b_stat = os.stat(b_path)
            except OSError as why:
                # print('Can\'t stat', b_path, ':', why.args[1])
                ok = 0

            if ok:
                a_type = stat.S_IFMT(a_stat.st_mode)
                b_type = stat.S_IFMT(b_stat.st_mode)
                if a_type != b_type:
                    self.common_funny.append(x)
                elif stat.S_ISDIR(a_type):
                    self.common_dirs.append(x)
                elif stat.S_ISREG(a_type):
                    self.common_files.append(x)
                else:
                    self.common_funny.append(x)
            else:
                self.common_funny.append(x)

    def phase3(self): # Find out differences between common files
        xx = cmpfiles(self.left, self.right, self.common_files)
        self.same_files, self.diff_files, self.funny_files = xx

    def phase4(self): # Find out differences between common subdirectories
        # A new dircmp object is created for each common subdirectory,
        # these are stored in a dictionary indexed by filename.
        # The hide and ignore properties are inherited from the parent
        self.subdirs = {}
        for x in self.common_dirs:
            a_x = os.path.join(self.left, x)
            b_x = os.path.join(self.right, x)
            self.subdirs[x]  = dircmp(a_x, b_x, self.ignore, self.hide)

    def phase4_closure(self): # Recursively call phase4() on subdirectories
        self.phase4()
        for sd in self.subdirs.values():
            sd.phase4_closure()

    def report(self): # Print a report on the differences between a and b
        # Output format is purposely lousy
        print('diff', self.left, self.right)
        if self.left_only:
            self.left_only.sort()
            print('Only in', self.left, ':', self.left_only)
        if self.right_only:
            self.right_only.sort()
            print('Only in', self.right, ':', self.right_only)
        if self.same_files:
            self.same_files.sort()
            print('Similar files :', self.same_files)
        if self.diff_files:
            self.diff_files.sort()
            print('Differing files :', self.diff_files)
        if self.funny_files:
            self.funny_files.sort()
            print('Trouble with common files :', self.funny_files)
        if self.common_dirs:
            self.common_dirs.sort()
            print('Common subdirectories :', self.common_dirs)
        if self.common_funny:
            self.common_funny.sort()
            print('Common funny cases :', self.common_funny)
            
    def report_mod(self, file):
        file.write('\nCOMPARISON OF FILES BETWEEN FOLDERS:\n\n')
        file.write(self.left + '\n and \n' + self.right + '\n')
        if self.left_only:
            self.left_only.sort()
            file.write('\nOnly in '+ self.left + ':\n')
            to_file(self.left_only, file)
        if self.right_only:
            self.right_only.sort()
            file.write('\nOnly in '+ self.right + ':\n')
            to_file(self.right_only, file)
        if self.same_files:
            self.same_files.sort()
            file.write('\nSimilar files :\n')
            to_file(self.same_files, file)
        if self.diff_files:
            self.diff_files.sort()
            file.write('\nDiffering files :\n')
            to_file(self.diff_files, file)
        if self.funny_files:
            self.funny_files.sort()
            file.write('\nTrouble with common files :\n')
            to_file(self.funny_files, file)
        if self.common_dirs:
            self.common_dirs.sort()
            file.write('\nCommon subdirectories :\n')
            to_file(self.common_dirs, file)
        if self.common_funny:
            self.common_funny.sort()
            file.write('\nCommon funny cases :\n')
            to_file(self.common_funny, file)
	
    def report_partial_closure(self): # Print reports on self and on subdirs
        self.report()
        for sd in self.subdirs.values():
            print()
            sd.report()

    def report_full_closure(self, file): # Report on self and subdirs recursively
        self.report_mod(file)
        for sd in self.subdirs.values():
            print()
            sd.report_full_closure(file)

    methodmap = dict(subdirs=phase4,
                     same_files=phase3, diff_files=phase3, funny_files=phase3,
                     common_dirs = phase2, common_files=phase2, common_funny=phase2,
                     common=phase1, left_only=phase1, right_only=phase1,
                     left_list=phase0, right_list=phase0)

    def __getattr__(self, attr):
        if attr not in self.methodmap:
            raise AttributeError(attr)
        self.methodmap[attr](self)
        return getattr(self, attr)

def cmpfiles(a, b, common, shallow=True):
    """Compare common files in two directories.

    a, b -- directory names
    common -- list of file names found in both directories
    shallow -- if true, do comparison based solely on stat() information

    Returns a tuple of three lists:
      files that compare equal
      files that are different
      filenames that aren't regular files.

    """
    res = ([], [], [])
    for x in common:
        ax = os.path.join(a, x)
        bx = os.path.join(b, x)
        res[_cmp(ax, bx, shallow)].append(x)
    return res


# Compare two files.
# Return:
#       0 for equal
#       1 for different
#       2 for funny cases (can't stat, etc.)
#
def _cmp(a, b, sh, abs=abs, cmp=cmp):
    try:
        return not abs(cmp(a, b, sh))
    except OSError:
        return 2


# Return a copy with items that occur in skip removed.
#
def _filter(flist, skip):
    return list(filterfalse(skip.__contains__, flist))

		
def output(filename):
    f = open(filename+'.txt', 'w')
    f.write ('File: ' + filename + '.xml processed by dirdiff 2.0\n')
    f.write ('by Alina Lapina '+ datetime.datetime.now().isoformat() + '\n')
    return f
    
def dirdiff(dir1, dir2, filename):
    f = output(filename)
    comparison = dircmp(dir1, dir2)
    comparison.report_full_closure(f)

# Demonstration and testing.
#
def interface():
    import sys
    import getopt
    print("Dirdiff started.")
    options, args = getopt.getopt(sys.argv[1:], 'r')
    if len(args) != 3:
        raise getopt.GetoptError('Usage: dirdiff <dir1> <dir2> <report_name>', None)
    #dd = dircmp(args[0], args[1], args[2])
    #if ('-r', '') in options:
    #    dd.report_full_closure()
    #else:
    print("Args is ok: ", args[0], args[1], args[2])
    dirdiff(args[0], args[1], args[2])

if __name__ == '__main__':
    interface()

