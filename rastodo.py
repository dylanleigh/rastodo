#!/usr/bin/python3
#
# rastodo / rastatodo - text based todo list
# Copyright (c) 2004-2016 Dylan Leigh.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# 3. Modified versions must be plainly marked as such, and must not be
#    misrepresented as being the original software.
#
# 4. The names of the authors or copyright holders must not be used to
#    endorse or promote products derived from this software without
#    prior written permission.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE, EVEN IF ADVISED
# OF THE POSSIBILITY OF SUCH DAMAGE.
#
# -----
#

'''
   rastatodo - text based todo list

   http://www.dylanleigh.net/software/rastodo/

 You'll need a .todo file (default location is $HOME/.todo;
 the -f option selects a file). Each line of this file should be:

   - blank
   - A comment (line starts with a #; ignored by the program)
   - A category (just a name in square brackets)
   - A todo item (format described later)

 A sample .todo file is within the cut lines below:

 --8<--

c0 always today (this doesn't have a category)
c1 always tomorrow (this doesn't have a category either)

[CS101   ]
t  2014-06-03 week 1 lab report
t  2014-06-10 week 2 lab report

# This is a comment....

[CS134   ]
c0 see lecturer about something asap
t  2014-06-13 assignment 1 due
t  2014-07-23 assignment 2 due

[CS123   ]
a2 2014-06-05 12:30 appointment with lecturer about project
t  2014-06-15 project report 1 due

[new types]
a3 2014-06-07 doctor's appointment
s0 2014-06-06 do backups (s0 - this appears only on the day)
s1 2014-06-06 backups tomorrow! (this first appears the day before)
c2            fix something soon
w             fix something whenever
r5 2016-02-02 +2m Do something every 2 months apart
r3 2016-02-01 =2m Do something every 2 months on the same day

[birthdays]
a15 2014-06-11 Alice's birthday
a12 2014-06-08 Bob's birthday

 --8<--

 Todo item Format:
 <type><[priority]> <[date YYYY-MM-DD]> <description with spaces>\n 

 Some types do not have a priority, some don't have a date, some have
 both or neither.

 Item types are represented by a single char:

 t - Todo - No priority, simply has a date by which it must be done.
            Equivalent to the old todo.c usage.

 s - Sleeping - Priority is the number of days proximity before it
                is shown in the output. Useful for things you don't need to think
                about until they are nearly due.

 a - Appointment - These are handled the same as sleeping items, but
                   as you can filter on type this lets you easily show
                   only appointments in the output. They also display the
                   Weekday in the todo entry.

 r - Recurring - Priority the same as sleeping items, and has an extra
                 '+nx'/'=nx' entry after the date.
                 The x is d (days), w (weeks), m (months) or y (years)
                 If + the bump will be relative to the current date; if = it will be
                 relative to the old due date.

 c - Constant - No date, the priority is number of days away this item
                is "due".

 w - Wishlist - No priority, No date. Wishlist items are effectively
                infinity days away but are always shown (unless turned
                off with the exclude types = wishlist option).

'''

# FIXME: Recurring should be added to online docs etc!

# Design notes:
#
# Todo items have the following attributes:
# - Type (character or constant)
# - Priority (positive integer, the precise meaning of this field
#             depends on type, for some types it does not appear)
#             For the other types that currently use it, this
#             indicates the number of days away when this should
#             appear on the list.
# - Date. In the .todo file this is in YYYY MM DD format. For
#         some types this does not appear.
# - Description (string)
# - Category (string) (not in item line, derived from category in
#            previous lines)
# - Days away (derived from type, date and/or priority)
#
#
# For each valid type of item, there must be:
#  - an entry in default VALIDTYPES
#  - a regex for the line entry
#  - a section in parseTodoLine for the type
#
# TODO: - Settings via env vars
#       - Use linecache when reading single lines
#       - Handle white backgrounds neatly
#       - Group by category with original file order
#       - Better factoring on filter arguments
#       - Implement p (pending) and f (followup) items
#       - --count or --stats options
#       - Priorities setting colours early?

import os, sys, re, optparse
import datetime

# If import android fails, don't do the other android stuff...
try:
    import android
    droid = android.Android()
except (ImportError):
    droid = None  # test on this later for droid vs terminal

# Default settings and constants - Constants are in UPPERCASE.
TODAY = datetime.date.today()
VALIDTYPES = 'tsacwr'

class FilterSettings(object):
   # TODO: different days/types defaults on droid?
   days_cutoff = 22  # If due later than this, will not be shown
   show_line_nums = False  # FIXME display settings
   only_types = VALIDTYPES
   only_categories = None
   exclude_categories = None  # NB: if both only and ex are specified only use only
filter_settings = FilterSettings()

settings = {}  # FIXME ^^^

# File and display settings - these differ by platform
if droid is None:
   EDITOR = os.getenv('EDITOR', default='vim')
   DEFAULTTODOFILE = "%s/.todo" % os.getenv('HOME') # Default for help
   settings['display'] = {
      'use_colours': True,
      'two_lines': False,
   }
else:  # android:
   EDITOR = ""
   DEFAULTTODOFILE = "/sdcard/dotfiles/.todo"   # TODO make setting
   settings['display'] = {
      'use_colours': False,  # TODO: fix with NON-ansi colours...
      'two_lines': True,
   }
settings['paths'] = {
   'todopath': DEFAULTTODOFILE,
}

# ANSI colours
# these are all with black background (40)
ANSI_COLOURS = {
   'red': "\033[0;31m",       # dull
   'green': "\033[0;32m",     # bright enough
   'yellow': "\033[0;33m",    # more orange than yellow
   'blue': "\033[0;34m",      # dull
   'magenta': "\033[0;35m",   # fairly dull
   'cyan': "\033[0;36m",      # TODO: Would be neat to make use of this...
   'white': "\033[0;37m",     # bright
   'boldred': "\033[0;31;1m",
   'boldmagenta': "\033[0;35;1m",
   'normal': "\033[0m"    # 'return to normal' - XXX must use at end of output!
}


class TodoItem(object):
    # Every todo item has a description and type
    # If cat/days/date are not given, we do not use or display.
    # TODO refactor to calc some on demand based on pri?
    # FIXME pri in init too
    def __init__(self, type, desc, linenum, \
                 category=None, days=None, date=None, wake=None, recur=None):
        self.type = type.lower()  # validation TODO
        self.linenum = int(linenum)
        self.desc = desc
        self.category = category
        self.date = date
        self.wake = int(wake) if wake is not None else None
        self.days = int(days) if days is not None else None
        self.recur = recur

    def daysAway(self):
        # for wishlist items without a date, fudges days = the
        # cutoff so they are filtered and sorted properly.
        if self.days is None:
            return filter_settings.days_cutoff
        else:
            return self.days

    # FIXME: below should be __str__...
    def prettyPrintStr(self, showType=True):
        '''Returns a string representing this todoitem suitable for display to user'''
        # TODO: break long lines for droid?
        preamble = ""  # For colours and status
        if settings['display']['use_colours']:
            if self.days is None:
                preamble = ANSI_COLOURS['blue']
            elif self.days > 4:
                preamble = ANSI_COLOURS['green']
            elif self.days > 0:
                preamble = ANSI_COLOURS['yellow']
            elif self.days == 0:
                preamble = ANSI_COLOURS['boldmagenta']
            else:
                preamble = ANSI_COLOURS['boldred']

        if filter_settings.show_line_nums:  # If set, line numbers should be first
            preamble = "%s%03d " % (preamble, self.linenum)
        if showType:  # show the type of the entry
            preamble = "%s%s " % (preamble, self.type)

        # add date and days to preamble? XXX
        if self.date is None:
            date = '     '
        elif self.type == 'a':   # FIXME refactor to strftime the lot
            date = '%02d-%02d %s:' % (self.date.month, \
                                      self.date.day, self.date.strftime('%a'))
        else:
            date = '%02d-%02d' % (self.date.month, self.date.day)
        if self.days is None:
            days = '    '
        else:
            days = '[%02d]' % self.days

        if settings['display']['two_lines']:  # newline before description
            self.desc = "%s%s" % ('\n', self.desc)
        if self.recur:  # print date of next after desc
            self.desc = "%s [next %s]" % (self.desc, self.recur.isoformat())

        if settings['display']['use_colours']:
            if self.category is None:
                return '%s%s %s %s%s' % \
                       (preamble, days, date, self.desc, ANSI_COLOURS['normal'])
            else:
                return '%s%s %s [%s] %s%s' % (preamble, days, \
                                              date, self.category, self.desc, ANSI_COLOURS['normal'])
        else:
            if self.category is None:
                return '%s%s %s %s' % \
                       (preamble, days, date, self.desc)
            else:
                return '%s%s %s [%s] %s' % (preamble, days, \
                                            date, self.category, self.desc)
                # end prettyPrint

# end TodoItem class

# Regexes for parsing lines
regexT = re.compile(r'[Tt]\s+(\d{4}-\d{2}-\d{2})\s+(.+)')         # Standard "todo" by date
regexS = re.compile(r'[Ss](\d+)\s+(\d{4}-\d{2}-\d{2})\s+(.+)')    # sleeping "todo" by date
regexA = re.compile(r'[Aa](\d+)\s+(\d{4}-\d{2}-\d{2})\s+(.+)')    # appointment
regexC = re.compile(r'[Cc](\d+)\s+(.+)')                          # constant days away
regexW = re.compile(r'[Ww]\s+(.+)')                               # "wishlist" no set date
regexR = re.compile(r'[Rr](\d+)\s+(\d{4}-\d{2}-\d{2})\s+([=+])(\d+)([dwmy])\s+(.+)')  # "Recurring"
# Recurring r 2016-02-20 +12d add 12 days from today
# Recurring r 2016-02-20 =1w 1 week from todo date exactly

# TODO: These are not currently implemented
#regexP = re.compile(r'[Pp]\s+(\d{4}-\d{2}-\d{2})\s+(.+)')         # "Pending"
#regexF = re.compile(r'[Ff]\s+(\d{4}-\d{2}-\d{2})\s+(.+)')         # "Followup"


# Standalone functions
def parseISODate(s):
    '''Given a string in ISO 8602 format (yyyy-mm-dd), returns a
       date object representing the date (see datetime module)
       Throws TypeError or ValueError on bad format'''
    (y, m, d) = s.split('-')
    return datetime.date(int(y), int(m), int(d))


def parseTodoLine(line, num, category=None):
    '''Takes a single line string (and optionally the current
       category); returns a todo item or None if it is invalid.'''
    # Determine type of line
    if line[0] == 't':  # Todo item
        mat = regexT.match(line)
        if mat:
            date = parseISODate(mat.group(1))
            desc = mat.group(2)
            days = (date - TODAY).days
            return TodoItem(
                't',
                desc,
                linenum=num,
                category=category,
                days=days,
                date=date
            )
        else:
            return None

    elif line[0] == 's':  # 'Sleeping' item
        mat = regexS.match(line)
        if mat:
            wake = int(mat.group(1))
            date = parseISODate(mat.group(2))
            desc = mat.group(3)
            days = (date - TODAY).days
            return TodoItem(
                's',
                desc,
                linenum=num,
                category=category,
                days=days,
                date=date,
                wake=wake
            )
        else:
            return None

    elif line[0] == 'a':  # Appointments
        mat = regexA.match(line)
        if mat:
            wake = int(mat.group(1))
            date = parseISODate(mat.group(2))
            desc = mat.group(3)
            days = (date - TODAY).days
            return TodoItem(
                'a',
                desc,
                linenum=num,
                category=category,
                days=days,
                date=date,
                wake=wake
            )
        else:
            return None

    elif line[0] == 'c':  # Constant
        mat = regexC.match(line)
        if mat:
            days = int(mat.group(1))
            desc = mat.group(2)
            return TodoItem(
                'c',
                desc,
                linenum=num,
                category=category,
                days=days,
            )
        else:
            return None

    elif line[0] == 'w':  # Wishlist
        mat = regexW.match(line)
        if mat:
            desc = mat.group(1)
            return TodoItem(
                'w',
                desc,
                linenum=num,
                category=category,
            )
        else:
            return None

    elif line[0] == 'r':  # Recurring item
        mat = regexR.match(line)
        if mat:
            wake = int(mat.group(1))
            date = parseISODate(mat.group(2))
            recurtype = mat.group(3)
            recurlen = int(mat.group(4))
            recurunit = mat.group(5)
            desc = mat.group(6)

            days = (date - TODAY).days

            # Find time of next event
            if recurunit == 'd':
               datedelta = datetime.timedelta(days=recurlen)
            elif recurunit == 'w':
               datedelta = datetime.timedelta(days=recurlen*7)
            # TODO longer times
            #elif recurunit == 'm':
            #   datedelta = datetime.timedelta(months=recurlen)
            #elif recurunit == 'y':
            #   datedelta = datetime.timedelta(months=recurlen*12)
            else:
                return None

            if recurtype == '=':
                nextdate = date + datedelta
            elif recurtype == '+':
                nextdate = TODAY + datedelta
            else:
                return None

            return TodoItem(
                'r',
                desc,
                linenum=num,
                category=category,
                days=days,
                date=date,
                wake=wake,
                recur=nextdate
            )
        else:
            return None

    else:  # no recognized type
        return None


def todoInclude(item):
    '''Returns true if the todo item should be included based on
       the global options. Otherwise returns false.'''
    # FIXME TODO move into class
    # Filter items
    if not cliopts.all:
        if item.wake is not None:
            if item.wake < item.daysAway():
                return False
        if item.daysAway() > filter_settings.days_cutoff:
            return False

        # type of item
        if filter_settings.only_types.find(item.type) == -1:
            return False

        # category
        if filter_settings.only_categories is not None:
            if item.category not in filter_settings.only_categories:
                return False
        else:
            if filter_settings.exclude_categories is not None:
                if item.category in filter_settings.exclude_categories:
                    return False

    # end if not cliopts.all
    return True


def parseTodoFile(file):
    '''Takes a file-like object, returns a list containing
       filtered but unsorted todo objects'''
    ret = []
    category = None
    linecount = 0

    for line in file:
        linecount += 1
        if line == "" or line.isspace() or line[0] == '#':
            continue  # skip blanks and comments

        # handle categories
        if line[0] == '[':
            category = line.lstrip('[').rstrip(']\n')
        else:  # try parsing as a todo line
            todoitem = parseTodoLine(line, linecount+1, category)
            if todoitem:
                if todoInclude(todoitem):
                    ret.append(todoitem)
            else:
                print("Syntax error at line", linecount)

    # end for line in file
    return ret


if __name__ == '__main__':
    # Parse commandline arguments
    optparser = optparse.OptionParser()      # TODO: optparser is deprecated :(

    optparser.add_option('-f', '--file', \
                         help='File to parse (defaults to %s)' % DEFAULTTODOFILE)

    if droid is None:
        optparser.add_option('-e', '--edit', action='store_true', \
                             help='Invoke your EDITOR (%s) on todo file.' % EDITOR)
    else:  # android TODO invoke text intent
        optparser.add_option('-e', '--edit', action='store_true', \
                             help='Invoke a text editor on todo file.')

    optparser.add_option('-r', '--reverse', action='store_true', \
                         help='Reversed order of sorting.')
    optparser.add_option('--mono', action='store_true', \
                         dest='monochrome', help='Monochrome output')
    optparser.add_option('--terminal', action='store_true', \
                         dest='terminal', help='Disable Android GUI (if present)')

    optparser.add_option('--sort-cat', action='store_true', \
                         help='Group by category')
    optparser.add_option('--line-numbers', action='store_true', \
                         help='Show line numbers from todo file in output')    

    optparser.add_option('--all', action='store_true', \
                         help='Shows all items, regardless of date and filtering')
    optparser.add_option('-d', '--days', \
                         help='Days after which item will not be included')

    # Don't use store_const for only-types for if-else later XXX
    optparser.add_option('--only-types', \
                         help='Only include these types (string of letters)')
    optparser.add_option('--appointments', \
                         action='store_const', const='a', dest='only_types', \
                         help='Shows appointments only (equivalent to --only-types=a')
    optparser.add_option('--ex-types', \
                         help='Exclude these types (string of letters)')
    optparser.add_option('--only-cat', \
                         help='Only include these categories (comma delimited)')
    optparser.add_option('--ex-cat', \
                         help='Exclude these categories (comma delimited)')
    optparser.add_option('--two-lines', action='store_true', \
                         help='Newline before description')

    (cliopts, cliargs) = optparser.parse_args()

    # TODO: Break up below into functions!

    # Check term option first
    if cliopts.terminal:
        droid = None

    # Check file argument second
    if cliopts.file:
        settings['paths']['todopath'] = cliopts.file
    todopath = settings['paths']['todopath']
    if not os.access(todopath, os.F_OK):
        sys.exit("%s does not exist; use the -f option to specify a todo file" % todopath)
    if not os.access(todopath, os.R_OK):
        sys.exit("%s is not readable." % todopath)

    # If edit mode, send to defined editor, replacing this process
    if cliopts.edit:
        os.execlp(EDITOR, "editor", todopath)  # replaces this process
    # If bumping, read the whole file up to the given line
    #if cliopts.bump_line:  # TODO not implemented
    #    rewrite_todo_file(todopath, 'bump', cliopts.bump_line)

    # Determine any cutoff dates, categories or types to be
    # excluded beforehand so that we don't include those items when
    # loading from the file. XXX
    if cliopts.days:
        filter_settings.days_cutoff = int(cliopts.days)

    if cliopts.only_cat:
        filter_settings.only_categories = cliopts.only_cat.split(',')
    else:
        if cliopts.ex_cat:
            filter_settings.exclude_categories = cliopts.ex_cat.split(',')

    if cliopts.only_types:
        filter_settings.only_types = cliopts.only_types
    else:
        if cliopts.ex_types:
            for type in cliopts.ex_types:
                filter_settings.only_types = filter_settings.only_types.replace(type, '')
    # end if only types

    filter_settings.show_line_nums = True if cliopts.line_numbers else False

    # Open the file and give it to the parsing function.
    todoFile = open(todopath)
    todoList = parseTodoFile(todoFile)
    todoFile.close()

    # Sort
    if droid is None:
        todoList.sort(key=lambda x: x.daysAway(), \
                      reverse=not cliopts.reverse)
    else:  # android always newest on top
        todoList.sort(key=lambda x: x.daysAway(), reverse=False)
    if cliopts.sort_cat:
        todoList.sort(key=lambda x: x.category)

    # Misc display options
    if cliopts.two_lines:
        settings['display']['two_lines'] = True
    if cliopts.monochrome:
        settings['display']['use_colours'] = False

    # Display items
    if droid is None:
        for item in todoList:
            print(item.prettyPrintStr())
    else:  # droid - display in listview
        categories = list()
        for item in todoList:
            if item.category is None:
                # no duplicates
                if 0 == categories.count("[Uncategorized]"):
                    categories.append("[Uncategorized]")
            else:
                # no duplicates
                if 0 == categories.count(item.category):
                    categories.append(item.category)

        # TODO: Option for [Add Item] ? In each category?
        todoselection = None

        while todoselection == None:
            try:
                droid.dialogCreateAlert('Todo Categories:', '')
                droid.dialogSetItems(categories)
                droid.dialogShow()

                # triggers an exception if back key used
                cat = categories[droid.dialogGetResponse().result['item']]
                if cat == "[Uncategorized]":
                    cat = None

            except:
                sys.exit()  # back pressed in cat menu

            try:
                items = []
                for item in todoList:
                    if item.category == cat:
                        items.append(item.prettyPrintStr())

                droid.dialogCreateAlert('Todo List:', cat)
                droid.dialogSetItems(items)
                droid.dialogShow()

                # triggers an exception if back key used
                todoselection = droid.dialogGetResponse().result['item']
            except:
                pass  # do nothing; goes back to cat menu

                # end while for displaying listview
                # action on selected todo item
                # XXX: menu with options, date/time picker etc?
                # TODO: newline = droid.dialogGetInput('Edit Entry',  oldline, oldline).result


                # end else for droid displayitems

# end if main
