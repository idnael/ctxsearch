# -*- coding: utf-8 -*-

import io, urllib, subprocess, os, time, re, sys, psutil

def uniq(values):
    if len(values) == 0:
        raise Exception("zero")
    elif len(values) == 1:
        return values[0]
    else:
        raise Exception("more than one")

def compare_lists(l1, l2):
    if len(l1) != len(l2):
        return False
    s1 = set(l1)
    s2 = set(l2)
    for x in s1:
        if not x in s2:
            return False
    return True

def parse(text, basedirs):
    return LsParser().parse(text, basedirs)

class LsParser:
    def parse(self,text, basedirs):
        lines = text.strip().split("\n")

        files = []
        sucess_basedir = None

        for basedir in basedirs:
            self.basedir = basedir
            #print "testing",basedir
            try:
                test = self._parse_files(lines)
                if test:
                    if files and not compare_lists(test, files):
                        #print "Encontrei possibilidades em duas shells diferentes"
                        return None, []
                    else:
                        sucess_basedir = self.basedir
                        files = test

            except Exception as ex:
                #print "pid",proc.pid, str(ex)
                pass

        return sucess_basedir,files


    # Returns a list of absolute files present in the text.
    # Assumes text is output of ls program, which can be multicolumn.
    # Raise exception if not found or found more than one possible solution
    def _parse_files(self, lines):
        if len(lines) == 1:
            # single line
            line0tabs = uniq(self._detect_grid(lines, 0))
            tabs = None # will not be used

        elif len(lines) == 2:
            # two lines, can have completely independent tab positions
            line0tabs = uniq(self._detect_grid(lines[0:1], 0))
            tabs = uniq(self._detect_grid(lines[1:2], 0))

        else:
            # Three or more lines.
            # The first one can be incomplete
            # Example:
            # the user selected int the output of the ls program
            # but only included the last columns of the first line.
            # xxxxxxxxxxxxxxxxxxxxxxxxxxxx "modlanguage.py  t2.py"
            # "config.py    main.py         modsyntax.py    t_.py"
            # "control.py   modfiles.py     modweb.py       unac.py"
            # "__init__.py  modgrabinfo.py"
            # First detect the tabs ignoring the first line.
            # Then have to find from which tab position (i) the first line have started
            line0result = []
            for test in self._detect_grid(lines[1:], 0):
                for i in range(0, len(test)-1):
                    line0test = [test[j] - test[i] for j in range(i,len(test))]
                    for k in range(0, len(line0test)-1):
                        if not self._test_column(lines[0:1], line0test[k], line0test[k+1]):
                            break
                    else:
                        line0result.append(line0test)
                        tabs = test
            line0tabs = uniq(line0result)

        files = []
        self._collect_files(lines[0:1], line0tabs, files) 
        self._collect_files(lines[1:], tabs, files)
        return files

    TAB_RE = re.compile(" +")
    
    # Given some lines of text, try to detect the tab positions that make the grid.
    # The last line can be incomplete (which means, don't have some of the final columns).
    # The tabs are the initial positions of each column, followed by the end position of the last column.
    # p0 is the initial position.
    # Returns all possible solutions, as a list of lists. If did not find any solution, returns an empty list.
    # Example:
    # "actions.py   keydetector.py  modlanguage.py  t2.py"
    # "config.py    main.py         modsyntax.py    t_.py"
    # "control.py   modfiles.py     modweb.py       unac.py"
    # "__init__.py  modgrabinfo.py"
    #  0            13              29              45
    def _detect_grid(self, lines, p0):
        if p0 >= len(lines[0]):
            return [[p0]] # the end

        result = []
        p = p0
        while p < len(lines[0]):
            match = self.TAB_RE.search(lines[0], p)
            # if didn't find a match, go to the end
            p = match and match.end() or sys.maxint
            if self._test_column(lines, p0,p):
                # try to detect the rest of the grid
                for tabs in self._detect_grid(lines, p):
                    result.append([p0] + tabs)

        return result

    # Tests if all the lines have a valid file between positions p0 and p
    # If one of the lines is shorter than p0, ignore it.
    def _test_column(self, lines, p0, p):
        for line in lines:
            l = len(line)
            if p0 < l:
                if p < l:
                    if line[p-1] != " " or not self._test_cell(line[p0:p]):
                        return False
                else:
                    # to the end
                    if not self._test_cell(line[p0:]):
                        return False
        return True

    # converts a name to a absolute path, relative to basedir
    def absfile(self, name):
        if name.startswith("~/") or name == "~":
            return os.path.expanduser(name)
        else:
            return os.path.join(self.basedir, name)

    # Test if the cell is a valid file
    def _test_cell(self, cell):
        return os.path.exists(self.absfile(cell.strip()))

    # Collect all the files from the given lines, using the given tab positions
    # Append the result to the files list.
    def _collect_files(self, lines, tabs, files):
        for line in lines:
            for c in range(0, len(tabs)-1):
                cell = line[tabs[c] : tabs[c+1]].strip()
                if cell:
                    files.append(self.absfile(cell))
