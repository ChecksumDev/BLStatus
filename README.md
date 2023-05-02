![](https://media.discordapp.net/attachments/1068292632855457882/1068955639650463885/Page_1_35.png?width=150&height=150)

# BeatLeader Status

An application that monitors the status of the BeatLeader servers.

## Quick Start

```bash
docker run -d --name beatleader-status \
              -v /path/to/data:/app/data/ \
              -e TOKEN=YOUR_TOKEN_HERE \
              ghcr.io/checksumdev/blstatus:latest
``` 