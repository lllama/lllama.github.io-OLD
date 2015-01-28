Title: My Nessus Viewer
Date: 2013-05-17
kind: article
excerpt: I say _my_ Nessus viewer because Nessus parsing scripts are one of the rites of passage for any pentester...
status: published
---
# My Nessus Viewer

I say _my_ Nessus viewer because Nessus parsing scripts are one of the rites
of passage for any pentester.

If you've been using Nessus for long enough then you'll remember the `NBE`
format. `NBE` was a lovely little pipe delimited format that I never had the
misfortune to work with. I started out hating the HTML format and working with
the first version of the XML output. Version one of the XML format was the
worst kind of XML - closer to HTML than something useful. A lot more human
readable than machine readable, and machine readable is what you wanted.

The reason you wanted a machine readable format is because of Nessus's dirty
little secret: it's not for pentesters. The secret begins to reveal itself the
more you actually use Nessus. Pentesters do not need global profiles; we want
per-project profiles. We do not need all our reports stored in one place; we
want them separate and stored along with all of our other output from the test.
And in the vast, vast, majority of cases, we do not want things reported
host by host. Most pentest reports will list the things found and the hosts
that are affected by the thing.

That final point is why you want machine readable formats. And it's also why
all pentesters must, at some point, write a Nessus parsing script. This one is
mine.

It represents my first attempt at GUI programming; it's a little simple but it
does two things: shows your results by issue, rather than by host, and merges
multiple reports into one.

If you have any differences in the output then these will be shown in a "Diffs"
tab. It's an ugly format but gets the job done.

There are also a couple of output formats as well: reStructured Text, CSV and
XML. The XML format is used internally, so is not that useful for others.

Here's what you get when you run it:

![Nothing to see here](/images/nessusviewer_nothing_loaded.PNG "Nothing loaded
yet")

Here's what you get when you load up a Nessus file:

![Metasploitable scan](/images/nessusviewer_Metasploitable_scan.PNG
"Metasploitable has some issues")

If I load up the same scan again and hit the "merge" button the results get
combined:

![Metasploitable scan](/images/nessusviewer_Metasploitable_scan_merged.PNG
"Metasploitable has some issues. Again.")

It is not code that I'm super happy with but I works well enough and others
have found it useful, so check it out [on
Github](http://github.com/nccgroup/lapith).
