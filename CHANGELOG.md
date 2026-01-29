# CHANGELOG


## v0.11.0 (2026-01-29)

### Features

- Enable support for snoo sleepytime timeout levels
  ([#46](https://github.com/Lash-L/python-snoo/pull/46),
  [`4c5a919`](https://github.com/Lash-L/python-snoo/commit/4c5a91907f5d4caf75dd4db919e30d86b94352d7))

* Enable support for snoo sleepytime timeout levels with enum provide values

* Update python_snoo/snoo.py

Co-authored-by: Copilot <175728472+Copilot@users.noreply.github.com>

* Update containers.py

remove future annotations

* Fix up linting as suggested

* Fix ordering of imports

As suggested by linter

* Update snoo.py

* Update python_snoo/snoo.py

Co-authored-by: Luke Lashley <conway220@gmail.com>

* Update snoo.py for linter

* trailing comma for linter

* chore: lint

---------

Co-authored-by: Copilot <175728472+Copilot@users.noreply.github.com> Co-authored-by: Luke Lashley
  <conway220@gmail.com>


## v0.10.0 (2025-10-26)

### Features

- Add get_babies function ([#45](https://github.com/Lash-L/python-snoo/pull/45),
  [`f96667f`](https://github.com/Lash-L/python-snoo/commit/f96667f84f65a413a8e66ba7bd1d37cf1ff19f4c))

* Added get_babies function

* Fixed linting


## v0.9.0 (2025-08-18)

### Features

- Expose weaning_baseline enum value ([#44](https://github.com/Lash-L/python-snoo/pull/44),
  [`62608a3`](https://github.com/Lash-L/python-snoo/commit/62608a3f41dd836c8130aa266e19d0a9541af1b8))

WEANING_BASELINE is the same as BASELINE, but without motion.

Co-authored-by: Dave Reisner <dreisner@google.com>


## v0.8.3 (2025-08-15)

### Bug Fixes

- Reauth
  ([`7c1c4eb`](https://github.com/Lash-L/python-snoo/commit/7c1c4eb1e40dac20d273d7c44cbad65fc569e64f))


## v0.8.2 (2025-08-13)

### Bug Fixes

- Create ssl context safely
  ([`ec4542e`](https://github.com/Lash-L/python-snoo/commit/ec4542e314396682588fc2c07bbd47d0542af36b))


## v0.8.1 (2025-08-13)

### Bug Fixes

- Add aiomqtt
  ([`10c0f50`](https://github.com/Lash-L/python-snoo/commit/10c0f5092892c0c9d1c490120102a30afed73211))


## v0.8.0 (2025-08-12)


## v0.7.0 (2025-08-10)

### Features

- Enable fetching activity and logging diapers for babies
  ([`91ba36d`](https://github.com/Lash-L/python-snoo/commit/91ba36d3a56e01cdb56a1ba7b25015d9268b2ef2))

feat: enable fetching activity & logging diapers for babies

- Enable fetching activity & logging diapers for babies
  ([`31b86da`](https://github.com/Lash-L/python-snoo/commit/31b86da748ffeafb1e9ee5d365d5c8ecd8daae8d))


## v0.6.7 (2025-06-30)

### Features

- Convert to MQTT
  ([`35e72a3`](https://github.com/Lash-L/python-snoo/commit/35e72a3feeed865d655855ff81e4263a85d7688f))


## v0.6.6 (2025-05-13)

### Bug Fixes

- Improve reauth
  ([`434a9d4`](https://github.com/Lash-L/python-snoo/commit/434a9d401b36f9d4b288623f0cb879646ae78ee4))


## v0.6.5 (2025-03-27)

### Bug Fixes

- Add missing event
  ([`16ac0bb`](https://github.com/Lash-L/python-snoo/commit/16ac0bb5150ad06594a36957968bac7a6490e2a2))

- Missing config_change event
  ([`4fc36c8`](https://github.com/Lash-L/python-snoo/commit/4fc36c88232ffcf986699691caea1da20f0b304b))


## v0.6.4 (2025-03-20)

### Bug Fixes

- Missing states
  ([`a380c76`](https://github.com/Lash-L/python-snoo/commit/a380c76ee7b839158f67249fe39a2cd0a2bea860))


## v0.6.3 (2025-03-14)

### Bug Fixes

- Catch errors on send command
  ([`73a1d32`](https://github.com/Lash-L/python-snoo/commit/73a1d3289675ad56566b4edf74e2756dd3a88168))


## v0.6.2 (2025-03-14)

### Bug Fixes

- Set base exception type
  ([`139ab40`](https://github.com/Lash-L/python-snoo/commit/139ab401ee0e15dbbfe37455171e19d343a3b6f5))


## v0.6.1 (2025-03-06)

### Bug Fixes

- Default some items for None for non-matching responses
  ([`00b77a8`](https://github.com/Lash-L/python-snoo/commit/00b77a800fbefb72509775423c2349e45e1cfe8d))


## v0.6.0 (2025-02-19)

### Features

- Add foundation for baby stuff
  ([`cc7269e`](https://github.com/Lash-L/python-snoo/commit/cc7269e7d31a0383cfa2daf85789e9d17e6b5fc7))


## v0.5.0 (2025-02-19)

### Features

- Add hold for set_level
  ([`91d1800`](https://github.com/Lash-L/python-snoo/commit/91d180015f76e86bb5c9dd9e61c3babdb202eaf9))


## v0.4.1 (2025-02-03)

### Bug Fixes

- Remove accidental code
  ([`f15bd21`](https://github.com/Lash-L/python-snoo/commit/f15bd215cbd80947c8b3eca8d5573d29cc1d8c0c))


## v0.4.0 (2025-02-03)

### Features

- Save levels and fix bug with white noise
  ([`a828468`](https://github.com/Lash-L/python-snoo/commit/a8284682ee4cfc203b3266b91b12e69d092ff14b))


## v0.3.3 (2025-01-20)

### Bug Fixes

- Add sticky_white_noise state
  ([`a6d3a8a`](https://github.com/Lash-L/python-snoo/commit/a6d3a8a0416c8ae04c1de430ae0a97328890d4a1))


## v0.3.2 (2024-12-30)

### Bug Fixes

- Improve containers
  ([`16e9840`](https://github.com/Lash-L/python-snoo/commit/16e9840c9e2dcbd2359a4c3f9b482f7112ef35da))


## v0.3.1 (2024-12-30)

### Bug Fixes

- Add status_requested
  ([`03b637c`](https://github.com/Lash-L/python-snoo/commit/03b637c465533cd17dfe843c61155a046bc98628))


## v0.3.0 (2024-12-30)

### Features

- Add SnooEvents
  ([`dd17a60`](https://github.com/Lash-L/python-snoo/commit/dd17a6026dac891f6d862cafd4a8f4903a4bc846))


## v0.2.4 (2024-12-29)

### Bug Fixes

- Change to async
  ([`e860bf6`](https://github.com/Lash-L/python-snoo/commit/e860bf61beaad5cc0a162d34c9359e817f1641e1))


## v0.2.3 (2024-12-29)

### Bug Fixes

- Improve disconnect
  ([`b55382c`](https://github.com/Lash-L/python-snoo/commit/b55382ca08b58ab359a92b2431380335974d9be8))


## v0.2.2 (2024-12-29)


## v0.2.1 (2024-12-29)

### Bug Fixes

- Add mashumaro and fix enum again
  ([`8cb044e`](https://github.com/Lash-L/python-snoo/commit/8cb044eb23f1b65a91a862bf65e1c61579c868e0))


## v0.2.0 (2024-12-29)

### Bug Fixes

- Change auth_snoo logic
  ([`ab3ad4f`](https://github.com/Lash-L/python-snoo/commit/ab3ad4f159a1fc80637dc085a156ee2542481c53))

### Features

- Fix strenum for snoo states
  ([`4e45c13`](https://github.com/Lash-L/python-snoo/commit/4e45c137e1bdf83b020293680d5a9bf0c9dc8789))


## v0.1.0 (2024-12-29)

### Features

- Initial commit
  ([`5c426f2`](https://github.com/Lash-L/python-snoo/commit/5c426f2f8b7cc20d705d4e807f284590b7493d49))
