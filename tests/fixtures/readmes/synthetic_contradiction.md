# Relaybox

Relaybox forwards webhook events to the sinks you configure.

## Usage

Send a build failure to Slack and to email:

```bash
relaybox send --sink slack --sink email --event build.failed
```

The email sink accepts any SMTP server.

## Start it locally

```bash
ssh deploy@192.168.3.116 'relaybox serve --config /Users/mina/relay/config.yml'
```

## Roadmap

- Email sink — planned for 0.4
- Discord sink — not yet implemented
