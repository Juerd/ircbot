ircbot
======
Dependencies:
python-dateutil

======
Config file ~/.ircbot:

<pre>
[main]
server=$host[:$port]
[password=$password]
channel=$channel
nickname=$nickname
admin=$admin([;$other_admin)*
admin_channels=$channel[;$channel ...]
</pre>

======
For the modules:
<pre>
[google]
api_key=
cx=

[ns]
username=
password=

[tkkrlab]
status_file=
quote_file=
led_url=$message={0}
</pre>
