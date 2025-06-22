## /etc/hosts provider for octoDNS

An [octoDNS](https://github.com/octodns/octodns/) provider that creates a "best effort" static/emergency content that can be used in /etc/hosts to resolve things. A, AAAA records are supported and ALIAS and CNAME records will be included when they can be mapped within the zone.

### Installation

#### Command line

```
pip install octodns-etchosts
```

#### requirements.txt/setup.py

Pinning specific versions or SHAs is recommended to avoid unplanned upgrades.

##### Versions

```
# Start with the latest versions and don't just copy what's here
octodns==0.9.14
octodns-etchosts==0.0.1
```

##### SHAs

```
# Start with the latest/specific versions and don't just copy what's here
-e git+https://git@github.com/octodns/octodns.git@9da19749e28f68407a1c246dfdf65663cdc1c422#egg=octodns
-e git+https://git@github.com/octodns/octodns-etchosts.git@ec9661f8b335241ae4746eea467a8509205e6a30#egg=octodns_etchosts
```

### Configuration

```yaml
providers:
  etchosts:
    class: octodns_etchosts.EtcHostsProvider
    # The output directory for the hosts file <zone>.hosts
    directory: ./hosts
    # Remove trailing dots of zone names (e.g. example.com. => example.com) (optional)
    # Avoids problems with certain DNS providers, as the host file format requires an alphanumeric character to be the final character in a hostname.
    # Default: True
    #remove_trailing_dots: True
```

### Support Information

#### Records

EtcHostsProvider supports A and AAAA, and has partial support for tracing ALIAS and CNAME records when they can be resolved within the zone.

#### Dynamic

EtcHostsProvider does not support dynamic records.

### Development

See the [/script/](/script/) directory for some tools to help with the development process. They generally follow the [Script to rule them all](https://github.com/github/scripts-to-rule-them-all) pattern. Most useful is `./script/bootstrap` which will create a venv and install both the runtime and development related requirements. It will also hook up a pre-commit hook that covers most of what's run by CI.
