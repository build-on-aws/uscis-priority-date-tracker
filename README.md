# USCIS Priority Date Tracker

This project contains the sample code for a small utility to pull and store the priority dates from the monthly USCIS Visa Bulletins. It is based on series of articles on [Community.aws](https://community.aws).

Articles:

1. [Using Amazon Q to build a tracker for my Green Card priority date](https://community.aws/content/2hsUp8ZV7UoQpVCApnaTOBljCai)

## Running it locally

To run the project locally, you will need:

1. Git installed
2. Python 3.11
3. Pip

After cloning the repo, you can run the app with the following:

```bash
cd src

python3 -m venv package
source package/bin/activate

pip3 install -r requirements.txt

python3 local_test.py
```

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the LICENSE file.
