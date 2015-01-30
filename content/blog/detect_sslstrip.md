Title: Detecting SSLStrip using CSS
Date: 2013-06-27
kind: article
excerpt: |
    Some of the newer CSS selectors can be used for basic detection of
    SSLStrip
status: published
author: Felix Ingram
created_at: 2013-06-19
---
# Detecting SSLStrip using CSS

SSLStrip is a simple proxying tool that will change HTTPS links to vanilla
HTTP. It's one of the reasons why pentest reports will recommend against
promoting a user's session from unencrypted to encrypted channels when they
access a sensitive section of a site. If an attacker is able to position
themselves between the user and the site and alter traffic, then they can
change all of the server's responses to remove any links to HTTPS URLs, before
the session is moved to the secure channel.

The problem is made worse by the user not being able to detect that the
modifications are being performed. If they don't know that the site is supposed
to be running over a secure connection then they won't know to check the links
that they are clicking.

One way to inform the user that something is amiss is to make use of some of
the newer CSS selectors. The following example will be concerned with forms
that get submitted to HTTPS URLs - something that is normally seen on login
pages.

    <form method="POST" action="https://mysite/login.php">
        <label>Username</label><input type="text" name="username" />
        <label>Password</label><input type="password" name="password" />
    </form>

Here we see that the site will submit the form to the URL
'https://mysite/login.php'. If we have a look at the code for SSLStrip
([see here](https://github.com/moxie0/sslstrip/blob/master/sslstrip/ServerConnection.py#L31))
then we see that that regular expression used to find secure links is fairly
basic. Anything starting with "https" and then followed by some valid URL
characters has the "https" replaced with "http"
([as shown here](https://github.com/moxie0/sslstrip/blob/master/sslstrip/ServerConnection.py#L144])).

In our example this will result in our form looking like the following:

    <form method="POST" action="http://mysite/login.php">
        <label>Username</label><input type="text" name="username" />
        <label>Password</label><input type="password" name="password" />
    </form>

And the user being none the wiser.

In order to detect this change with CSS we need to use attribute value
selectors. The following CSS rule:

    form.secure[action^="http://"]:after {
        content: url("/images/nedry.gif");
    }

Will change the following form:

<form class="secure" method="POST" action="https://#">
    <label for="username1">Username</label>
    <input type="text" name="username1" id="username1" /><br/>
    <label for="password1">Password</label>
    <input type="password" name="password1" id="password1" />
</form>

To look like the following:

<form class="secure" method="POST" action="http://#">
    <style type="text/css" scoped>
        form.secure[action^="http://"]:after {
            content: url("/images/nedry.gif");
        }
    </style>
    <label for="username2">Username</label>
    <input type="text" name="username2" id="username2" /><br/>
    <label for="password2">Password</label>
    <input type="password" name="password2" id="password2" /><br/>
</form>

Not the most subtle of indicators, but should get the point across.

The selector `form.secure[action^="http://"]:after` will match all forms that
have the class of 'secure' and who's action begins with "http://". (The `:after`
is used to insert content after the form). Site owners would have to add the
class on all forms that they wanted to be secure and include some appropriate
styling and content to warn users that their traffic is being intercepted.

Obviously, this technique will only work when 'traditional' forms are being
used. When JavaScript is being used for validation or other such trickery, and
the form's action is changed as a result, then this method would not work as
well. Including HTTPS links and overriding submission actions could still be
used to make this technique valid, but that is left as an exercise to the
reader.
