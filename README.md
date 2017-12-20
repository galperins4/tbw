# Python True Block Weight

## Installation

```sh
pip install pythark
pip install https://github.com/ArkEcosystem/arky/archive/aip11.zip
git clone https://github.com/galperins4/tbw
```

## Configuration & Usage

After the repository has been cloned you need to open the `config.json` and change it to your liking. Once this has been done execute `python3 tbw.py` to start true block weight script

Important! - pay_addresses and keep keys should match in config.json. DO NOT delete the reserve key as it is required. All other's can be deleted or more added

## To Do

- Add more features to config (e.g., multi-reserve accounts, tx fee handling, black/white list, etc)
- Manual block processing / allocation
- Additional exception handling

## Changelog

### .03
- Modified config file to add minimum payment threshold functionality

### .02
- Modified config file and added multi-address capability for delegate share addresses

### .01
- Initial release

## Security

If you discover a security vulnerability within this package, please open an issue. All security vulnerabilities will be promptly addressed.

## Credits

- [galperins4](https://github.com/galperins4)
- [All Contributors](../../contributors)

## License

[MIT](LICENSE) © [galperins4](https://github.com/galperins4)





