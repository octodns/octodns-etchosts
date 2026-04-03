## 1.1.0 - 2026-04-03

Minor:
* Omit trailing . from entries to match the requirement that names end in an alphanumeric character, per the manpage/spec. Previous behavior of trailing dots is available with remove_trailing_dots=False - [#43](https://github.com/octodns/octodns-etchosts/pull/43)

Patch:
* Use new [changelet](https://github.com/octodns/changelet) tooling - [#42](https://github.com/octodns/octodns-etchosts/pull/42)

## v1.0.0 - 2025-05-04 - Long overdue 1.0

* Address pending octoDNS 2.x deprecations, require minimum of 1.5.x

## v0.0.2 - 2022-09-03 - More detail, across the zones

* Support tracking records across other zones in the same run
* Include more information about why things matched in the case of
  wildcards/cnames etc.

## v0.0.1 - 2022-01-09 - Moving

#### Nothworthy Changes

* Initial extraction of EtcHostsProvider from octoDNS core

#### Stuff

Nothing
