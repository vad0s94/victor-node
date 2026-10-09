# Vendored from aver-ua/esphome-hybrid-inverter-2341

- Source: https://github.com/aver-ua/esphome-hybrid-inverter-2341 (fork of odya/esphome-powmr-hybrid-inverter), Apache-2.0
- Commit: 9c607d6d2f61288da019f046ca12c09b39190b05
- Files:
  - `src/powmr-inverter/helpers/myHelpers.{h,cpp}` -> `helpers/`
  - `src/powmr-inverter/modules/{inverter,inverter-info,pow-hvm6.2m-48v,common-sensors}.yaml` -> `modules/`

## Local changes
Only what ESPHome 2026.9 requires, recorded in `esphome-2026.9.patch`:
- `modules/inverter.yaml`: removed `register_count: 15` from the "Load Percent" sensor
  (option removed from ESPHome; the modbus controller now issues a separate read for 4529+).

Why vendored instead of a remote package: upstream does not build on current ESPHome
(the option above), and C++ helpers cannot come from a remote package anyway.
To update: re-download the files at a newer commit, re-apply the patch, rebuild.
