# USB → RJ45 male

**What it is:** USB cable ending in an Ethernet **plug** (male), not a jack.

**Studio role:** Plug the stick laptop straight into a **wall jack / switch / isolator** when you do not have a patch lead.

## How to use

1. Plug USB into host; male RJ45 into switch/wall.
2. Confirm link; same SecCheck / lite-pen rules as other NICs.
3. For a **Pi’s female Ethernet port**, use **ATHEN or Lenovo female NIC + patch cable** instead — male-to-male needs a coupler and is awkward.

## Ubuntu Helper notes

- Same stack as other USB NICs: NetworkManager + drivers.
- Identify interface with `ip link` after plug-in.

## Do not

- Force into a Pi Ethernet jack expecting a female receptacle without the right gender.
- Use on foreign office jacks you are not authorized to test.
