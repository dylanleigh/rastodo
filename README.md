# rastodo
Rastatodo console/Android text based TODO app

http://dylanleigh.net/software/rastodo/

# Overview

Rastodo/Rastatodo is a cross-platform Python script which parses a text file
containing "To Do" items and displays them in the order of urgency and
importance.

# Features

- Single flat text file backend. Easy to edit many items, and you
  can use your own backup/version control/synchronization systems
  to control how you want to manage the file.

- Supports multiple "types" of TODO list items, including
  appointments, "sleeping" items which won't appear until a
  specified time, "wishlist" items without a due date and more.

- Supports ANSI colour output when run from a terminal/console and
  a GUI interface on Android.

- Written in 100% Python, with the same script running both the
  Unix terminal and the Android GUI versions.

# .todo File Format

 You'll need a .todo file (default location is $HOME/.todo);
 the -f option selects a file). Each line of this file should be:

   - blank
   - A comment (line starts with a #; ignored by the program)
   - A category (just a name in square brackets)
   - A todo item (format described later)

Todo item Format
----------------

 <type><[priority]> <[date YYYY-MM-DD]> <description with spaces>\n 

 Some types do not have a priority, some don't have a date, some have
 both or neither.

 Item types are represented by a single char:

```
 t - Todo - No priority, simply has a date by which it must be done.
            Equivalent to the old todo.c usage.

 s - Sleeping - Priority is the number of days proximity before it
                is shown in the output.

 a - Appointment - These are handled the same as sleeping items, but
                   as you can filter on type this lets you easily show
                   only appointments in the output. They also display the
                   Weekday in the todo entry.

 c - Constant - No date, the priority is number of days away this item
                is "due".

 w - Wishlist - No priority, No date. Wishlist items are effectively
                infinity days away but are always shown (unless turned
                off with the exclude types = wishlist option).
```

It is anticipated that more types will be added, in particular I intend to add
recurring (r) and followup (f) items.

Sample .todo file
-----------------

```
c0 always today (this doesn't have a category)
c1 always tomorrow (this doesn't have a category either)

[CS101   ]
t  2008-03-03 week 1 lab report
t  2008-03-10 week 2 cal report

[CS134   ]
c0 see lecturer about something asap
t  2008-03-15 assignment 1

[CS123   ]
a2 2008-03-05 12:30 appointment with lecturer about project
t  2008-03-15 project report 1 due

[new types]
a3 2008-03-04 doctor's  appointment
s0 2008-03-02 do backups (this shows up only on the day)
c2            fix something soon
w             fix something whenever

[birthdays]
a5 2008-02-11 Alice's birthday
a5 2008-01-21 Bob's birthday
```

# Options

Use the -h option to the script for a full list. The list below may be out of date.

You can use a partial long argument as long as it is unique
(e.g. "--app" or even "--ap" instead of "--appointments")

```
  -f FILE, --file=FILE  File to parse (defaults to $HOME/.todo)
  -e, --edit            Invoke your $EDITOR on todo file
  -r, --reverse         Reversed order of sorting
  --mono                Monochrome output
  --sort-cat            Group by category
  --all                 Shows all items, regardless of date and filtering
  -d DAYS, --days=DAYS  Days after which item will not be included
  --only-types=TYPES    Only include these types (string of letters)
  --appointments        Shows appointments only (equivalent to --only-types=a
  --ex-types=EX_TYPES   Exclude these types (string of letters)
  --only-cat=ONLY_CAT   Only include these categories (comma delimited)
  --ex-cat=EX_CAT       Exclude these categories (comma delimited)
  --two-lines           Newline before description (i.e. description is on its own line)
```

# Rastodo on Android

An unattractive but functional Android GUI is included (using list dialogs).
The same script can be used from a terminal and on a droid device - it will use
the GUI if it can import the Android module, otherwise it will use text output.

To run Python scripts on Android you will need Scripting Layer for Android
(SL4A): https://code.google.com/p/android-scripting/

The default todo file location on Android is /sdcard/svncos/dotfiles/todo -
because thats where I keep it (svncos is my Subversion directories). You might
want to modify this or create a shortcut with the -f option to use another
location.

Using the Droid GUI
-------------------

Tap a category to view entries within that category, then back to return to the
list of categories.

Pressing back at the category list will quit the script. Selecting an
individual todo entry also quits the script at this stage, however in future
versions this will open a dialog that lets you edit or delete that entry.

The lists are sorted with highest priority/urgency at the top.

# Notes/Tips/FAQ

- You can use a cronjob with rastodo piped through wc to collect statistics
  about how busy you are. Some RRDtool graphs of my TODO are at
  http://www.dylanleigh.net/stuff/todo/

- If you use Vim to edit your .todo file, in Normal Mode, Ctrl-A and Ctrl-X
  will increase/decrease the number under or to the right of the cursor. This
  makes it easy to change dates for things in Vim.

- I keep my .todo file in Subversion and use that to sync files between my
  assorted computers/phones/tablets; others have successfully used Bittorrent
  Sync, AeroFS, and Owncloud.

- There is no Android widget, and unless widget support is added to SL4A there
  won't be a dedicated one. However, on my phone I have built my own by using a
  script that runs Rastodo whenever I sync the todo file and pipes the output to
  a file. I then use the "Word Widget" (displays a plain text file) to display
  the output file on my home screen.

- The name "Rastodo" is derived from the previous version "Rastatodo" which was
  inspired by the red/yellow/green bands of colour output on earlier versions.
  (This has become less rastafarian as more colours and types were added).

# Authors

Dylan Leigh - http://www.dylanleigh.net

Rastodo is a much-improved Python rewrite of Dylan's "Rastatodo" todo.c which
was itself based on Emil Mikulic's todo.c (http://dmr.ath.cx/code/todo/todo.c).

