---
title: Scanning multiple VLANs from VMware
kind: article
status: draft
---
# All your scans are belong to us

Scanning different VLANs is a pain. The major pain points are the pentester's
two friends: time and cables. All scans will take a certain amount of time, and
can only be done if the cables are in the right ports.

The only way to speed up scanning multiple VLANs is with more cables (or
scanning while travelling near the speed of light). The 'more cables' option
usually takes the form of adding more NICs to your lappy. You can then plug in
as many VLANs as you have ports, and kick off all the scans at once. Some my
argue that you're bridging the networks but (as I test from a laptop, not
a router) I don't see any real issues with this. I've looked at getting a PCI
Express dual-port NIC to try this with but having multiple cables sprouting
from a laptop seemed a little ungainly. I've seen others plug four USB NICs
into a hub, but this too seemed a little messy. So I bought a switch.

[This switch][1] to be exact. It was ~£40 delivered and supports all of
the switchy things that you'd expect. In particular it can be trunked to
another switch, and that's what we'll make use of here. To make things extra
tricky, we'll do our scans from a Backtrack VM, hosted under Windows.

The first thing to do is to configure the switch. These switches have a simple
web interface which is crying out for a bit of scripting but we'll use it as
intended for the moment.

First browse to the VLAN tab. Trunking is then configured as per [these][2] 
instructions.

![Configure trunking](/images/nessusviewer_Metasploitable_scan_merged.PNG
"Configuring trunking")

Next we set up the 
